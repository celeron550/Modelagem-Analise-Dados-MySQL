import uuid
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_engine
from app.main import app

client = TestClient(app)


def _criar_musica_teste() -> int:
    sufixo = uuid.uuid4().hex[:8]
    res = client.post(
        "/musicas",
        json={
            "titulo": f"Faixa Teste {sufixo}",
            "artista": f"Artista Teste {sufixo}",
            "album": f"Album Teste {sufixo}",
            "popularity": 80,
            "danceability": 0.7,
            "energy": 0.8,
            "tempo": 120.0,
        },
    )
    assert res.status_code == 201
    return res.json()["id_musica"]


def test_criar_avaliacao_sucesso():
    id_musica = _criar_musica_teste()

    res = client.post(
        "/avaliacoes",
        json={
            "id_musica": id_musica,
            "nota": 9.5,
            "comentario": "Produção impecável!",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["id_musica"] == id_musica
    assert data["nota"] == 9.5
    assert data["comentario"] == "Produção impecável!"
    assert "id_avaliacao" in data
    assert "data_avaliacao" in data


def test_criar_avaliacao_nota_invalida_422():
    res = client.post(
        "/avaliacoes",
        json={
            "id_musica": 1,
            "nota": 11.0,
            "comentario": "Nota acima do limite permitido",
        },
    )
    assert res.status_code == 422


def test_criar_avaliacao_duplicada_409():
    id_musica = _criar_musica_teste()
    payload = {
        "id_musica": id_musica,
        "nota": 8.0,
        "comentario": "Primeira avaliação",
    }

    res_1 = client.post("/avaliacoes", json=payload)
    assert res_1.status_code == 201

    res_2 = client.post("/avaliacoes", json=payload)
    assert res_2.status_code == 409


def test_atualizar_avaliacao_dispara_trigger_auditoria():
    id_musica = _criar_musica_teste()

    res_create = client.post(
        "/avaliacoes",
        json={
            "id_musica": id_musica,
            "nota": 7.0,
            "comentario": "Nota inicial",
        },
    )
    assert res_create.status_code == 201
    id_avaliacao = res_create.json()["id_avaliacao"]

    res_update = client.put(
        f"/avaliacoes/{id_avaliacao}",
        json={"nota": 9.0, "comentario": "Subindo a nota após ouvir de novo"},
    )
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["id_avaliacao"] == id_avaliacao
    assert updated_data["nota"] == 9.0
    assert updated_data["comentario"] == "Subindo a nota após ouvir de novo"

    # Confirma no banco que a trigger trg_auditoria_avaliacao gravou em Log_Avaliacoes
    with get_engine().connect() as conn:
        sql_log = text(f"""
            SELECT id_avaliacao, nota_antiga, nota_nova
            FROM {settings.DB_APP_NAME}.Log_Avaliacoes
            WHERE id_avaliacao = :id_avaliacao
            ORDER BY id_log DESC
            LIMIT 1
        """)
        log_row = conn.execute(sql_log, {"id_avaliacao": id_avaliacao}).mappings().first()

    assert log_row is not None
    assert float(log_row["nota_antiga"]) == 7.0
    assert float(log_row["nota_nova"]) == 9.0


def test_atualizar_avaliacao_inexistente_404():
    res = client.put(
        "/avaliacoes/99999999",
        json={"nota": 8.5, "comentario": "Não existe"},
    )
    assert res.status_code == 404