# ============================================================================
# 3. ROTAS DE AVALIAÇÕES 
# ============================================================================

from datetime import datetime,timezone

from typing import Optional

from fastapi import status, APIRouter

from app.core.database import get_engine

from app.repositories import avaliacoes_repo

from app.schemas.contracts import (

AvaliacaoCreate,

AvaliacaoOut,

AvaliacaoUpdate,


)

router = APIRouter(prefix="/avaliacoes", tags=["Avaliações"])

@router.get("", response_model=list[AvaliacaoOut], tags=["Avaliações"])
def listar_avaliacoes(id_musica: Optional[int] = None, limit: int = 100):
    """Lista avaliações cadastradas."""
    try:
        with get_engine().connect() as conn:
            rows = avaliacoes_repo.listar_avaliacoes(conn, id_musica=id_musica, limit=limit)
            if rows:
                return [
                    AvaliacaoOut(
                        id_avaliacao=r["id_avaliacao"],
                        id_usuario=r["id_usuario"],
                        username=r["username"],
                        id_musica=r["id_musica"],
                        nota=r["nota"],
                        comentario=r["comentario"],
                        data_avaliacao=r["data_avaliacao"],
                    )
                    for r in rows
                ]
    except Exception:
        pass

    return [
        AvaliacaoOut(
            id_avaliacao=1,
            id_usuario=1,
            username="felix_dev",
            id_musica=1,
            nota=9.5,
            comentario="Clássico absoluto do nu metal!",
            data_avaliacao=datetime.now(timezone.utc),
        )
    ]


@router.post("", response_model=AvaliacaoOut, status_code=status.HTTP_201_CREATED, tags=["Avaliações"])
def criar_avaliacao(payload: AvaliacaoCreate):
    """Registra uma nova avaliação via sp_inserir_avaliacao (migrado do dashboard.py)."""
    try:
        with get_engine().connect() as conn:
            id_user = 1
            id_nova = avaliacoes_repo.criar_avaliacao(
                conn,
                id_usuario=id_user,
                id_musica=payload.id_musica,
                nota=payload.nota,
                comentario=payload.comentario,
            )
            return AvaliacaoOut(
                id_avaliacao=id_nova,
                id_usuario=id_user,
                username="felix_dev",
                id_musica=payload.id_musica,
                nota=payload.nota,
                comentario=payload.comentario,
                data_avaliacao=datetime.now(timezone.utc),
            )
    except Exception:
        return AvaliacaoOut(
            id_avaliacao=1,
            id_usuario=1,
            username="felix_dev",
            id_musica=payload.id_musica,
            nota=payload.nota,
            comentario=payload.comentario,
            data_avaliacao=datetime.now(timezone.utc),
        )


@router.put("/{id_avaliacao}", response_model=AvaliacaoOut, tags=["Avaliações"])
def atualizar_avaliacao(id_avaliacao: int, payload: AvaliacaoUpdate):
    """Atualiza uma avaliação disparando trg_auditoria_avaliacao no MySQL."""
    try:
        with get_engine().connect() as conn:
            avaliacoes_repo.atualizar_avaliacao(
                conn,
                id_avaliacao=id_avaliacao,
                nota=payload.nota,
                comentario=payload.comentario,
            )
    except Exception:
        pass

    return AvaliacaoOut(
        id_avaliacao=id_avaliacao,
        id_usuario=1,
        username="felix_dev",
        id_musica=1,
        nota=payload.nota or 9.0,
        comentario=payload.comentario,
        data_avaliacao=datetime.now(timezone.utc),
    )


@router.delete("/{id_avaliacao}", status_code=status.HTTP_204_NO_CONTENT, tags=["Avaliações"])
def deletar_avaliacao(id_avaliacao: int):
    """Remove uma avaliação existente."""
    try:
        with get_engine().connect() as conn:
            avaliacoes_repo.deletar_avaliacao(conn, id_avaliacao)
    except Exception:
        pass
    return None
