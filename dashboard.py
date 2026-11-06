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
    tabela = st.radio(
        "Selecione qual tabela deseja visualizar:",
        ["Artista", "Album", "Musica", "Avaliacao_Musica"],
    )
    
    if tabela == "Avaliacao_Musica":
        # Traz os dados da avaliação + o nome da música correspondente
        query = """
            SELECT a.id_avaliacao, a.id_usuario, u.username AS 'usuario_nome',
                   a.id_musica, m.track_name AS 'nome_da_musica',
                   a.nota, a.comentario, a.data_avaliacao
            FROM avaliacao_musica a
            JOIN usuario u ON a.id_usuario = u.id_usuario
            LEFT JOIN musica m ON a.id_musica = m.id_musica
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
        cursor.execute(
            "SELECT id_album, album_name FROM Album ORDER BY album_name, id_album;"
        )
        albuns_db = cursor.fetchall()
        if albuns_db:
            opcoes_albuns = {
                f"{album['id_album']} - {album['album_name']}": album["id_album"]
                for album in albuns_db
            }
            album_selecionado = st.selectbox(
                "Álbum", options=list(opcoes_albuns.keys())
            )
            if st.button("Inserir Registro"):
                if not nome.strip():
                    st.error("Informe o nome da faixa.")
                else:
                    cursor.execute(
                        "INSERT INTO Musica (track_name, duration_ms, id_album) "
                        "VALUES (%s, %s, %s)",
                        (nome.strip(), duracao, opcoes_albuns[album_selecionado]),
                    )
                    conn.commit()
                    st.success("Música inserida com sucesso!")
        else:
            st.warning("Cadastre um álbum antes de inserir uma música.")
            
    elif acao == "Atualizar Popularidade":
        cursor.execute(
            "SELECT id_musica, track_name FROM Musica ORDER BY track_name, id_musica;"
        )
        musicas_db = cursor.fetchall()
        if musicas_db:
            opcoes_musicas = {
                f"{musica['id_musica']} - {musica['track_name']}": musica["id_musica"]
                for musica in musicas_db
            }
            musica_selecionada = st.selectbox(
                "Música", options=list(opcoes_musicas.keys())
            )
            nova_pop = st.number_input(
                "Nova Popularidade (0 a 100)", min_value=0, max_value=100, step=1
            )
            if st.button("Atualizar Métrica"):
                cursor.execute(
                    "UPDATE Musica SET track_popularity = %s WHERE id_musica = %s",
                    (nova_pop, opcoes_musicas[musica_selecionada]),
                )
                conn.commit()
                st.success("Popularidade atualizada com sucesso!")
        else:
            st.warning("Não existem músicas cadastradas para atualizar.")
            
    elif acao == "Remover Música":
        cursor.execute(
            "SELECT id_musica, track_name FROM Musica ORDER BY track_name, id_musica;"
        )
        musicas_db = cursor.fetchall()
        if musicas_db:
            opcoes_musicas = {
                f"{musica['id_musica']} - {musica['track_name']}": musica["id_musica"]
                for musica in musicas_db
            }
            musica_selecionada = st.selectbox(
                "Música para exclusão", options=list(opcoes_musicas.keys())
            )
            if st.button("Deletar do Banco"):
                cursor.execute(
                    "DELETE FROM Musica WHERE id_musica = %s",
                    (opcoes_musicas[musica_selecionada],),
                )
                conn.commit()
                st.warning(
                    "Música removida do banco de dados (e as avaliações dela também!)."
                )
        else:
            st.warning("Não existem músicas cadastradas para remover.")

# ==========================================
# 4. VISUALIZAR AVALIAÇÕES
# ==========================================
elif escolha == "Visualizar Avaliações":
    st.subheader("Comentários da Comunidade")
    cursor.execute("""
        SELECT m.track_name AS 'Música', u.username AS 'Usuário',
               a.nota AS 'Nota', a.comentario AS 'Comentário',
               a.data_avaliacao AS 'Data'
        FROM avaliacao_musica a
        JOIN musica m ON m.id_musica = a.id_musica
        JOIN usuario u ON u.id_usuario = a.id_usuario;
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
        
        cursor.execute("SELECT id_usuario, username FROM usuario ORDER BY username;")
        usuarios_db = cursor.fetchall()
        cadastrar_usuario = st.radio(
            "Usuário",
            ["Selecionar usuário cadastrado", "Cadastrar novo usuário"],
            index=0 if usuarios_db else 1,
        )
        if cadastrar_usuario == "Selecionar usuário cadastrado" and usuarios_db:
            opcoes_usuarios = {
                f"{usuario['username']} (ID {usuario['id_usuario']})": usuario[
                    "id_usuario"
                ]
                for usuario in usuarios_db
            }
            usuario_selecionado = st.selectbox(
                "Selecione o usuário", options=list(opcoes_usuarios.keys())
            )
            id_usuario = opcoes_usuarios[usuario_selecionado]
        else:
            if cadastrar_usuario == "Selecionar usuário cadastrado":
                st.warning("Não há usuários cadastrados. Selecione o cadastro de novo usuário.")
            username = st.text_input("Nome de usuário")
            email = st.text_input("E-mail")
            id_usuario = None

        nota = st.slider("Nota", 0, 10, 5)
        comentario = st.text_area("Comentário")
        
        if st.button("Submeter Avaliação"):
            if id_usuario is None:
                if not username.strip() or not email.strip():
                    st.error("Informe o nome de usuário e o e-mail.")
                else:
                    cursor.execute(
                        "SELECT id_usuario FROM usuario "
                        "WHERE username = %s OR email = %s LIMIT 1",
                        (username.strip(), email.strip()),
                    )
                    if cursor.fetchone():
                        st.error(
                            "Esse nome de usuário ou e-mail já está cadastrado. "
                            "Selecione o usuário existente."
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO usuario (username, email) VALUES (%s, %s)",
                            (username.strip(), email.strip()),
                        )
                        id_usuario = cursor.lastrowid

            if id_usuario is not None:
                cursor.execute(
                    "SELECT id_avaliacao FROM avaliacao_musica "
                    "WHERE id_usuario = %s AND id_musica = %s LIMIT 1",
                    (id_usuario, id_musica),
                )
                if cursor.fetchone():
                    st.error("Esse usuário já avaliou esta música.")
                else:
                    cursor.execute(
                        "INSERT INTO avaliacao_musica "
                        "(id_usuario, id_musica, nota, comentario) "
                        "VALUES (%s, %s, %s, %s)",
                        (id_usuario, id_musica, nota, comentario),
                    )
                    conn.commit()
                    st.success("Avaliação registrada com sucesso!")
    else:
        st.warning("Nenhuma música cadastrada no banco de dados no momento.")