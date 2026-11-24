from typing import Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.core.database import get_engine
from app.repositories import catalogo_repo
from app.schemas.contracts import (
    MusicaCreate,
    MusicaDetalheOut,
    MusicaOut,
    PopularidadeUpdate,
)

router = APIRouter(prefix="/musicas", tags=["Catálogo"])


@router.get("", response_model=list[MusicaOut])
def listar_musicas(
    termo: str = "",
    artista: Optional[str] = None,
    album: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Lista músicas com filtros por termo, artista ou álbum."""
    with get_engine().connect() as conn:
        rows = catalogo_repo.listar_musicas(
            conn, termo=termo, artista=artista, album=album, limit=limit, offset=offset
        )
        return [MusicaOut(**r) for r in rows]


@router.get("/{id_musica}", response_model=MusicaDetalheOut)
def detalhe_musica(id_musica: int):
    """Obtém detalhes e média de avaliações de uma música específica."""
    with get_engine().connect() as conn:
        row = catalogo_repo.buscar_detalhe_musica(conn, id_musica)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Música não encontrada.",
            )
        return MusicaDetalheOut(**row)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def criar_musica(payload: MusicaCreate):
    """Insere nova música no catálogo com transação atômica."""
    try:
        with get_engine().begin() as conn:
            id_musica = catalogo_repo.criar_musica_completa(
                conn,
                titulo=payload.titulo,
                artista=payload.artista,
                album=payload.album,
                popularity=payload.popularity or 0,
                danceability=payload.danceability,
                energy=payload.energy,
                tempo=payload.tempo,
            )
            return {"id_musica": id_musica, "mensagem": "Música cadastrada com sucesso!"}
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflito de integridade ao cadastrar música.",
        )


@router.patch("/{id_musica}/popularidade", response_model=dict)
def atualizar_popularidade_musica(id_musica: int, payload: PopularidadeUpdate):
    """Atualiza a popularidade de uma faixa."""
    with get_engine().begin() as conn:
        ok = catalogo_repo.atualizar_popularidade(conn, id_musica, payload.popularity)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Música não encontrada.",
            )
        return {
            "sucesso": True,
            "id_musica": id_musica,
            "nova_popularidade": payload.popularity,
        }


@router.delete("/{id_musica}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_musica(id_musica: int):
    """Remove uma faixa do catálogo."""
    with get_engine().begin() as conn:
        ok = catalogo_repo.remover_musica(conn, id_musica)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Música não encontrada.",
            )
    return None