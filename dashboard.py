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
    
    # 1ª MUDANÇA: Consulta SQL com JOIN para buscar o nome do artista
    cursor.execute("""
        SELECT m.id_musica, m.track_name, ar.artist_name 
        FROM musica m
        JOIN album al ON m.id_album = al.id_album
        JOIN artista ar ON ar.id_artista = al.id_artista
        ORDER BY m.track_name ASC 
        LIMIT 1000;
    """)
    musicas_db = cursor.fetchall()
    
    if musicas_db:
        # 2ª MUDANÇA: Adiciona o nome do artista formatado entre parênteses
        opcoes = {f"{m['id_musica']} - {m['track_name']} ({m['artist_name']})": m['id_musica'] for m in musicas_db}
        
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
        nome_artista = st.text_input("Nome do Artista")
        nome_album = st.text_input("Nome do Álbum")
        
        # Criando colunas para organizar o formulário na tela
        col1, col2 = st.columns(2)
        with col1:
            duracao = st.number_input("Duração (ms)", min_value=0, step=1000, value=200000)
            ano_album = st.number_input("Ano de Lançamento (se for um novo álbum)", min_value=1900, max_value=2026, step=1, value=2024)
        with col2:
            popularidade = st.slider("Popularidade Inicial", 0, 100, 0)
            explicit = st.checkbox("É uma música com conteúdo explícito?")
            
        if st.button("Inserir Registro"):
            if not nome or not nome_artista or not nome_album:
                st.error("Por favor, preencha o nome da música, do artista e do álbum.")
            else:
                try:
                    # PASSO 1: Lidar com o Artista
                    cursor.execute("SELECT id_artista FROM artista WHERE artist_name = %s", (nome_artista,))
                    resultado_artista = cursor.fetchone()
                    
                    if resultado_artista:
                        id_art = resultado_artista[0] # Pega o ID existente
                    else:
                        cursor.execute("INSERT INTO artista (artist_name) VALUES (%s)", (nome_artista,))
                        id_art = cursor.lastrowid # Pega o novo ID gerado
                        
                    # PASSO 2: Lidar com o Álbum (amarrado ao ID do artista)
                    cursor.execute("SELECT id_album FROM album WHERE album_name = %s AND id_artista = %s", (nome_album, id_art))
                    resultado_album = cursor.fetchone()
                    
                    if resultado_album:
                        id_al = resultado_album[0]
                    else:
                        cursor.execute("INSERT INTO album (id_artista, album_name, release_year) VALUES (%s, %s, %s)", (id_art, nome_album, ano_album))
                        id_al = cursor.lastrowid
                        
                    # PASSO 3: Inserir a Música (amarrada ao ID do álbum)
                    cursor.execute(
                        "INSERT INTO musica (id_album, track_name, duration_ms, explicit, track_popularity) VALUES (%s, %s, %s, %s, %s)", 
                        (id_al, nome, duracao, explicit, popularidade)
                    )
                    
                    # Salva TUDO no banco de dados
                    conn.commit()
                    st.success(f"Sucesso! A música '{nome}' (Álbum: {nome_album}, Artista: {nome_artista}) foi cadastrada perfeitamente!")
                    
                except Exception as e:
                    st.error(f"Erro ao inserir no banco: {e}")
            
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