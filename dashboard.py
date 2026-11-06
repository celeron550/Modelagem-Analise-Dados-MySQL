import streamlit as st
import mysql.connector
import pandas as pd

# Função para conectar ao banco de dados certo (App ou Análise)
# Nota: Para o futuro, em vez de 'root' e '123456' aqui, usaríamos st.secrets, 
# mas para o trabalho da faculdade funcionar direto na máquina de quem avaliar, vamos manter assim.
def get_conexao(banco):
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database=banco
    )

st.set_page_config(layout="wide", page_title="Spotify DB - Eng. Software")
st.title("🎵 Dashboard Completo - Spotify DB")

menu = [
    "📈 Análises e Estatísticas", 
    "🏆 Ranking (IMDb da Música)",
    "📝 Fazer Avaliação", 
    "⚙️ Gerenciar Catálogo (CRUD)",
    "🗃️ Visão Geral (Tabelas)"
]
escolha = st.sidebar.selectbox("Navegação do Sistema", menu)

# ==========================================
# 1. ANÁLISES E ESTATÍSTICAS (Exigência do Professor)
# ==========================================
if escolha == "📈 Análises e Estatísticas":
    st.subheader("Análise de Dados (Schema: musica_analise)")
    conn = get_conexao("musica_analise")
    
    st.markdown("#### 1. Músicas Explícitas têm popularidade diferente?")
    df_explicit = pd.read_sql("""
        SELECT 
            IF(explicit = 1, 'Sim', 'Não') as 'Explícita', 
            COUNT(*) as 'Total de Músicas', 
            ROUND(AVG(track_popularity), 1) as 'Popularidade Média',
            MAX(track_popularity) as 'Pop. Máxima', 
            MIN(track_popularity) as 'Pop. Mínima'
        FROM dataset_bruto
        GROUP BY explicit;
    """, conn)
    st.dataframe(df_explicit, use_container_width=True)
    
    st.markdown("#### 2. Músicas 'Invisíveis' (Popularidade Zero)")
    df_zero = pd.read_sql("""
        SELECT 
            COUNT(*) as 'Músicas com Pop Zero',
            ROUND((COUNT(*) / (SELECT COUNT(*) FROM dataset_bruto)) * 100, 2) as 'Percentagem do Catálogo (%)'
        FROM dataset_bruto
        WHERE track_popularity = 0;
    """, conn)
    st.dataframe(df_zero, use_container_width=True)

    st.markdown("#### 3. Relação entre Energia, Dançabilidade e Popularidade")
    df_energia = pd.read_sql("""
        SELECT 
            CASE 
                WHEN energy > 0.8 THEN 'Alta Energia'
                WHEN energy > 0.5 THEN 'Média Energia'
                ELSE 'Baixa Energia'
            END AS categoria_energia,
            ROUND(AVG(danceability), 2) as 'Dançabilidade Média',
            ROUND(AVG(track_popularity), 2) as 'Popularidade Média',
            COUNT(*) as 'Quantidade'
        FROM dataset_bruto
        GROUP BY categoria_energia
        ORDER BY 'Popularidade Média' DESC;
    """, conn)
    st.dataframe(df_energia, use_container_width=True)
    conn.close()

# ==========================================
# 2. RANKING (O "IMDb da Música")
# ==========================================
elif escolha == "🏆 Ranking (IMDb da Música)":
    st.subheader("Top Músicas Avaliadas pela Comunidade")
    conn = get_conexao("musica_app")
    
    # Usando a VIEW que criamos no schema.sql
    df_ranking = pd.read_sql("SELECT * FROM vw_ranking_musicas ORDER BY nota_media DESC, n_avaliacoes DESC LIMIT 50;", conn)
    
    if not df_ranking.empty and df_ranking['nota_media'].max() > 0:
        st.dataframe(df_ranking, use_container_width=True)
    else:
        st.info("Ainda não há avaliações suficientes para formar um ranking.")
    conn.close()

