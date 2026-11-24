import uuid
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
    sufixo = uuid.uuid4().hex[:8]
    payload = {
        "username": f"tester_{sufixo}",
        "email": f"tester_{sufixo}@ufrn.br",
        "password": "SenhaForte123",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == f"tester_{sufixo}"
    assert data["email"] == f"tester_{sufixo}@ufrn.br"
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
    sufixo = uuid.uuid4().hex[:8]
    res_musica = client.post(
        "/musicas",
        json={
            "titulo": f"Musica API {sufixo}",
            "artista": f"Artista API {sufixo}",
            "album": f"Album API {sufixo}",
            "popularity": 75,
        },
    )
    assert res_musica.status_code == 201
    id_musica = res_musica.json()["id_musica"]

    payload = {
        "id_musica": id_musica,
        "nota": 9.0,
        "comentario": "Excelente composição!",
    }
    response = client.post("/avaliacoes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nota"] == 9.0

    res_list = client.get(f"/avaliacoes?id_musica={id_musica}")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1


def test_atualizar_e_deletar_avaliacao():
    sufixo = uuid.uuid4().hex[:8]
    res_musica = client.post(
        "/musicas",
        json={
            "titulo": f"Musica Del {sufixo}",
            "artista": f"Artista Del {sufixo}",
            "album": f"Album Del {sufixo}",
            "popularity": 70,
        },
    )
    assert res_musica.status_code == 201
    id_musica = res_musica.json()["id_musica"]

    res_create = client.post(
        "/avaliacoes",
        json={"id_musica": id_musica, "nota": 7.5, "comentario": "Inicial"},
    )
    assert res_create.status_code == 201
    id_avaliacao = res_create.json()["id_avaliacao"]

    payload = {"nota": 8.0, "comentario": "Revisado"}
    response = client.put(f"/avaliacoes/{id_avaliacao}", json=payload)
    assert response.status_code == 200
    assert response.json()["id_avaliacao"] == id_avaliacao
    assert response.json()["nota"] == 8.0

    resp_del = client.delete(f"/avaliacoes/{id_avaliacao}")
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