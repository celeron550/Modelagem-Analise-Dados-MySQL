import os
import httpx
import pandas as pd
import streamlit as st

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="MusicRate — Plataforma de Avaliação e Análise Musical",
    layout="wide",
    page_icon="🎵",
)

st.title("🎵 MusicRate — Plataforma de Avaliação e Análise Musical")

if "token" not in st.session_state:
    st.session_state["token"] = None

if "user" not in st.session_state:
    st.session_state["user"] = None

# Barra lateral: status da conexão e navegação
st.sidebar.header("Navegação do Sistema")
menu = [
    "📈 Análises e Estatísticas",
    "🏆 Ranking (IMDb da Música)",
    "📝 Fazer Avaliação",
    "⚙️ Gerenciar Catálogo (CRUD)",
    "👤 Minha Conta / Autenticação",
]
escolha = st.sidebar.selectbox("Ir para:", menu)

# Indicador do status da API
try:
    health_resp = httpx.get(f"{API_URL}/health", timeout=2.0)
    if health_resp.status_code == 200:
        st.sidebar.success(f"API Online ({health_resp.json().get('milestone', 'ok')})")
    else:
        st.sidebar.warning(f"API retornou status {health_resp.status_code}")
except Exception:
    st.sidebar.error("API Offline — Verifique o serviço backend")


# ============================================================================
# 1. ANÁLISES E ESTATÍSTICAS (Migrado de dashboard.py - Seção 1)
# ============================================================================
if escolha == "📈 Análises e Estatísticas":
    st.subheader("Análise de Dados e Estatísticas Agregadas")

    # KPIs agregados da API
    try:
        resp_kpi = httpx.get(f"{API_URL}/analytics/kpis", timeout=5.0)
        if resp_kpi.status_code == 200:
            k = resp_kpi.json()
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total de Músicas [COUNT]", f"{k.get('total_musicas', 0):,}")
            c2.metric("Pop. Média [AVG]", f"{float(k.get('popularidade_media', 0.0)):.1f}")
            c3.metric("Pop. Máxima [MAX]", int(k.get("popularidade_maxima", 0)))
            c4.metric("Dançabilidade Média", f"{float(k.get('dancabilidade_media', 0.0)):.2f}")
            c5.metric("Energia Média", f"{float(k.get('energia_media', 0.0)):.2f}")
    except Exception as e:
        st.warning(f"Não foi possível carregar os KPIs: {e}")

    st.markdown("---")

    col_esq, col_dir = st.columns(2)

    with col_esq:
        st.markdown("#### 1. Ranking de Artistas por Popularidade Média")
        try:
            resp_art = httpx.get(f"{API_URL}/analytics/ranking-artistas?limit=10", timeout=5.0)
            if resp_art.status_code == 200 and resp_art.json():
                df_art = pd.DataFrame(resp_art.json())
                st.dataframe(df_art, use_container_width=True)
                if "artista" in df_art.columns and "popularidade_media" in df_art.columns:
                    st.bar_chart(df_art.set_index("artista")[["popularidade_media"]])
            else:
                st.info("Nenhum dado de artista disponível.")
        except Exception as e:
            st.error(f"Erro ao buscar ranking de artistas: {e}")

    with col_dir:
        st.markdown("#### 2. Relação entre Energia, Dançabilidade e Sucesso")
        try:
            resp_audio = httpx.get(f"{API_URL}/analytics/correlacao-audio?min_popularity=60", timeout=5.0)
            if resp_audio.status_code == 200 and resp_audio.json():
                df_audio = pd.DataFrame(resp_audio.json())
                st.dataframe(df_audio, use_container_width=True)
                if not df_audio.empty and "musica" in df_audio.columns:
                    st.line_chart(df_audio.set_index("musica")[["danceability", "energy"]])
            else:
                st.info("Nenhuma faixa com popularidade >= 60 encontrada.")
        except Exception as e:
            st.error(f"Erro ao buscar análise acústica: {e}")

    st.markdown("---")
    st.markdown("#### 3. Estatísticas de Ritmo (BPM) por Álbum")
    try:
        resp_ritmo = httpx.get(f"{API_URL}/analytics/ritmo-album", timeout=5.0)
        if resp_ritmo.status_code == 200 and resp_ritmo.json():
            df_ritmo = pd.DataFrame(resp_ritmo.json())
            st.dataframe(df_ritmo, use_container_width=True)
        else:
            st.info("Nenhuma métrica de BPM disponível.")
    except Exception as e:
        st.error(f"Erro ao buscar ritmo dos álbuns: {e}")


