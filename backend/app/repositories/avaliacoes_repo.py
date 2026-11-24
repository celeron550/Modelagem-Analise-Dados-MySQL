from typing import Any
from sqlalchemy import text
from sqlalchemy.engine import Connection
from app.core.config import settings


def listar_avaliacoes_por_album(conn: Connection, nome_album: str) -> list[dict[str, Any]]:
    """Evolução de query_album() de consultas.py cruzando catálogo e avaliações."""
    sql = text(f"""
        SELECT
            al.nome AS album,
            ar.nome AS artista,
            m.titulo AS faixa,
            m.popularity,
            CAST(m.tempo AS FLOAT) AS bpm,
            COUNT(av.id_avaliacao) AS total_avaliacoes,
            ROUND(AVG(av.nota), 1) AS nota_media
        FROM {settings.DB_ANALISE_NAME}.Album al
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        LEFT JOIN {settings.DB_ANALISE_NAME}.Musica m ON al.id_album = m.id_album
        LEFT JOIN {settings.DB_APP_NAME}.Avaliacao_Musica av ON m.id_musica = av.id_musica
        WHERE al.nome = :nome_album
        GROUP BY al.nome, ar.nome, m.titulo, m.popularity, m.tempo
        ORDER BY m.titulo;
    """)
    result = conn.execute(sql, {"nome_album": nome_album}).mappings().all()
    return [dict(r) for r in result]


def listar_avaliacoes(
    conn: Connection,
    id_musica: int | None = None,
    id_usuario: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Lista avaliações com dados do usuário e da música."""
    conditions = ["1=1"]
    params: dict[str, Any] = {"limit": limit}

    if id_musica:
        conditions.append("av.id_musica = :id_musica")
        params["id_musica"] = id_musica

    if id_usuario:
        conditions.append("av.id_usuario = :id_usuario")
        params["id_usuario"] = id_usuario

    where_clause = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            av.id_avaliacao,
            av.id_usuario,
            u.username,
            av.id_musica,
            m.titulo AS faixa,
            ar.nome AS artista,
            CAST(av.nota AS FLOAT) AS nota,
            av.comentario,
            av.data_avaliacao
        FROM {settings.DB_APP_NAME}.Avaliacao_Musica av
        JOIN {settings.DB_APP_NAME}.Usuario u ON av.id_usuario = u.id_usuario
        JOIN {settings.DB_ANALISE_NAME}.Musica m ON av.id_musica = m.id_musica
        JOIN {settings.DB_ANALISE_NAME}.Album al ON m.id_album = al.id_album
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        WHERE {where_clause}
        ORDER BY av.data_avaliacao DESC
        LIMIT :limit;
    """)
    result = conn.execute(sql, params).mappings().all()
    return [dict(r) for r in result]


def buscar_avaliacao_por_id(conn: Connection, id_avaliacao: int) -> dict[str, Any] | None:
    """Busca uma avaliação específica por ID."""
    sql = text(f"""
        SELECT
            av.id_avaliacao,
            av.id_usuario,
            u.username,
            av.id_musica,
            m.titulo AS faixa,
            ar.nome AS artista,
            CAST(av.nota AS FLOAT) AS nota,
            av.comentario,
            av.data_avaliacao
        FROM {settings.DB_APP_NAME}.Avaliacao_Musica av
        JOIN {settings.DB_APP_NAME}.Usuario u ON av.id_usuario = u.id_usuario
        JOIN {settings.DB_ANALISE_NAME}.Musica m ON av.id_musica = m.id_musica
        JOIN {settings.DB_ANALISE_NAME}.Album al ON m.id_album = al.id_album
        JOIN {settings.DB_ANALISE_NAME}.Artista ar ON al.id_artista = ar.id_artista
        WHERE av.id_avaliacao = :id_avaliacao
    """)
    row = conn.execute(sql, {"id_avaliacao": id_avaliacao}).mappings().first()
    return dict(row) if row else None


def criar_avaliacao(
    conn: Connection,
    id_usuario: int,
    id_musica: int,
    nota: float,
    comentario: str | None = None,
) -> int:
    """Insere avaliação no banco deixando erros de integridade (FK/UNIQUE) propagarem."""
    sql_insert = text(f"""
        INSERT INTO {settings.DB_APP_NAME}.Avaliacao_Musica
            (id_usuario, id_musica, nota, comentario)
        VALUES
            (:user, :musica, :nota, :comentario)
    """)
    res = conn.execute(sql_insert, {
        "user": id_usuario,
        "musica": id_musica,
        "nota": nota,
        "comentario": comentario,
    })
    return res.lastrowid


def atualizar_avaliacao(
    conn: Connection,
    id_avaliacao: int,
    nota: float | None = None,
    comentario: str | None = None,
) -> bool:
    """Atualiza avaliação disparando a trigger trg_auditoria_avaliacao no MySQL."""
    fields = []
    params: dict[str, Any] = {"id_avaliacao": id_avaliacao}

    if nota is not None:
        fields.append("nota = :nota")
        params["nota"] = nota

    if comentario is not None:
        fields.append("comentario = :comentario")
        params["comentario"] = comentario

    if not fields:
        return False

    sql = text(f"UPDATE {settings.DB_APP_NAME}.Avaliacao_Musica SET {', '.join(fields)} WHERE id_avaliacao = :id_avaliacao")
    res = conn.execute(sql, params)
    return res.rowcount > 0


def deletar_avaliacao(conn: Connection, id_avaliacao: int) -> bool:
    """Remove uma avaliação pelo ID."""
    sql = text(f"DELETE FROM {settings.DB_APP_NAME}.Avaliacao_Musica WHERE id_avaliacao = :id_avaliacao")
    res = conn.execute(sql, {"id_avaliacao": id_avaliacao})
    return res.rowcount > 0


def obter_ou_criar_usuario(
    conn: Connection,
    username: str,
    email: str | None = None,
    role: str = "USER",
) -> dict[str, Any]:
    """Busca um usuário pelo username ou cria um novo registro padrão."""
    sql_find = text(f"SELECT * FROM {settings.DB_APP_NAME}.Usuario WHERE username = :username")
    row = conn.execute(sql_find, {"username": username}).mappings().first()
    if row:
        return dict(row)

    default_email = email or f"{username.lower().replace(' ', '_')}@musicrate.com"
    sql_ins = text(f"""
        INSERT INTO {settings.DB_APP_NAME}.Usuario (username, email, senha_hash, role)
        VALUES (:username, :email, 'mock_hash', :role)
    """)
    res = conn.execute(sql_ins, {"username": username, "email": default_email, "role": role})
    new_id = res.lastrowid
    return {
        "id_usuario": new_id,
        "username": username,
        "email": default_email,
        "role": role,
    }