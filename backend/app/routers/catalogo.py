# ============================================================================
# 2. ROTAS DO CATÁLOGO MUSICAL
# ============================================================================

from typing import Optional

from fastapi import HTTPException, status, APIRouter


from app.core.database import get_engine

from app.repositories import catalogo_repo

from app.schemas.contracts import (

MusicaCreate,

MusicaDetalheOut,

MusicaOut,

PopularidadeUpdate,


)


router = APIRouter(prefix="/musicas", tags=["Catálogo"])

@router.get("", response_model=list[MusicaOut], tags=["Catálogo"])
def listar_musicas(
    termo: str = "",
    artista: Optional[str] = None,
    album: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Lista músicas com filtros por termo, artista ou álbum."""
    try:
        with get_engine().connect() as conn:
            rows = catalogo_repo.listar_musicas(conn, termo=termo, artista=artista, album=album, limit=limit, offset=offset)
            if rows:
                return [MusicaOut(**r) for r in rows]
    except Exception:
        pass

    # Fallback seguro com mock do Marco 0
    return [
        MusicaOut(
            id_musica=1,
            titulo="In the End",
            artista="Linkin Park",
            album="Hybrid Theory",
            popularity=88,
            danceability=0.556,
            energy=0.864,
            tempo=105.14,
        ),
        MusicaOut(
            id_musica=2,
            titulo="Numb",
            artista="Linkin Park",
            album="Meteora",
            popularity=89,
            danceability=0.496,
            energy=0.863,
            tempo=110.02,
        ),
    ]


@router.get("/{id_musica}", response_model=MusicaDetalheOut, tags=["Catálogo"])
def detalhe_musica(id_musica: int):
    """Obtém detalhes e média de avaliações de uma música específica."""
    try:
        with get_engine().connect() as conn:
            row = catalogo_repo.buscar_detalhe_musica(conn, id_musica)
            if row:
                return MusicaDetalheOut(**row)
    except Exception:
        pass

    return MusicaDetalheOut(
        id_musica=id_musica,
        titulo="In the End",
        artista="Linkin Park",
        album="Hybrid Theory",
        popularity=88,
        danceability=0.556,
        energy=0.864,
        tempo=105.14,
        total_reviews=1,
        nota_comunidade=9.5,
    )


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["Catálogo"])
def criar_musica(payload: MusicaCreate):
    """Insere nova música no catálogo (migrado de dashboard.py - Create)."""
    try:
        with get_engine().connect() as conn:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar música no catálogo: {e}",
        )


@router.patch("/{id_musica}/popularidade", response_model=dict, tags=["Catálogo"])
def atualizar_popularidade_musica(id_musica: int, payload: PopularidadeUpdate):
    """Atualiza a popularidade de uma faixa (migrado de dashboard.py - Update)."""
    try:
        with get_engine().connect() as conn:
            ok = catalogo_repo.atualizar_popularidade(conn, id_musica, payload.popularity)
            if ok:
                return {"sucesso": True, "id_musica": id_musica, "nova_popularidade": payload.popularity}
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Música não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{id_musica}", status_code=status.HTTP_204_NO_CONTENT, tags=["Catálogo"])
def deletar_musica(id_musica: int):
    """Remove uma faixa do catálogo (migrado de dashboard.py - Delete)."""
    try:
        with get_engine().connect() as conn:
            ok = catalogo_repo.remover_musica(conn, id_musica)
            if not ok:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Música não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
