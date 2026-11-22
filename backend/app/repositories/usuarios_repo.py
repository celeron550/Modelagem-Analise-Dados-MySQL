from sqlalchemy import text
from sqlalchemy.engine import Connection


def criar_usuario(
    conn: Connection,
    username: str,
    email: str,
    senha_hash: str,
    role: str = "USER",
) -> dict:
    insert_sql = text("""
        INSERT INTO db_app_musica.Usuario (username, email, senha_hash, role)
        VALUES (:username, :email, :senha_hash, :role)
    """)
    result = conn.execute(
        insert_sql,
        {
            "username": username,
            "email": email,
            "senha_hash": senha_hash,
            "role": role,
        },
    )
    user_id = result.lastrowid
    return buscar_usuario_por_id(conn, user_id)


def buscar_usuario_por_email(conn: Connection, email: str) -> dict | None:
    sql = text("""
        SELECT id_usuario, username, email, senha_hash, role, data_cadastro
        FROM db_app_musica.Usuario
        WHERE email = :email
    """)
    row = conn.execute(sql, {"email": email}).mappings().first()
    return dict(row) if row else None


def buscar_usuario_por_id(conn: Connection, id_usuario: int) -> dict | None:
    sql = text("""
        SELECT id_usuario, username, email, role, data_cadastro
        FROM db_app_musica.Usuario
        WHERE id_usuario = :id_usuario
    """)
    row = conn.execute(sql, {"id_usuario": id_usuario}).mappings().first()
    return dict(row) if row else None