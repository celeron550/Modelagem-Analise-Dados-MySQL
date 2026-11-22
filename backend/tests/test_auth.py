import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_fluxo_completo_cadastro_login_e_me():
    sufixo = uuid.uuid4().hex[:8]
    email = f"dev_{sufixo}@ufrn.br"
    username = f"dev_{sufixo}"
    password = "SenhaSegura123"

    # 1. Cadastro válido -> 201
    res_reg = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert res_reg.status_code == 201
    dados_reg = res_reg.json()
    assert dados_reg["email"] == email
    assert dados_reg["role"] == "USER"
    assert "senha_hash" not in dados_reg

    # 2. Cadastro duplicado -> 409
    res_dup = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert res_dup.status_code == 409

    # 3. Login com senha errada -> 401
    res_bad = client.post(
        "/auth/login",
        json={"email": email, "password": "SenhaErrada999"},
    )
    assert res_bad.status_code == 401

    # 4. Login válido -> 200 + JWT
    res_login = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 5. Rota protegida /auth/me com token -> 200
    res_me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["username"] == username


def test_rota_protegida_sem_token_retorna_401():
    res = client.get("/auth/me")
    assert res.status_code == 401