from typing import Any
from sqlalchemy import text
from sqlalchemy.engine import Connection
from app.core.config import settings


def buscar_detalhe_musica(conn: Connection, id_musica: int) -> dict[str, Any] | None:
    """Busca detalhes completos de uma faixa com estatísticas da comunidade (Marco 0 / Dev 3)."""
    sql = text(f"""
        SELECT
            m.id_musica,
            m.titulo,
            ar.nome AS artista,
            al.nome AS album,
            m.popularity,
            CAST(m.danceability AS FLOAT) AS danceability,
            CAST(m.energy AS FLOAT) AS energy,
            CAST(m.tempo AS FLOAT) AS tempo,
            COUNT(av.id_avaliacao) AS total_reviews,
            ROUND(AVG(av.nota), 1) AS nota_comunidade
        FROM {settings.DB_ANALISE_NAME}.Musica m
        JOIN {settings.DB_ANALISE_NAME}.Album al ON m.id_album = al.id_album
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        LEFT JOIN {settings.DB_APP_NAME}.Avaliacao_Musica av ON m.id_musica = av.id_musica
        WHERE m.id_musica = :id_musica
        GROUP BY m.id_musica, m.titulo, ar.nome, al.nome,
                 m.popularity, m.danceability, m.energy, m.tempo
    """)
    row = conn.execute(sql, {"id_musica": id_musica}).mappings().first()
    return dict(row) if row else None


def buscar_musica_por_faixa(conn: Connection, nome_musica: str) -> list[dict[str, Any]]:
    """Evolução de query_musica() de consultas.py: busca faixas pelo título."""
    sql = text(f"""
        SELECT
            m.id_musica,
            m.titulo,
            ar.nome AS artista,
            al.nome AS album,
            m.popularity,
            CAST(m.danceability AS FLOAT) AS danceability,
            CAST(m.energy AS FLOAT) AS energy,
            CAST(m.tempo AS FLOAT) AS tempo
        FROM {settings.DB_ANALISE_NAME}.Musica m
        JOIN {settings.DB_ANALISE_NAME}.Album al ON m.id_album = al.id_album
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        WHERE m.titulo = :nome_musica
        ORDER BY m.popularity DESC;
    """)
    result = conn.execute(sql, {"nome_musica": nome_musica}).mappings().all()
    return [dict(r) for r in result]


def listar_musicas(
    conn: Connection,
    termo: str = "",
    artista: str | None = None,
    album: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Lista músicas com suporte a busca textual por faixa ou artista e paginação."""
    conditions = ["1=1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if termo:
        conditions.append("(m.titulo LIKE :termo OR ar.nome LIKE :termo)")
        params["termo"] = f"%{termo}%"

    if artista:
        conditions.append("ar.nome = :artista")
        params["artista"] = artista

    if album:
        conditions.append("al.nome = :album")
        params["album"] = album

    where_clause = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            m.id_musica,
            m.titulo,
            ar.nome AS artista,
            al.nome AS album,
            m.popularity,
            CAST(m.danceability AS FLOAT) AS danceability,
            CAST(m.energy AS FLOAT) AS energy,
            CAST(m.tempo AS FLOAT) AS tempo
        FROM {settings.DB_ANALISE_NAME}.Musica m
        JOIN {settings.DB_ANALISE_NAME}.Album al ON m.id_album = al.id_album
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        WHERE {where_clause}
        ORDER BY m.id_musica DESC
        LIMIT :limit OFFSET :offset;
    """)
    result = conn.execute(sql, params).mappings().all()
    return [dict(r) for r in result]


def musicas_por_artista(conn: Connection, nome_artista: str) -> list[dict[str, Any]]:
    """Evolução de musicas_por_artista() de consultas.py."""
    sql = text(f"""
        SELECT
            m.id_musica,
            m.titulo,
            ar.nome AS artista,
            al.nome AS album,
            m.popularity,
            CAST(m.danceability AS FLOAT) AS danceability,
            CAST(m.energy AS FLOAT) AS energy,
            CAST(m.tempo AS FLOAT) AS tempo
        FROM {settings.DB_ANALISE_NAME}.Musica m
        JOIN {settings.DB_ANALISE_NAME}.Album al ON m.id_album = al.id_album
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        WHERE ar.nome = :nome_artista
        ORDER BY m.popularity DESC;
    """)
    result = conn.execute(sql, {"nome_artista": nome_artista}).mappings().all()
    return [dict(r) for r in result]


