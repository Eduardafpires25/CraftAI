import enum


class UserRole(str, enum.Enum):
    CLIENT = "client"
    SELLER = "seller"
    ADMIN = "admin"


class OrderStatus(str, enum.Enum):
    DRAFT = "draft"                  # cliente ainda iterando, nao enviado
    IN_ANALYSIS = "in_analysis"      # enviado ao vendedor
    APPROVED = "approved"            # aprovado pelo vendedor
    PAID = "paid"                    # cliente pagou (no carrinho e checkout)
    IN_PRODUCTION = "in_production"  # em producao
    SENT = "sent"                    # enviado pelo vendedor
    DELIVERED = "delivered"          # confirmado recebimento pelo cliente
    COMPLETED = "completed"          # finalizado
    CANCELLED = "cancelled"          # cancelado


class IterationStatus(str, enum.Enum):
    PENDING = "pending"        # aguardando geracao da imagem
    GENERATING = "generating"  # IA processando
    READY = "ready"            # imagem gerada
    FAILED = "failed"          # falha na geracao
    APPROVED = "approved"      # iteracao escolhida pelo cliente


class SellerCategory(str, enum.Enum):
    """Segmento principal da loja. Define o foco do vendedor."""
    MUG = "mug"                # canecas
    SHIRT = "shirt"            # camisetas
    POSTER = "poster"          # posters / quadros
    STICKER = "sticker"        # adesivos
    KEYCHAIN = "keychain"      # chaveiros
    TOTE_BAG = "tote_bag"      # ecobags
    CERAMIC = "ceramic"        # ceramica em geral
    WOODWORK = "woodwork"      # madeira / marcenaria
    JEWELRY = "jewelry"        # bijuterias / joias
    OTHER = "other"            # outros / multi-categoria
