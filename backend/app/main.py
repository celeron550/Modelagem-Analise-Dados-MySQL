from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import get_engine
from app.repositories import analytics_repo, avaliacoes_repo, catalogo_repo
from app.schemas.contracts import (
    AvaliacaoCreate,
    AvaliacaoOut,
    AvaliacaoUpdate,
    CorrelacaoAudioOut,
    KpiCatalogoOut,
    MusicaCreate,
    MusicaDetalheOut,
    MusicaOut,
    PopularidadeUpdate,
    RankingArtistaOut,
    RankingComunidadeOut,
    RitmoAlbumOut,
    RoleEnum,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
)

app = FastAPI(
    title="MusicRate API — Sistema de Avaliação Musical",
    description="API RESTful com autenticação JWT, catálogo musical e avaliações.",
    version="0.1.0-marco0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Infra"])
def health_check():
    """Health check do serviço."""
    return {"status": "ok", "milestone": "marco-0"}


# ============================================================================
# 1. ROTAS DE AUTENTICAÇÃO E USUÁRIOS (Trilha Dev 2)
# ============================================================================

@app.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Auth"])
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


@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(payload: UserLogin):
    mock_user = UserOut(
        id_usuario=1,
        username="felix_dev",
        email=payload.email,
        role=RoleEnum.USER,
        data_cadastro=datetime.now(timezone.utc),
    )
    return TokenResponse(access_token="mock-jwt-token-marco0", user=mock_user)


# ============================================================================
# 2. ROTAS DO CATÁLOGO MUSICAL (Trilha Dev 3 - Migração consultas.py + dashboard.py)
# ============================================================================

@app.get("/musicas", response_model=list[MusicaOut], tags=["Catálogo"])
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


@app.get("/musicas/{id_musica}", response_model=MusicaDetalheOut, tags=["Catálogo"])
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


@app.post("/musicas", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["Catálogo"])
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


@app.patch("/musicas/{id_musica}/popularidade", response_model=dict, tags=["Catálogo"])
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


@app.delete("/musicas/{id_musica}", status_code=status.HTTP_204_NO_CONTENT, tags=["Catálogo"])
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


# ============================================================================
# 3. ROTAS DE AVALIAÇÕES (Trilha Dev 3 - Migração CRUD dashboard.py)
# ============================================================================

@app.get("/avaliacoes", response_model=list[AvaliacaoOut], tags=["Avaliações"])
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


@app.post("/avaliacoes", response_model=AvaliacaoOut, status_code=status.HTTP_201_CREATED, tags=["Avaliações"])
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


@app.put("/avaliacoes/{id_avaliacao}", response_model=AvaliacaoOut, tags=["Avaliações"])
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


@app.delete("/avaliacoes/{id_avaliacao}", status_code=status.HTTP_204_NO_CONTENT, tags=["Avaliações"])
def deletar_avaliacao(id_avaliacao: int):
    """Remove uma avaliação existente."""
    try:
        with get_engine().connect() as conn:
            avaliacoes_repo.deletar_avaliacao(conn, id_avaliacao)
    except Exception:
        pass
    return None


# ============================================================================
# 4. ROTAS DE ANALYTICS & RANKINGS (Trilha Dev 3 & Dev 4 - Migração consultas.py)
# ============================================================================

@app.get("/analytics/ranking-comunidade", response_model=list[RankingComunidadeOut], tags=["Analytics"])
def ranking_comunidade(limit: int = 50):
    """Top faixas avaliadas pela comunidade através da view vw_ranking_comunidade."""
    try:
        with get_engine().connect() as conn:
            rows = analytics_repo.ranking_comunidade(conn, limit=limit)
            if rows:
                return [RankingComunidadeOut(**r) for r in rows]
    except Exception:
        pass

    return [
        RankingComunidadeOut(
            id_musica=1,
            artista="Linkin Park",
            faixa="In the End",
            total_avaliacoes=1,
            nota_media=9.5,
            maior_nota=9.5,
            menor_nota=9.5,
        )
    ]


@app.get("/analytics/ranking-artistas", response_model=list[RankingArtistaOut], tags=["Analytics"])
def ranking_artistas(limit: int = 10):
    """Ranking de artistas por popularidade agregada (migrado de consultas.py - rank_popularidade)."""
    try:
        with get_engine().connect() as conn:
            rows = analytics_repo.rank_popularidade(conn, min_faixas=1, limit=limit)
            if rows:
                return [RankingArtistaOut(**r) for r in rows]
    except Exception:
        pass

    return [
        RankingArtistaOut(artista="Linkin Park", total_faixas=2, popularidade_media=88.5),
        RankingArtistaOut(artista="Daft Punk", total_faixas=1, popularidade_media=85.0),
    ]


@app.get("/analytics/correlacao-audio", response_model=list[CorrelacaoAudioOut], tags=["Analytics"])
def correlacao_audio(min_popularity: int = 60):
    """Relação entre energia, danceability e popularidade (migrado de consultas.py - analise_audio)."""
    try:
        with get_engine().connect() as conn:
            rows = analytics_repo.analise_audio(conn, min_popularity=min_popularity)
            if rows:
                return [CorrelacaoAudioOut(**r) for r in rows]
    except Exception:
        pass

    return [
        CorrelacaoAudioOut(
            musica="In the End",
            artista="Linkin Park",
            danceability=0.556,
            energy=0.864,
            popularity=88,
        ),
        CorrelacaoAudioOut(
            musica="Numb",
            artista="Linkin Park",
            danceability=0.496,
            energy=0.863,
            popularity=89,
        ),
    ]


@app.get("/analytics/ritmo-album", response_model=list[RitmoAlbumOut], tags=["Analytics"])
def ritmo_album():
    """Estatísticas de BPM por álbum de cada artista (migrado de consultas.py - ritmo_album)."""
    try:
        with get_engine().connect() as conn:
            rows = analytics_repo.ritmo_album(conn)
            if rows:
                return [RitmoAlbumOut(**r) for r in rows]
    except Exception:
        pass

    return [
        RitmoAlbumOut(
            artista="Linkin Park",
            album="Hybrid Theory",
            qtd_musicas=1,
            bpm_medio=105.1,
            bpm_minimo=105.1,
            bpm_maximo=105.1,
        ),
        RitmoAlbumOut(
            artista="Linkin Park",
            album="Meteora",
            qtd_musicas=1,
            bpm_medio=110.0,
            bpm_minimo=110.0,
            bpm_maximo=110.0,
        ),
    ]


@app.get("/analytics/kpis", response_model=KpiCatalogoOut, tags=["Analytics"])
def kpis_catalogo():
    """Indicadores consolidados (COUNT, AVG, MAX, MIN) migrados de dashboard.py."""
    try:
        with get_engine().connect() as conn:
            res = analytics_repo.kpi_catalogo(conn)
            return KpiCatalogoOut(**res)
    except Exception:
        pass

    return KpiCatalogoOut(
        total_musicas=3,
        popularidade_media=87.3,
        popularidade_maxima=89,
        popularidade_minima=85,
        dancabilidade_media=0.615,
        energia_media=0.846,
    )
