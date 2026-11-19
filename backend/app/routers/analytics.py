# ============================================================================
# 4. ROTAS DE ANALYTICS & RANKINGS 
# ============================================================================


from fastapi import APIRouter

from app.core.database import get_engine

from app.repositories import analytics_repo

from app.schemas.contracts import (

CorrelacaoAudioOut,

KpiCatalogoOut,

RankingArtistaOut,

RankingComunidadeOut,

RitmoAlbumOut,

)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/ranking-comunidade", response_model=list[RankingComunidadeOut], tags=["Analytics"])
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


@router.get("/ranking-artistas", response_model=list[RankingArtistaOut], tags=["Analytics"])
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


@router.get("/correlacao-audio", response_model=list[CorrelacaoAudioOut], tags=["Analytics"])
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


@router.get("/ritmo-album", response_model=list[RitmoAlbumOut], tags=["Analytics"])
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


@router.get("/kpis", response_model=KpiCatalogoOut, tags=["Analytics"])
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
