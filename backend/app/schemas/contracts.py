from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# 1. CONTRATOS DE AUTENTICAÇÃO E AUTORIZAÇÃO (Trilha Dev 2)
# ============================================================================

class RoleEnum(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["felix_dev"])
    email: EmailStr = Field(..., examples=["felix@ufrn.br"])
    password: str = Field(..., min_length=6, max_length=72, examples=["SenhaForte123"])


class UserLogin(BaseModel):
    email: EmailStr = Field(..., examples=["felix@ufrn.br"])
    password: str = Field(..., examples=["SenhaForte123"])


class UserOut(BaseModel):
    id_usuario: int
    username: str
    email: EmailStr
    role: RoleEnum
    data_cadastro: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ============================================================================
# 2. CONTRATOS DO CATÁLOGO MUSICAL (Trilha Dev 3)
# ============================================================================

class MusicaOut(BaseModel):
    id_musica: int
    titulo: str
    artista: str
    album: str
    popularity: Optional[int] = None
    danceability: Optional[float] = None
    energy: Optional[float] = None
    tempo: Optional[float] = None


class MusicaDetalheOut(MusicaOut):
    total_reviews: int = 0
    nota_comunidade: Optional[float] = None


# ============================================================================
# 3. CONTRATOS DE AVALIAÇÕES — CRUD (Trilha Dev 3)
# ============================================================================

class AvaliacaoCreate(BaseModel):
    id_musica: int = Field(..., gt=0, examples=[1])
    nota: float = Field(..., ge=0.0, le=10.0, examples=[9.5])
    comentario: Optional[str] = Field(default=None, max_length=1000, examples=["Clássico absoluto!"])


class AvaliacaoUpdate(BaseModel):
    nota: Optional[float] = Field(default=None, ge=0.0, le=10.0, examples=[8.5])
    comentario: Optional[str] = Field(default=None, max_length=1000, examples=["Revisando minha nota."])


class AvaliacaoOut(BaseModel):
    id_avaliacao: int
    id_usuario: int
    username: str
    id_musica: int
    nota: float
    comentario: Optional[str] = None
    data_avaliacao: datetime


# ============================================================================
# 4. CONTRATOS DE ANALYTICS & RANKINGS (Trilha Dev 3 & Dev 4)
# ============================================================================

class RankingComunidadeOut(BaseModel):
    id_musica: int
    artista: str
    faixa: str
    total_avaliacoes: int
    nota_media: float
    maior_nota: float
    menor_nota: float


class CorrelacaoAudioOut(BaseModel):
    musica: str
    artista: str
    danceability: float
    energy: float
    popularity: int


class RankingArtistaOut(BaseModel):
    artista: str
    total_faixas: int
    popularidade_media: float


class RitmoAlbumOut(BaseModel):
    artista: str
    album: str
    qtd_musicas: int
    bpm_medio: float
    bpm_minimo: float
    bpm_maximo: float


class KpiCatalogoOut(BaseModel):
    total_musicas: int
    popularidade_media: float
    popularidade_maxima: int
    popularidade_minima: int
    dancabilidade_media: float
    energia_media: float


class MusicaCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=255, examples=["In the End"])
    artista: str = Field(..., min_length=1, max_length=255, examples=["Linkin Park"])
    album: str = Field(..., min_length=1, max_length=255, examples=["Hybrid Theory"])
    popularity: Optional[int] = Field(default=0, ge=0, le=100)
    danceability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    energy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tempo: Optional[float] = Field(default=None, ge=0.0)


class PopularidadeUpdate(BaseModel):
    popularity: int = Field(..., ge=0, le=100, examples=[90])

