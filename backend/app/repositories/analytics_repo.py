from typing import Any
from sqlalchemy import text
from sqlalchemy.engine import Connection
from app.core.config import settings


def rank_artistas(conn: Connection, limit: int = 10) -> list[dict[str, Any]]:
    """Evolução de rank_artistas() de consultas.py."""
    sql = text(f"""
        SELECT
            ar.nome AS artista,
            COUNT(m.id_musica) AS total_faixas,
            ROUND(AVG(m.popularity), 1) AS popularidade_media
        FROM {settings.DB_ANALISE_NAME}.Artista ar
        JOIN {settings.DB_ANALISE_NAME}.Album al ON ar.id_artista = al.id_artista
        JOIN {settings.DB_ANALISE_NAME}.Musica m ON al.id_album = m.id_album
        GROUP BY ar.id_artista, ar.nome
        ORDER BY popularidade_media DESC
        LIMIT :limit;
    """)
    result = conn.execute(sql, {"limit": limit}).mappings().all()
    return [dict(r) for r in result]


def rank_popularidade(conn: Connection, min_faixas: int = 1, limit: int = 10) -> list[dict[str, Any]]:
    """Evolução de rank_popularidade() de consultas.py com agregação por artista."""
    sql = text(f"""
        SELECT
            ar.nome AS artista,
            COUNT(m.id_musica) AS total_faixas,
            ROUND(AVG(m.popularity), 2) AS popularidade_media
        FROM {settings.DB_ANALISE_NAME}.Artista ar
        JOIN {settings.DB_ANALISE_NAME}.Album al ON ar.id_artista = al.id_artista
        JOIN {settings.DB_ANALISE_NAME}.Musica m ON al.id_album = m.id_album
        GROUP BY ar.id_artista, ar.nome
        HAVING COUNT(m.id_musica) >= :min_faixas
        ORDER BY popularidade_media DESC
        LIMIT :limit;
    """)
    result = conn.execute(sql, {"min_faixas": min_faixas, "limit": limit}).mappings().all()
    return [dict(r) for r in result]


def analise_audio(conn: Connection, min_popularity: int = 60) -> list[dict[str, Any]]:
    """Evolução de analise_audio() de consultas.py mapeada para CorrelacaoAudioOut."""
    sql = text(f"""
        SELECT
            m.titulo AS musica,
            ar.nome AS artista,
            ROUND(CAST(m.danceability AS FLOAT), 4) AS danceability,
            ROUND(CAST(m.energy AS FLOAT), 4) AS energy,
            m.popularity AS popularity
        FROM {settings.DB_ANALISE_NAME}.Musica m
        JOIN {settings.DB_ANALISE_NAME}.Album al ON m.id_album = al.id_album
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        WHERE m.popularity >= :min_popularity
        ORDER BY m.popularity DESC;
    """)
    result = conn.execute(sql, {"min_popularity": min_popularity}).mappings().all()
    return [dict(r) for r in result]


def ritmo_album(conn: Connection) -> list[dict[str, Any]]:
    """Evolução de ritmo_album() de consultas.py com métricas de BPM por álbum."""
    sql = text(f"""
        SELECT
            ar.nome AS artista,
            al.nome AS album,
            COUNT(m.id_musica) AS qtd_musicas,
            ROUND(AVG(m.tempo), 1) AS bpm_medio,
            ROUND(MIN(m.tempo), 1) AS bpm_minimo,
            ROUND(MAX(m.tempo), 1) AS bpm_maximo
        FROM {settings.DB_ANALISE_NAME}.Album al
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        JOIN {settings.DB_ANALISE_NAME}.Musica m ON al.id_album = m.id_album
        GROUP BY ar.nome, al.nome
        ORDER BY ar.nome, bpm_medio DESC;
    """)
    result = conn.execute(sql).mappings().all()
    return [dict(r) for r in result]


def ranking_comunidade(conn: Connection, limit: int = 50) -> list[dict[str, Any]]:
    """Consulta a view vw_ranking_comunidade ou realiza agregação inter-schema com fallback."""
    try:
        sql_view = text(f"SELECT * FROM {settings.DB_APP_NAME}.vw_ranking_comunidade LIMIT :limit")
        result = conn.execute(sql_view, {"limit": limit}).mappings().all()
        if result:
            return [dict(r) for r in result]
    except Exception:
        pass

    sql_agg = text(f"""
        SELECT
            m.id_musica,
            ar.nome AS artista,
            m.titulo AS faixa,
            COUNT(av.id_avaliacao) AS total_avaliacoes,
            ROUND(AVG(av.nota), 1) AS nota_media,
            MAX(av.nota) AS maior_nota,
            MIN(av.nota) AS menor_nota
        FROM {settings.DB_ANALISE_NAME}.Musica m
        JOIN {settings.DB_ANALISE_NAME}.Album al ON m.id_album = al.id_album
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        JOIN {settings.DB_APP_NAME}.Avaliacao_Musica av ON m.id_musica = av.id_musica
        GROUP BY m.id_musica, ar.nome, m.titulo
        HAVING total_avaliacoes > 0
        ORDER BY nota_media DESC, total_avaliacoes DESC
        LIMIT :limit;
    """)
    result = conn.execute(sql_agg, {"limit": limit}).mappings().all()
    return [dict(r) for r in result]


def kpi_catalogo(conn: Connection) -> dict[str, Any]:
    """Agregações gerais (COUNT, AVG, MAX, MIN) provenientes das seções do dashboard.py."""
    sql = text(f"""
        SELECT
            COUNT(m.id_musica) AS total_musicas,
            ROUND(AVG(m.popularity), 1) AS popularidade_media,
            COALESCE(MAX(m.popularity), 0) AS popularidade_maxima,
            COALESCE(MIN(m.popularity), 0) AS popularidade_minima,
            ROUND(AVG(m.danceability), 3) AS dancabilidade_media,
            ROUND(AVG(m.energy), 3) AS energia_media
        FROM {settings.DB_ANALISE_NAME}.Musica m;
    """)
    row = conn.execute(sql).mappings().first()
    return dict(row) if row else {
        "total_musicas": 0,
        "popularidade_media": 0.0,
        "popularidade_maxima": 0,
        "popularidade_minima": 0,
        "dancabilidade_media": 0.0,
        "energia_media": 0.0,
    }