def musicas_por_album(conn: Connection, nome_album: str) -> list[dict[str, Any]]:
    """Evolução de musicas_por_album() de consultas.py."""
    sql = text(f"""
        SELECT
            m.id_musica,
            m.titulo,
            al.nome AS album,
            CAST(m.tempo AS FLOAT) AS bpm,
            CAST(m.energy AS FLOAT) AS energy,
            CAST(m.danceability AS FLOAT) AS danceability,
            m.popularity
        FROM {settings.DB_ANALISE_NAME}.Musica m
        JOIN {settings.DB_ANALISE_NAME}.Album al ON m.id_album = al.id_album
        WHERE al.nome = :nome_album
        ORDER BY m.titulo;
    """)
    result = conn.execute(sql, {"nome_album": nome_album}).mappings().all()
    return [dict(r) for r in result]


def criar_musica_completa(
    conn: Connection,
    titulo: str,
    artista: str,
    album: str,
    popularity: int = 0,
    danceability: float | None = None,
    energy: float | None = None,
    tempo: float | None = None,
) -> int:
    """Operação de CREATE do dashboard.py migrada para repositório seguro."""
    # 1. Artista (reaproveita ou cria)
    sql_art_find = text(f"SELECT id_artista FROM {settings.DB_ANALISE_NAME}.Artista WHERE nome = :nome")
    row_art = conn.execute(sql_art_find, {"nome": artista}).first()
    if row_art:
        id_artista = row_art[0]
    else:
        sql_art_ins = text(f"INSERT INTO {settings.DB_ANALISE_NAME}.Artista (nome) VALUES (:nome)")
        res_art = conn.execute(sql_art_ins, {"nome": artista})
        id_artista = res_art.lastrowid

    # 2. Album (reaproveita ou cria)
    sql_alb_find = text(
        f"SELECT id_album FROM {settings.DB_ANALISE_NAME}.Album WHERE nome = :nome AND id_artista = :id_artista"
    )
    row_alb = conn.execute(sql_alb_find, {"nome": album, "id_artista": id_artista}).first()
    if row_alb:
        id_album = row_alb[0]
    else:
        sql_alb_ins = text(
            f"INSERT INTO {settings.DB_ANALISE_NAME}.Album (id_artista, nome) VALUES (:id_artista, :nome)"
        )
        res_alb = conn.execute(sql_alb_ins, {"id_artista": id_artista, "nome": album})
        id_album = res_alb.lastrowid

    # 3. Musica
    sql_mus_ins = text(f"""
        INSERT INTO {settings.DB_ANALISE_NAME}.Musica
            (id_album, titulo, popularity, danceability, energy, tempo)
        VALUES
            (:id_album, :titulo, :popularity, :danceability, :energy, :tempo)
    """)
    res_mus = conn.execute(sql_mus_ins, {
        "id_album": id_album,
        "titulo": titulo,
        "popularity": popularity,
        "danceability": danceability,
        "energy": energy,
        "tempo": tempo,
    })
    conn.commit()
    return res_mus.lastrowid


def atualizar_popularidade(conn: Connection, id_musica: int, nova_popularidade: int) -> bool:
    """Operação de UPDATE do dashboard.py migrada para repositório seguro."""
    sql = text(f"UPDATE {settings.DB_ANALISE_NAME}.Musica SET popularity = :pop WHERE id_musica = :id")
    res = conn.execute(sql, {"pop": nova_popularidade, "id": id_musica})
    conn.commit()
    return res.rowcount > 0


def remover_musica(conn: Connection, id_musica: int) -> bool:
    """Operação de DELETE do dashboard.py migrada para repositório seguro."""
    sql = text(f"DELETE FROM {settings.DB_ANALISE_NAME}.Musica WHERE id_musica = :id")
    res = conn.execute(sql, {"id": id_musica})
    conn.commit()
    return res.rowcount > 0
