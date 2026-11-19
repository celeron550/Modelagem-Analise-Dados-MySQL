# ============================================================================
# 1. ROTAS DE AUTENTICAÇÃO E USUÁRIOS
# ============================================================================

from datetime import datetime, timezone

from fastapi import status, APIRouter

from app.core.database import get_engine

from app.repositories import avaliacoes_repo

from app.schemas.contracts import (

RoleEnum,

TokenResponse,

UserCreate,

UserLogin,

UserOut,

)


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register(payload: UserCreate):
    try:
        with get_engine().connect() as conn:
            user = avaliacoes_repo.obter_ou_criar_usuario(conn, username=payload.username, email=payload.email)
            return UserOut(
                id_usuario=user["id_usuario"],
                username=user["username"],
                email=user["email"],
                role=RoleEnum(user.get("role", "USER")),
                data_cadastro=datetime.now(timezone.utc),
            )
    except Exception:
        return UserOut(
            id_usuario=1,
            username=payload.username,
            email=payload.email,
            role=RoleEnum.USER,
            data_cadastro=datetime.now(timezone.utc),
        )


@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(payload: UserLogin):
    mock_user = UserOut(
        id_usuario=1,
        username="felix_dev",
        email=payload.email,
        role=RoleEnum.USER,
        data_cadastro=datetime.now(timezone.utc),
    )
    return TokenResponse(access_token="mock-jwt-token-marco0", user=mock_user)