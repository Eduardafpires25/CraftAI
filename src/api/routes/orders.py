from __future__ import annotations

import io
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models.user import User
from src.database.models.order import Order
from src.database.models.project_iteration import ProjectIteration
from src.database.models.enums import IterationStatus, OrderStatus, UserRole
from src.api.dependencies.auth import get_current_active_user, require_seller_email_verified
from src.api.repositories.auth_repository import UserRepository
from src.api.repositories.order_repository import IterationRepository, OrderRepository
from src.api.models.order import (
    CancelRequest,
    IterationCreateRequest,
    IterationResponse,
    MessageResponse,
    OrderCreateRequest,
    OrderListItem,
    OrderListResponse,
    OrderResponse,
    OrderUpdateRequest,
    SellerDecisionRequest,
    StatusUpdateRequest,
)
from src.api.ai import ai_client, AIError
from src.storage import image_service
from config.logger import logger
from config.settings import settings

router = APIRouter(prefix="/orders", tags=["orders"])


# =============================================================================
# Helpers
# =============================================================================

def _url(key: Optional[str]) -> Optional[str]:
    return image_service.get_url(key) if key else None


def _iter_to_response(it: ProjectIteration) -> IterationResponse:
    return IterationResponse(
        id=it.id,
        order_id=it.order_id,
        version=it.version,
        description=it.description,
        prompt=it.prompt,
        image_key=it.image_key,
        image_url=_url(it.image_key),
        ai_model=it.ai_model,
        status=it.status,
        error_message=it.error_message,
        created_at=it.created_at,
        updated_at=it.updated_at,
    )


def _order_to_response(order: Order) -> OrderResponse:
    iterations = list(order.iterations) if order.iterations is not None else []
    iterations_sorted = sorted(iterations, key=lambda i: i.version)
    approved = order.approved_iteration

    return OrderResponse(
        id=order.id,
        title=order.title,
        description=order.description,
        product_type=order.product_type,
        product_options=order.product_options or {},
        quantity=order.quantity,
        estimated_price=order.estimated_price,
        status=order.status,
        client_id=order.client_id,
        seller_id=order.seller_id,
        approved_iteration_id=order.approved_iteration_id,
        submitted_at=order.submitted_at,
        approved_at=order.approved_at,
        completed_at=order.completed_at,
        shipping_address=order.shipping_address,
        shipping_number=order.shipping_number,
        shipping_complement=order.shipping_complement,
        shipping_city=order.shipping_city,
        shipping_state=order.shipping_state,
        shipping_zip_code=order.shipping_zip_code,
        shipping_phone=order.shipping_phone,
        image_url=order.image_url,
        created_at=order.created_at,
        updated_at=order.updated_at,
        iterations=[_iter_to_response(i) for i in iterations_sorted],
        approved_iteration=_iter_to_response(approved) if approved else None,
    )


def _order_to_list_item(order: Order) -> OrderListItem:
    cover = None
    if order.approved_iteration and order.approved_iteration.image_key:
        cover = _url(order.approved_iteration.image_key)
    return OrderListItem(
        id=order.id,
        title=order.title,
        product_type=order.product_type,
        quantity=order.quantity,
        status=order.status,
        seller_id=order.seller_id,
        client_id=order.client_id,
        cover_url=cover,
        submitted_at=order.submitted_at,
        created_at=order.created_at,
    )


def _get_order_for_user(
    db: Session,
    order_id: uuid.UUID,
    user: User,
) -> Order:
    """Busca pedido se o usuario for o cliente, o seller atribuido ou admin."""
    repo = OrderRepository(db)
    order = repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado.")

    if user.role == UserRole.ADMIN:
        return order
    if order.client_id == user.id:
        return order
    if order.seller_id == user.id:
        return order

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao tem acesso a este pedido.")


def _ensure_status(order: Order, allowed: List[OrderStatus]):
    if order.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operacao nao permitida no status atual ({order.status.value}).",
        )