# ============================================================================
# 2. RANKING DA COMUNIDADE (IMDb da Música - Migrado de dashboard.py - Seção 2)
# ============================================================================
elif escolha == "🏆 Ranking (IMDb da Música)":
    st.subheader("Top Músicas Avaliadas pela Comunidade")
    try:
        resp = httpx.get(f"{API_URL}/analytics/ranking-comunidade?limit=50", timeout=5.0)
        if resp.status_code == 200:
            ranking_data = resp.json()
            if ranking_data:
                df_rank = pd.DataFrame(ranking_data)
                st.dataframe(df_rank, use_container_width=True)
            else:
                st.info("Ainda não há avaliações suficientes para formar um ranking.")
        else:
            st.error(f"Erro na API: {resp.status_code}")
    except Exception as e:
        st.error(f"Falha de comunicação com o backend: {e}")


# ============================================================================
# 3. FAZER AVALIAÇÃO (Migrado de dashboard.py - Seção 3)
# ============================================================================
elif escolha == "📝 Fazer Avaliação":
    st.subheader("Avaliar uma Faixa Musical")

    # Busca catálogo para dropdown
    musicas_opcoes = {}
    try:
        resp_m = httpx.get(f"{API_URL}/musicas?limit=100", timeout=5.0)
        if resp_m.status_code == 200:
            for item in resp_m.json():
                label = f"{item['id_musica']} - {item['titulo']} ({item['artista']})"
                musicas_opcoes[label] = item["id_musica"]
    except Exception as e:
        st.warning(f"Não foi possível listar as músicas: {e}")

    if musicas_opcoes:
        musica_selecionada = st.selectbox("Selecione a Música", options=list(musicas_opcoes.keys()))
        id_musica = musicas_opcoes[musica_selecionada]

        nota = st.slider("Nota (0.0 a 10.0)", min_value=0.0, max_value=10.0, value=8.5, step=0.5)
        comentario = st.text_area("Comentário sobre a faixa", placeholder="O que você achou dessa música?")

        if st.button("Submeter Avaliação"):
            headers = {}
            if st.session_state["token"]:
                headers["Authorization"] = f"Bearer {st.session_state['token']}"

            payload = {
                "id_musica": id_musica,
                "nota": nota,
                "comentario": comentario,
            }
            try:
                resp_post = httpx.post(f"{API_URL}/avaliacoes", json=payload, headers=headers, timeout=5.0)
                if resp_post.status_code in (200, 201):
                    st.success("Avaliação registrada com sucesso!")
                else:
                    st.error(f"Erro ao registrar avaliação: {resp_post.text}")
            except Exception as e:
                st.error(f"Falha ao enviar avaliação: {e}")
    else:
        st.info("Nenhuma música cadastrada no catálogo.")


