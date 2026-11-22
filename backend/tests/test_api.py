from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["milestone"] == "marco-0"


def test_auth_register():
    payload = {
        "username": "tester",
        "email": "tester@ufrn.br",
        "password": "SenhaForte123",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "tester"
    assert data["email"] == "tester@ufrn.br"
    assert data["role"] == "USER"


def test_auth_login():
    client.post(
        "/auth/register",
        json={"username": "felix_ci", "email": "felix_ci@ufrn.br", "password": "SenhaForte123"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "felix_ci@ufrn.br", "password": "SenhaForte123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_listar_musicas():
    response = client.get("/musicas")
    assert response.status_code == 200
    musicas = response.json()
    assert isinstance(musicas, list)
    assert len(musicas) > 0
    assert "titulo" in musicas[0]
    assert "artista" in musicas[0]


def test_detalhe_musica():
    response = client.get("/musicas/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id_musica"] == 1
    assert "titulo" in data
    assert "total_reviews" in data


def test_criar_e_listar_avaliacoes():
    payload = {
        "id_musica": 1,
        "nota": 9.0,
        "comentario": "Excelente composição!",
    }
    response = client.post("/avaliacoes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nota"] == 9.0
    assert data["id_musica"] == 1

    resp_list = client.get("/avaliacoes?id_musica=1")
    assert resp_list.status_code == 200
    assert isinstance(resp_list.json(), list)


def test_atualizar_e_deletar_avaliacao():
    payload = {"nota": 8.0, "comentario": "Revisado"}
    response = client.put("/avaliacoes/1", json=payload)
    assert response.status_code == 200
    assert response.json()["id_avaliacao"] == 1

    resp_del = client.delete("/avaliacoes/1")
    assert resp_del.status_code == 204


def test_analytics_endpoints():
    r_comunidade = client.get("/analytics/ranking-comunidade")
    assert r_comunidade.status_code == 200
    assert isinstance(r_comunidade.json(), list)

    r_artistas = client.get("/analytics/ranking-artistas")
    assert r_artistas.status_code == 200
    assert isinstance(r_artistas.json(), list)

    r_audio = client.get("/analytics/correlacao-audio")
    assert r_audio.status_code == 200
    assert isinstance(r_audio.json(), list)

    r_ritmo = client.get("/analytics/ritmo-album")
    assert r_ritmo.status_code == 200
    assert isinstance(r_ritmo.json(), list)

    r_kpi = client.get("/analytics/kpis")
    assert r_kpi.status_code == 200
    assert "total_musicas" in r_kpi.json()
