from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.core.database import get_engine
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.repositories import usuarios_repo
from app.schemas.contracts import (
    RoleEnum,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate):
    senha_hash = hash_password(payload.password)
    try:
        with get_engine().begin() as conn:
            user = usuarios_repo.criar_usuario(
                conn,
                username=payload.username,
                email=payload.email,
                senha_hash=senha_hash,
                role=RoleEnum.USER.value,
            )
            return UserOut(**user)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário cadastrado com este e-mail ou username.",
        )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin):
    with get_engine().connect() as conn:
        user = usuarios_repo.buscar_usuario_por_email(conn, email=payload.email)

    if not user or not verify_password(payload.password, user["senha_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_out = UserOut(
        id_usuario=user["id_usuario"],
        username=user["username"],
        email=user["email"],
        role=RoleEnum(user["role"]),
        data_cadastro=user["data_cadastro"],
    )
    token = create_access_token(
        {
            "id_usuario": user["id_usuario"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
        }
    )
    return TokenResponse(access_token=token, user=user_out)


@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user)):
    with get_engine().connect() as conn:
        user = usuarios_repo.buscar_usuario_por_id(conn, current_user["id_usuario"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )
    return UserOut(**user)