# ==========================================
# 3. FAZER AVALIAÇÃO (Regra UNIQUE e Tabela Usuário)
# ==========================================
elif escolha == "📝 Fazer Avaliação":
    st.subheader("Avaliar uma Faixa")
    conn = get_conexao("musica_app")
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id_musica, track_name FROM musica ORDER BY track_name ASC LIMIT 1000;")
    musicas_db = cursor.fetchall()
    
    if musicas_db:
        opcoes = {f"{m['id_musica']} - {m['track_name']}": m['id_musica'] for m in musicas_db}
        musica_selecionada = st.selectbox("Selecione a Música", options=list(opcoes.keys()))
        id_musica = opcoes[musica_selecionada]
        
        username = st.text_input("Seu Nome de Usuário (Username)")
        nota = st.slider("Nota", 1, 5, 3)
        comentario = st.text_area("Comentário")
        
        if st.button("Submeter Avaliação"):
            if username.strip() == "":
                st.error("Por favor, digite um nome de usuário.")
            else:
                try:
                    # Verifica se o usuário existe, se não, cria na hora
                    cursor.execute("SELECT id_usuario FROM usuario WHERE username = %s", (username,))
                    user = cursor.fetchone()
                    
                    if user:
                        id_user = user['id_usuario']
                    else:
                        cursor.execute("INSERT INTO usuario (username) VALUES (%s)", (username,))
                        id_user = cursor.lastrowid
                    
                    # Insere avaliação
                    cursor.execute(
                        "INSERT INTO avaliacao_musica (id_usuario, id_musica, nota, comentario) VALUES (%s, %s, %s, %s)", 
                        (id_user, id_musica, nota, comentario)
                    )
                    conn.commit()
                    st.success("Avaliação registrada com sucesso!")
                
                except mysql.connector.IntegrityError:
                    st.error("Erro: Você já avaliou esta música! (Bloqueio do Banco de Dados)")
                except Exception as e:
                    st.error(f"Erro inesperado: {e}")
    else:
        st.warning("Nenhuma música cadastrada.")
    conn.close()

# ==========================================
# 4. GERENCIAR CATÁLOGO (CRUD Atualizado)
# ==========================================
elif escolha == "⚙️ Gerenciar Catálogo (CRUD)":
    st.subheader("Inserir, Atualizar ou Remover Músicas")
    conn = get_conexao("musica_app")
    cursor = conn.cursor()
    
    acao = st.selectbox("Escolha a ação", ["Inserir Nova Música", "Atualizar Popularidade", "Remover Música"])
    
    if acao == "Inserir Nova Música":
        nome = st.text_input("Nome da Faixa")
        duracao = st.number_input("Duração (ms)", min_value=0, step=1000, value=200000)
        id_al = st.number_input("ID do Álbum", min_value=1, step=1)
        explicit = st.checkbox("É uma música com conteúdo explícito?")
        popularidade = st.slider("Popularidade Inicial", 0, 100, 0)
        
        if st.button("Inserir Registro"):
            cursor.execute(
                "INSERT INTO musica (id_album, track_name, duration_ms, explicit, track_popularity) VALUES (%s, %s, %s, %s, %s)", 
                (id_al, nome, duracao, explicit, popularidade)
            )
            conn.commit()
            st.success("Música inserida com sucesso!")
            
    elif acao == "Atualizar Popularidade":
        id_mus = st.number_input("ID da Música Alvo", min_value=1, step=1)
        nova_pop = st.number_input("Nova Popularidade (0 a 100)", min_value=0, max_value=100, step=1)
        if st.button("Atualizar Métrica"):
            cursor.execute("UPDATE musica SET track_popularity = %s WHERE id_musica = %s", (nova_pop, id_mus))
            conn.commit()
            st.success("Popularidade atualizada com sucesso!")
            
    elif acao == "Remover Música":
        id_del = st.number_input("ID da Música para Exclusão", min_value=1, step=1)
        st.warning("⚠️ Atenção: A exclusão não pode ser desfeita e apagará também as avaliações desta música!")
        if st.button("Confirmar Exclusão"):
            cursor.execute("DELETE FROM musica WHERE id_musica = %s", (id_del,))
            conn.commit()
            st.success("Música removida do banco de dados.")
    conn.close()

# ==========================================
# 5. VISÃO GERAL (Tabelas)
# ==========================================
elif escolha == "🗃️ Visão Geral (Tabelas)":
    st.subheader("Explorar as Tabelas Normalizadas (Schema: musica_app)")
    conn = get_conexao("musica_app")
    tabela = st.radio("Selecione qual tabela deseja visualizar:", ["artista", "album", "musica", "usuario", "avaliacao_musica", "genero"])
    
    df = pd.read_sql(f"SELECT * FROM {tabela} LIMIT 100;", conn)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info(f"A tabela {tabela} está vazia no momento.")
    conn.close()