# =============================================================================
# Cliente: criar e gerenciar pedidos (DRAFT)
# =============================================================================

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    body: OrderCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cliente cria um novo pedido em DRAFT, vinculado a um seller.
    O pedido inicia sem iteracoes; o cliente deve criar iteracoes em seguida.
    """
    user_repo = UserRepository(db)
    seller_user = user_repo.get_by_id(body.seller_id)
    if not seller_user or seller_user.role != UserRole.SELLER:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller nao encontrado.",
        )
    if not seller_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seller inativo.",
        )

    order_repo = OrderRepository(db)
    order = order_repo.create(
        client_id=current_user.id,
        seller_id=body.seller_id,
        title=body.title,
        description=body.description,
        product_type=body.product_type,
        product_options=body.product_options,
        quantity=body.quantity,
    )
    # Registra criacao na auditoria
    order_repo.change_status(order, OrderStatus.DRAFT, changed_by_id=current_user.id, note="Pedido criado")
    logger.info("Pedido criado: %s (cliente=%s, seller=%s)", order.id, current_user.email, seller_user.email)

    order = order_repo.get_by_id(order.id)
    return _order_to_response(order)


@router.get("/me", response_model=OrderListResponse)
def list_my_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Lista pedidos do cliente logado."""
    repo = OrderRepository(db)
    orders = repo.list_for_client(current_user.id, status=status_filter, skip=skip, limit=limit)
    total = repo.count_for_client(current_user.id, status=status_filter)
    return OrderListResponse(
        items=[_order_to_list_item(o) for o in orders],
        total=total, skip=skip, limit=limit,
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Detalhes de um pedido. Acessivel por client, seller atribuido ou admin."""
    order = _get_order_for_user(db, order_id, current_user)
    return _order_to_response(order)


@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: uuid.UUID,
    body: OrderUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cliente edita pedido (apenas em DRAFT)."""
    order = _get_order_for_user(db, order_id, current_user)
    if order.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o cliente pode editar.")
    _ensure_status(order, [OrderStatus.DRAFT])

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nada para atualizar.")

    repo = OrderRepository(db)
    order = repo.update(order, **update_data)
    return _order_to_response(repo.get_by_id(order.id))


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: uuid.UUID,
    body: CancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cliente cancela pedido.
    Permitido em DRAFT ou IN_ANALYSIS.
    """
    order = _get_order_for_user(db, order_id, current_user)
    if order.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o cliente pode cancelar.")
    _ensure_status(order, [OrderStatus.DRAFT, OrderStatus.IN_ANALYSIS])

    repo = OrderRepository(db)
    order = repo.change_status(order, OrderStatus.CANCELLED, changed_by_id=current_user.id, note=body.note)
    return _order_to_response(repo.get_by_id(order.id))


# =============================================================================
# Cliente: iteracoes com IA
# =============================================================================

@router.get("/{order_id}/iterations", response_model=List[IterationResponse])
def list_iterations(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Lista iteracoes de um pedido. Acessivel por client/seller envolvidos."""
    order = _get_order_for_user(db, order_id, current_user)
    iter_repo = IterationRepository(db)
    iterations = iter_repo.list_by_order(order.id)
    return [_iter_to_response(i) for i in iterations]


@router.post(
    "/{order_id}/iterations",
    response_model=IterationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_iteration(
    order_id: uuid.UUID,
    body: IterationCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cliente cria nova iteracao com descricao customizada.
    A IA gera uma imagem (placeholder verde por enquanto) e salva no storage.
    Permitido apenas em DRAFT.
    """
    from src.api.services.iteration_service import iteration_service

    limit_data = iteration_service.get_iterations_limit(db, str(current_user.id))

    if limit_data["enabled"] and limit_data["remaining"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Limite diário de iterações atingido ({limit_data['daily_limit']} por dia). Tente novamente amanhã."
        )

    order = _get_order_for_user(db, order_id, current_user)
    if order.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o cliente pode iterar.")
    _ensure_status(order, [OrderStatus.DRAFT])

    iter_repo = IterationRepository(db)

    # Cria iteracao em estado GENERATING
    iteration = iter_repo.create(
        order_id=order.id,
        description=body.description,
        status=IterationStatus.GENERATING,
    )

    # Construir prompt padrão para geração de imagem lendo do arquivo .md
    import os
    
    prompt_template_path = os.path.join(os.path.dirname(__file__), "..", "ai", "prompts", "image_generation.md")
    
    try:
        with open(prompt_template_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # Fallback se o arquivo não existir
        prompt_template = "Gere uma imagem do produto específico solicitado. Nome do produto: {product_name}. Tipo de produto: {product_type}. {product_options}Descrição do usuário para refinamento: {user_description}."
    
    # Preparar parâmetros
    params_info = ""
    if order.product_options:
        params = "\n".join([f"  - **{key}:** {value}" for key, value in order.product_options.items()])
        if params:
            params_info = f"- **Parâmetros do produto:**\n{params}\n"
    
    # Substituir variáveis no template
    full_prompt = prompt_template.format(
        product_name=order.title,
        product_type=order.product_type or "personalizado",
        product_options=params_info,
        user_description=body.description,
    )

    # Gera imagem (placeholder verde quando AI_PLACEHOLDER_MODE=true)
    try:
        result = ai_client.generate_iteration_image(
            description=full_prompt,
            product_type=order.product_type,
        )
    except AIError as e:
        iter_repo.update(
            iteration,
            status=IterationStatus.FAILED,
            error_message=str(e)[:500],
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        iter_repo.update(
            iteration,
            status=IterationStatus.FAILED,
            error_message=str(e)[:500],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro inesperado na geracao de imagem.",
        )

    # Salva imagem no storage
    try:
        stored = image_service.upload_ai_generated(
            owner_id=str(current_user.id),
            file=io.BytesIO(result.image_bytes),
            filename=f"iter-{iteration.version}.png",
            content_type=result.content_type,
        )
    except Exception as e:
        iter_repo.update(
            iteration,
            status=IterationStatus.FAILED,
            error_message=f"Falha ao salvar imagem: {e}"[:500],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao salvar imagem gerada.",
        )

    iter_repo.update(
        iteration,
        prompt=result.prompt,
        ai_model=result.model,
        image_key=stored.key,
        status=IterationStatus.READY,
        error_message=None,
    )

    iteration = iter_repo.get_by_id(iteration.id)
    logger.info(
        "Iteracao criada: order=%s version=%d model=%s",
        order.id, iteration.version, result.model,
    )
    return _iter_to_response(iteration)


@router.get("/{order_id}/iterations/{iteration_id}", response_model=IterationResponse)
def get_iteration(
    order_id: uuid.UUID,
    iteration_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Detalhe de uma iteracao."""
    order = _get_order_for_user(db, order_id, current_user)
    iter_repo = IterationRepository(db)
    iteration = iter_repo.get_by_id(iteration_id)
    if not iteration or iteration.order_id != order.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Iteracao nao encontrada.")
    return _iter_to_response(iteration)


@router.post("/{order_id}/approve-iteration/{iteration_id}", response_model=OrderResponse)
def approve_iteration(
    order_id: uuid.UUID,
    iteration_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cliente seleciona uma iteracao como aprovada (escolha final).
    Pode ser trocada enquanto o pedido estiver em DRAFT.
    """
    order = _get_order_for_user(db, order_id, current_user)
    if order.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o cliente pode aprovar.")
    _ensure_status(order, [OrderStatus.DRAFT])

    iter_repo = IterationRepository(db)
    iteration = iter_repo.get_by_id(iteration_id)
    if not iteration or iteration.order_id != order.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Iteracao nao encontrada.")
    if iteration.status not in (IterationStatus.READY, IterationStatus.APPROVED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Iteracao nao esta pronta (status={iteration.status.value}).",
        )

    iter_repo.mark_approved_unique(iteration)

    order_repo = OrderRepository(db)
    order = order_repo.update(order, approved_iteration_id=iteration.id)
    logger.info("Iteracao aprovada: order=%s iteration=%s v%d", order.id, iteration.id, iteration.version)
    return _order_to_response(order_repo.get_by_id(order.id))


@router.post("/{order_id}/submit", response_model=OrderResponse)
def submit_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cliente envia o pedido (com iteracao aprovada) ao seller para analise.
    DRAFT -> IN_ANALYSIS.
    """
    order = _get_order_for_user(db, order_id, current_user)
    if order.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o cliente pode submeter.")
    _ensure_status(order, [OrderStatus.DRAFT])

    if not order.approved_iteration_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aprovacao de uma iteracao e obrigatoria antes de submeter.",
        )

    repo = OrderRepository(db)
    order = repo.change_status(
        order, OrderStatus.IN_ANALYSIS,
        changed_by_id=current_user.id, note="Cliente submeteu para analise do seller",
    )
    logger.info("Pedido submetido: %s", order.id)
    return _order_to_response(repo.get_by_id(order.id))


# =============================================================================
# Seller: aceitar/rejeitar e atualizar status
# =============================================================================

seller_router = APIRouter(prefix="/sellers/me/orders", tags=["sellers-me-orders"])


@seller_router.get("/", response_model=OrderListResponse)
def list_seller_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """Lista pedidos endereçados ao seller logado."""
    repo = OrderRepository(db)
    orders = repo.list_for_seller(current_user.id, status=status_filter, skip=skip, limit=limit)
    total = repo.count_for_seller(current_user.id, status=status_filter)
    return OrderListResponse(
        items=[_order_to_list_item(o) for o in orders],
        total=total, skip=skip, limit=limit,
    )


@router.post("/{order_id}/seller-decision", response_model=OrderResponse)
def seller_decision(
    order_id: uuid.UUID,
    body: SellerDecisionRequest,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """
    Seller aceita (-> APPROVED) ou rejeita (-> CANCELLED) o pedido em IN_ANALYSIS.
    """
    repo = OrderRepository(db)
    order = repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado.")
    if order.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao e o seller deste pedido.")
    _ensure_status(order, [OrderStatus.IN_ANALYSIS])

    if body.estimated_price is not None:
        repo.update(order, estimated_price=body.estimated_price)

    new_status = OrderStatus.APPROVED if body.accept else OrderStatus.CANCELLED
    note = body.note or ("Aceito pelo seller" if body.accept else "Rejeitado pelo seller")
    order = repo.change_status(order, new_status, changed_by_id=current_user.id, note=note)
    logger.info("Decisao do seller: %s -> %s", order.id, new_status.value)
    return _order_to_response(repo.get_by_id(order.id))


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: uuid.UUID,
    body: StatusUpdateRequest,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """
    Seller atualiza o status do pedido seguindo as transicoes permitidas:
      APPROVED -> PAID
      PAID -> IN_PRODUCTION
      IN_PRODUCTION -> SENT
      APPROVED|PAID|IN_PRODUCTION|SENT -> CANCELLED
    """
    repo = OrderRepository(db)
    order = repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado.")
    if order.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao e o seller deste pedido.")

    allowed_transitions = {
        OrderStatus.APPROVED: {OrderStatus.PAID, OrderStatus.CANCELLED},
        OrderStatus.PAID: {OrderStatus.IN_PRODUCTION, OrderStatus.CANCELLED},
        OrderStatus.IN_PRODUCTION: {OrderStatus.SENT, OrderStatus.CANCELLED},
        OrderStatus.SENT: {OrderStatus.CANCELLED},
    }
    valid_next = allowed_transitions.get(order.status, set())
    if body.status not in valid_next:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transicao invalida: {order.status.value} -> {body.status.value}.",
        )

    order = repo.change_status(order, body.status, changed_by_id=current_user.id, note=body.note)
    return _order_to_response(repo.get_by_id(order.id))


@router.patch("/{order_id}/confirm-delivery", response_model=OrderResponse)
def confirm_delivery(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cliente confirma o recebimento do pedido.
    SENT -> DELIVERED.
    """
    repo = OrderRepository(db)
    order = repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado.")
    if order.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o cliente pode confirmar o recebimento.")
    
    if order.status != OrderStatus.SENT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pedido deve estar em status ENVIADO para confirmar recebimento. Status atual: {order.status.value}.",
        )
    
    order = repo.change_status(order, OrderStatus.DELIVERED, changed_by_id=current_user.id, note="Recebimento confirmado pelo cliente")
    return _order_to_response(repo.get_by_id(order.id))


@router.patch("/{order_id}/complete", response_model=OrderResponse)
def complete_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cliente marca o pedido como concluído após confirmar o recebimento.
    DELIVERED -> COMPLETED.
    """
    repo = OrderRepository(db)
    order = repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado.")
    if order.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o cliente pode marcar o pedido como concluído.")
    
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pedido deve estar em status ENTREGUE para marcar como concluído. Status atual: {order.status.value}.",
        )
    
    order = repo.change_status(order, OrderStatus.COMPLETED, changed_by_id=current_user.id, note="Pedido concluído pelo cliente")
    return _order_to_response(repo.get_by_id(order.id))