# ============================================================================
# 4. GERENCIAR CATÁLOGO (CRUD - Migrado de dashboard.py - Seção 4)
# ============================================================================
elif escolha == "⚙️ Gerenciar Catálogo (CRUD)":
    st.subheader("Gerenciamento do Catálogo Musical")

    acao = st.selectbox("Escolha a ação desejada:", [
        "1. Inserir Nova Música (Create)",
        "2. Consultar Registros (Read)",
        "3. Atualizar Popularidade (Update)",
        "4. Remover Música (Delete)",
    ])

    # --- CREATE ---
    if acao == "1. Inserir Nova Música (Create)":
        st.markdown("#### Cadastrar Nova Faixa")
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título da Faixa")
            artista = st.text_input("Nome do Artista")
            album = st.text_input("Nome do Álbum")
        with col2:
            popularidade = st.slider("Popularidade Inicial (0 a 100)", 0, 100, 50)
            danceability = st.slider("Dançabilidade (0.0 a 1.0)", 0.0, 1.0, 0.5, step=0.05)
            energy = st.slider("Energia (0.0 a 1.0)", 0.0, 1.0, 0.5, step=0.05)
            tempo = st.number_input("BPM (Tempo)", min_value=0.0, value=120.0, step=1.0)

        if st.button("Salvar no Catálogo"):
            if not titulo.strip() or not artista.strip() or not album.strip():
                st.error("Por favor, preencha o título, o artista e o álbum.")
            else:
                payload = {
                    "titulo": titulo.strip(),
                    "artista": artista.strip(),
                    "album": album.strip(),
                    "popularity": popularidade,
                    "danceability": danceability,
                    "energy": energy,
                    "tempo": tempo,
                }
                try:
                    resp_create = httpx.post(f"{API_URL}/musicas", json=payload, timeout=5.0)
                    if resp_create.status_code in (200, 201):
                        st.success(f"Música '{titulo}' cadastrada com sucesso via API!")
                    else:
                        st.error(f"Erro ao cadastrar: {resp_create.text}")
                except Exception as e:
                    st.error(f"Falha de conexão com a API: {e}")


    # --- READ ---
    elif acao == "2. Consultar Registros (Read)":
        st.markdown("#### Consultar Catálogo")

        col1, col2, col3 = st.columns(3)

        with col1:
            termo_busca = st.text_input("Buscar por título:")

        with col2:
            artista_busca = st.text_input("Filtrar por artista:")

        with col3:
            album_busca = st.text_input("Filtrar por álbum:")

        params = {"limit": 100}

        if termo_busca:
            params["termo"] = termo_busca

        if artista_busca:
            params["artista"] = artista_busca

        if album_busca:
            params["album"] = album_busca

        try:
            resp_read = httpx.get(
                f"{API_URL}/musicas",
                params=params,
                timeout=5.0
            )

            if resp_read.status_code == 200:
                df_read = pd.DataFrame(resp_read.json())
                st.dataframe(df_read, use_container_width=True)
            else:
                st.error(f"Erro ao buscar registros: {resp_read.status_code}")

        except Exception as e:
            st.error(f"Falha de conexão com a API: {e}")


    # --- UPDATE ---
    elif acao == "3. Atualizar Popularidade (Update)":
        st.markdown("#### Atualizar Métrica de Popularidade")
        id_alvo = st.number_input("ID da Música", min_value=1, step=1, value=1)
        nova_pop = st.slider("Nova Popularidade", 0, 100, 80)

        if st.button("Atualizar no Banco"):
            try:
                resp_up = httpx.patch(
                    f"{API_URL}/musicas/{id_alvo}/popularidade",
                    json={"popularity": nova_pop},
                    timeout=5.0,
                )
                if resp_up.status_code == 200:
                    st.success(f"Popularidade da música {id_alvo} atualizada para {nova_pop}!")
                else:
                    st.error(f"Erro ao atualizar: {resp_up.text}")
            except Exception as e:
                st.error(f"Falha ao enviar atualização: {e}")

    # --- DELETE ---
    elif acao == "4. Remover Música (Delete)":
        st.markdown("#### Remover Música do Catálogo")
        id_del = st.number_input("ID da Música a Remover", min_value=1, step=1, value=1)
        confirmar = st.checkbox("Confirmo que desejo excluir esta música e suas avaliações")

        if st.button("Confirmar Exclusão"):
            if not confirmar:
                st.error("Marque a caixa de confirmação antes de excluir.")
            else:
                try:
                    resp_del = httpx.delete(f"{API_URL}/musicas/{id_del}", timeout=5.0)
                    if resp_del.status_code in (200, 204):
                        st.success(f"Música {id_del} removida com sucesso!")
                    else:
                        st.error(f"Erro ao excluir música: {resp_del.text}")
                except Exception as e:
                    st.error(f"Falha ao enviar exclusão: {e}")


# ============================================================================
# 5. MINHA CONTA / AUTENTICAÇÃO
# ============================================================================
elif escolha == "👤 Minha Conta / Autenticação":
    st.subheader("Login / Cadastro de Usuário")

    tab_login, tab_register = st.tabs(["Fazer Login", "Criar Nova Conta"])

    with tab_login:
        email = st.text_input("E-mail", value="felix@ufrn.br", key="login_email")
        senha = st.text_input("Senha", type="password", value="SenhaForte123", key="login_pass")
        if st.button("Entrar"):
            try:
                resp_login = httpx.post(
                    f"{API_URL}/auth/login",
                    json={"email": email, "password": senha},
                    timeout=5.0,
                )
                if resp_login.status_code == 200:
                    data = resp_login.json()
                    st.session_state["token"] = data["access_token"]
                    st.session_state["user"] = data["user"]
                    st.success(f"Logado como: {data['user']['username']}")
                else:
                    st.error(f"Falha no login: {resp_login.text}")
            except Exception as e:
                st.error(f"Erro de conexão com o auth: {e}")

    with tab_register:
        reg_username = st.text_input("Username", value="novo_usuario", key="reg_user")
        reg_email = st.text_input("E-mail", value="novo@ufrn.br", key="reg_email")
        reg_senha = st.text_input("Senha", type="password", value="SenhaForte123", key="reg_pass")
        if st.button("Registrar"):
            try:
                resp_reg = httpx.post(
                    f"{API_URL}/auth/register",
                    json={"username": reg_username, "email": reg_email, "password": reg_senha},
                    timeout=5.0,
                )
                if resp_reg.status_code in (200, 201):
                    st.success(f"Usuário {reg_username} registrado com sucesso! Agora faça login.")
                else:
                    st.error(f"Falha no registro: {resp_reg.text}")
            except Exception as e:
                st.error(f"Erro de conexão com o auth: {e}")

    if st.session_state["user"]:
        st.markdown("---")
        st.info(f"Sessão ativa: **{st.session_state['user']['username']}** ({st.session_state['user']['email']})")
        if st.button("Sair da Conta"):
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()
