# CraftAI - Auth Only

Este projeto foi reduzido para manter apenas o necessário para:
- cadastro de usuário
- login de usuário
- autenticação com token JWT

## Backend
Rotas disponíveis:
- `POST /api/auth/register`
- `POST /api/auth/login`

## Frontend
Telas disponíveis:
- `/login`
- `/register`

## Como rodar
### Docker
```bash
docker compose up --build
```

### URLs
- Frontend: `http://localhost:3001`
- Backend: `http://localhost:8000`
