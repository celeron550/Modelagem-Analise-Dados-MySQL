from typing import Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError
from app.core.database import get_engine
from app.repositories import avaliacoes_repo
from app.schemas.contracts import AvaliacaoCreate, AvaliacaoOut, AvaliacaoUpdate

router = APIRouter(prefix="/avaliacoes", tags=["Avaliações"])


@router.get("", response_model=list[AvaliacaoOut])
def listar_avaliacoes(id_musica: Optional[int] = None, limit: int = 100):
    """Lista avaliações cadastradas no banco."""
    with get_engine().connect() as conn:
        rows = avaliacoes_repo.listar_avaliacoes(conn, id_musica=id_musica, limit=limit)
        return [AvaliacaoOut(**r) for r in rows]


@router.post("", response_model=AvaliacaoOut, status_code=status.HTTP_201_CREATED)
def criar_avaliacao(payload: AvaliacaoCreate):
    """Registra uma nova avaliação real no banco com commit atômico."""
    id_user = 1
    try:
        with get_engine().begin() as conn:
            id_nova = avaliacoes_repo.criar_avaliacao(
                conn,
                id_usuario=id_user,
                id_musica=payload.id_musica,
                nota=payload.nota,
                comentario=payload.comentario,
            )
            criada = avaliacoes_repo.buscar_avaliacao_por_id(conn, id_nova)
            if not criada:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Falha ao recuperar avaliação recém-criada.",
                )
            return AvaliacaoOut(**criada)
    except IntegrityError as exc:
        orig_code = getattr(exc.orig, "args", [None])[0]
        if orig_code == 1062:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Usuário já avaliou esta música.",
            )
        if orig_code == 1452:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Música ou usuário não encontrado.",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Violação de integridade ao registrar avaliação.",
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc.orig),
        )


@router.put("/{id_avaliacao}", response_model=AvaliacaoOut)
def atualizar_avaliacao(id_avaliacao: int, payload: AvaliacaoUpdate):
    """Atualiza avaliação real disparando trg_auditoria_avaliacao e retorna o registro atualizado."""
    if payload.nota is None and payload.comentario is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe ao menos 'nota' ou 'comentario' para atualizar.",
        )

    with get_engine().begin() as conn:
        existente = avaliacoes_repo.buscar_avaliacao_por_id(conn, id_avaliacao)
        if not existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Avaliação não encontrada.",
            )

        avaliacoes_repo.atualizar_avaliacao(
            conn,
            id_avaliacao=id_avaliacao,
            nota=payload.nota,
            comentario=payload.comentario,
        )
        atualizada = avaliacoes_repo.buscar_avaliacao_por_id(conn, id_avaliacao)
        return AvaliacaoOut(**atualizada)


@router.delete("/{id_avaliacao}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_avaliacao(id_avaliacao: int):
    """Remove uma avaliação existente ou retorna 404."""
    with get_engine().begin() as conn:
        ok = avaliacoes_repo.deletar_avaliacao(conn, id_avaliacao)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Avaliação não encontrada.",
            )
    return None