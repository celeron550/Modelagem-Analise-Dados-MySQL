import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "root_secret_change_me")
    DB_ANALISE_NAME: str = os.getenv("DB_ANALISE_NAME", "db_analise_musica")
    DB_APP_NAME: str = os.getenv("DB_APP_NAME", "db_app_musica")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "troque_esta_chave_secreta_em_producao_256bits")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
