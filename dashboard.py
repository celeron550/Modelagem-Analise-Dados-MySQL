import streamlit as st
import mysql.connector
import pandas as pd

# Ligação ao banco de dados MySQL local
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456",
    database="engenharia_musica"
)
cursor = conn.cursor(dictionary=True)

st.set_page_config(layout="wide")
st.title("Dashboard")

menu = [
    "Visão Geral (Ver o Banco de Dados)", 
    "Estatísticas de Artistas", 
    "Gerenciar Músicas (CRUD)",
    "Visualizar Avaliações", 
    "Nova Avaliação"
]
escolha = st.sidebar.selectbox("Navegação do Sistema", menu)

# ==========================================
# 1. VISÃO GERAL (ATUALIZADA COM OS NOMES)
# ==========================================
if escolha == "Visão Geral (Ver o Banco de Dados)":
    st.subheader("Explorar as Tabelas do Banco de Dados")
    tabela = st.radio("Selecione qual tabela deseja visualizar:", ["Artista", "Album", "Musica", "Avaliacao"])
    
    if tabela == "Avaliacao":
        # Traz os dados da avaliação + o nome da música correspondente
        query = """
            SELECT a.id_avaliacao, a.id_musica, m.track_name as 'nome_da_musica', 
                   a.usuario_nome, a.nota, a.comentario, a.data_avaliacao
            FROM Avaliacao a
            LEFT JOIN Musica m ON a.id_musica = m.id_musica
            LIMIT 100;
        """
    elif tabela == "Musica":
        # Traz os dados da música + o nome do álbum correspondente
        query = """
            SELECT m.id_musica, m.track_name, m.id_album, al.album_name as 'nome_do_album',
                   m.duration_ms, m.explicit, m.track_popularity
            FROM Musica m
            LEFT JOIN Album al ON m.id_album = al.id_album
            LIMIT 100;
        """
    elif tabela == "Album":
        # Traz os dados do álbum + o nome do artista correspondente
        query = """
            SELECT al.id_album, al.album_name, al.release_date, al.id_artista, art.artist_name as 'nome_do_artista'
            FROM Album al
            LEFT JOIN Artista art ON al.id_artista = art.id_artista
            LIMIT 100;
        """
    else:
        # A tabela Artista não tem chaves estrangeiras, então mostra os dados normais
        query = f"SELECT * FROM {tabela} LIMIT 100;"
        
    cursor.execute(query)
    dados = cursor.fetchall()
    
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True)
        st.caption(f"Exibindo os registros combinados da tabela: {tabela}")
    else:
        st.warning(f"A tabela {tabela} está vazia no momento.")

# ==========================================
# 2. ESTATÍSTICAS
# ==========================================
elif escolha == "Estatísticas de Artistas":
    st.subheader("Top 10 Artistas por Popularidade Média")
    cursor.execute("""
        SELECT a.artist_name, AVG(m.track_popularity) as media_pop 
        FROM Musica m
        JOIN Album al ON m.id_album = al.id_album
        JOIN Artista a ON al.id_artista = a.id_artista
        GROUP BY a.artist_name
        ORDER BY media_pop DESC LIMIT 10;
    """)
    dados = cursor.fetchall()
    if dados:
        df = pd.DataFrame(dados)
        st.bar_chart(df.set_index('artist_name'))

# ==========================================
# 3. CRUD DE MÚSICAS
# ==========================================
elif escolha == "Gerenciar Músicas (CRUD)":
    st.subheader("Inserir, Atualizar ou Remover Músicas")
    acao = st.selectbox("Escolha a ação", ["Inserir Nova Música", "Atualizar Popularidade", "Remover Música"])
    
    if acao == "Inserir Nova Música":
        nome = st.text_input("Nome da Faixa")
        duracao = st.number_input("Duração (ms)", min_value=0, step=1000)
        id_al = st.number_input("ID do Álbum", min_value=1, step=1)
        if st.button("Inserir Registro"):
            cursor.execute("INSERT INTO Musica (track_name, duration_ms, id_album) VALUES (%s, %s, %s)", (nome, duracao, id_al))
            conn.commit()
            st.success("Música inserida com sucesso!")
            
    elif acao == "Atualizar Popularidade":
        id_mus = st.number_input("ID da Música Alvo", min_value=1, step=1)
        nova_pop = st.number_input("Nova Popularidade (0 a 100)", min_value=0, max_value=100, step=1)
        if st.button("Atualizar Métrica"):
            cursor.execute("UPDATE Musica SET track_popularity = %s WHERE id_musica = %s", (nova_pop, id_mus))
            conn.commit()
            st.success("Popularidade atualizada com sucesso!")
            
    elif acao == "Remover Música":
        id_del = st.number_input("ID da Música para Exclusão", min_value=1, step=1)
        if st.button("Deletar do Banco"):
            cursor.execute("DELETE FROM Musica WHERE id_musica = %s", (id_del,))
            conn.commit()
            st.warning("Música removida do banco de dados (e as avaliações dela também!).")

# ==========================================
# 4. VISUALIZAR AVALIAÇÕES
# ==========================================
elif escolha == "Visualizar Avaliações":
    st.subheader("Comentários da Comunidade")
    cursor.execute("""
        SELECT m.track_name as 'Música', a.usuario_nome as 'Usuário', 
               a.nota as 'Nota', a.comentario as 'Comentário', a.data_avaliacao as 'Data'
        FROM Musica m
        JOIN Avaliacao a ON m.id_musica = a.id_musica;
    """)
    dados = cursor.fetchall()
    
    if dados:
        st.dataframe(pd.DataFrame(dados), use_container_width=True)
    else:
        st.info("Ainda não existem avaliações.")

# ==========================================
# 5. NOVA AVALIAÇÃO
# ==========================================
elif escolha == "Nova Avaliação":
    st.subheader("Avaliar uma Faixa")
    
    cursor.execute("SELECT id_musica, track_name FROM Musica ORDER BY track_name ASC;")
    musicas_db = cursor.fetchall()
    
    if musicas_db:
        opcoes = {f"{m['id_musica']} - {m['track_name']}": m['id_musica'] for m in musicas_db}
        
        musica_selecionada = st.selectbox("Selecione a Música", options=list(opcoes.keys()))
        id_musica = opcoes[musica_selecionada]
        
        nome = st.text_input("Seu Nome")
        nota = st.slider("Nota", 1, 5, 3)
        comentario = st.text_area("Comentário")
        
        if st.button("Submeter Avaliação"):
            cursor.execute(
                "INSERT INTO Avaliacao (id_musica, usuario_nome, nota, comentario) VALUES (%s, %s, %s, %s)", 
                (id_musica, nome, nota, comentario)
            )
            conn.commit()
            st.success("Avaliação registrada com sucesso!")
    else:
        st.warning("Nenhuma música cadastrada no banco de dados no momento.")