import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "troque_esta_chave_secreta_em_producao_256bits")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

bearer_scheme = HTTPBearer(auto_error=False)

def hash_password(plain_pass : str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_pass.encode("utf-8"),salt)
    return hashed.decode("utf-8")

def verify_password(plain_pass: str, hashed_pass: str) -> bool:
    try:
        return bcrypt.checkpw(plain_pass.encode("utf-8"),
                              hashed_pass.encode("utf-8"))
    except ValueError:
        return False

def create_access_token(user_data : dict) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_data["id_usuario"]),
        "username": user_data["username"],
        "email": user_data["email"],
        "role": user_data["role"],
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_current_user(credentials : HTTPAuthorizationCredentials | None = Depends(bearer_scheme), ) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso ausente ou inválido.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
        return {
            "id_usuario": user_id,
            "username": payload["username"],
            "email": payload["email"],
            "role": payload["role"],
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_admin(current_user : dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acesso restrito apenas a administradores.",
                    headers={"WWW-Authenticate": "Bearer"},
                )