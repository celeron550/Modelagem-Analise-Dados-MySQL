import streamlit as st
import mysql.connector
import pandas as pd
import warnings

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy") # remover o aviso chato

# Função para conectar ao banco de dados certo
def get_conexao(banco):
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database=banco
    )


def view_existe(conn, nome):
    """True se a view existe no schema atual (evita erro 1146 se o dump estiver incompleto)."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM information_schema.views "
                "WHERE table_schema = DATABASE() AND table_name = %s", (nome,))
    ok = cur.fetchone()[0] > 0
    cur.close()
    return ok


def buscar_musicas(cursor, termo=""):
    """Lista até 50 músicas (as mais recentes primeiro), filtrando por faixa ou artista."""
    cursor.execute("""
        SELECT m.id_musica, m.track_name, ar.artist_name, m.track_popularity
        FROM musica m
        JOIN album al   ON al.id_album   = m.id_album
        JOIN artista ar ON ar.id_artista = al.id_artista
        WHERE m.track_name LIKE %s OR ar.artist_name LIKE %s
        ORDER BY m.id_musica DESC
        LIMIT 50;
    """, (f"%{termo}%", f"%{termo}%"))
    return cursor.fetchall()


def rotulo_musica(m):
    # m = (id_musica, track_name, artist_name, track_popularity)
    return f"{m[0]} - {m[1]} ({m[2]}) | popularidade atual: {m[3]}"

st.set_page_config(layout="wide", page_title="Spotify DB - Banco de Dados")
st.title("🎵 Dashboard Completo - Spotify DB")

menu = [
    "📈 Análises e Estatísticas", 
    "🏆 Ranking (IMDb da Música)",
    "📝 Fazer Avaliação", 
    "⚙️ Gerenciar Catálogo (CRUD)",
    "🔎 Views do Banco",
    "🗃️ Visão Geral (Tabelas)"
]
escolha = st.sidebar.selectbox("Navegação do Sistema", menu)

# ==========================================
# 1. ANÁLISES E ESTATÍSTICAS (Com SUM, AVG, MAX, MIN e Filtros)
# ==========================================
if escolha == "📈 Análises e Estatísticas":
    st.subheader("Análise de Dados e Estatísticas Agregadas")
    
    conn_app = get_conexao("musica_app")
    st.markdown("#### 🔍 Estatísticas por Gênero (View: `vw_estatisticas_genero`)")

    if view_existe(conn_app, "vw_estatisticas_genero"):
        # Filtro dinâmico por gênero musical
        df_generos_list = pd.read_sql("SELECT nome_genero FROM genero ORDER BY nome_genero;", conn_app)
        lista_generos = ["Todos"] + df_generos_list["nome_genero"].tolist()
        genero_selecionado = st.selectbox("Filtrar estatísticas por gênero musical:", lista_generos)

        if genero_selecionado == "Todos":
            # Visão do catálogo inteiro (cada música conta uma única vez)
            df_kpi = pd.read_sql("""
                SELECT COUNT(*) AS total_musicas,
                       ROUND(SUM(duration_ms) / 60000.0, 1) AS duracao_total_minutos,
                       ROUND(AVG(track_popularity), 1) AS popularidade_media,
                       MAX(track_popularity) AS popularidade_maxima,
                       MIN(track_popularity) AS popularidade_minima
                FROM musica;
            """, conn_app)
            df_vw_gen = pd.read_sql(
                "SELECT * FROM vw_estatisticas_genero ORDER BY total_musicas DESC;", conn_app
            )
        else:
            df_vw_gen = pd.read_sql(
                "SELECT * FROM vw_estatisticas_genero WHERE nome_genero = %s;",
                conn_app, params=(genero_selecionado,)
            )
            df_kpi = df_vw_gen

        if not df_kpi.empty:
            k = df_kpi.iloc[0]
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total de músicas [COUNT]", f"{int(k['total_musicas']):,}")
            col2.metric("Duração total (min) [SUM]", f"{float(k['duracao_total_minutos']):,.1f}")
            col3.metric("Pop. média [AVG]", f"{float(k['popularidade_media']):.1f}")
            col4.metric("Pop. máxima [MAX]", int(k["popularidade_maxima"]))
            col5.metric("Pop. mínima [MIN]", int(k["popularidade_minima"]))

        st.dataframe(df_vw_gen, width="stretch")
        if genero_selecionado == "Todos" and not df_vw_gen.empty:
            st.markdown("**Gêneros com mais músicas no catálogo (top 15)**")
            top = df_vw_gen.head(15).set_index("nome_genero")[["total_musicas"]].astype(float)
            st.bar_chart(top)
    else:
        st.warning("A view `vw_estatisticas_genero` não existe neste banco. Execute o script `generos_e_views.sql` (ou restaure o dump final) para ver esta análise.")
    conn_app.close()

    st.markdown("---")
    
    st.subheader("Análise do Catálogo Bruto (Schema: musica_analise)")
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
    st.dataframe(df_explicit, width="stretch")
    
    st.markdown("#### 2. Músicas 'Invisíveis' (Popularidade Zero)")
    df_zero = pd.read_sql("""
        SELECT 
            COUNT(*) as 'Músicas com Pop Zero',
            ROUND((COUNT(*) / (SELECT COUNT(*) FROM dataset_bruto)) * 100, 2) as 'Percentagem do Catálogo (%)'
        FROM dataset_bruto
        WHERE track_popularity = 0;
    """, conn)
    st.dataframe(df_zero, width="stretch")

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
        ORDER BY AVG(track_popularity) DESC;
    """, conn)
    st.dataframe(df_energia, width="stretch")

    st.markdown("#### 4. Evolução da Popularidade e das Características Musicais por Ano")
    df_anos = pd.read_sql("""
        SELECT
            CAST(LEFT(release_date, 4) AS UNSIGNED) AS ano,
            COUNT(*) AS quantidade_musicas,
            ROUND(AVG(track_popularity), 2) AS popularidade_media,
            ROUND(AVG(energy), 3) AS energia_media,
            ROUND(AVG(danceability), 3) AS dancabilidade_media
        FROM dataset_bruto
        WHERE release_date REGEXP '^[0-9]{4}'
        GROUP BY CAST(LEFT(release_date, 4) AS UNSIGNED)
        HAVING COUNT(*) >= 5
        ORDER BY ano;
    """, conn)

    st.markdown("**Dados agrupados por ano de lançamento**")
    st.dataframe(df_anos, width="stretch")

    st.markdown("**Evolução da popularidade média**")
    st.line_chart(df_anos.set_index("ano")[["popularidade_media"]])

    st.markdown("**Evolução das características sonoras**")
    st.line_chart(df_anos.set_index("ano")[["energia_media", "dancabilidade_media"]])

    st.markdown("**Quantidade de músicas por ano**")
    st.bar_chart(df_anos.set_index("ano")[["quantidade_musicas"]])

    st.markdown("#### 5. Artistas mais seguidos e desempenho das faixas (MAX, COUNT, AVG, SUM)")
    df_top_art = pd.read_sql("""
        SELECT artist_name AS artista,
               MAX(followers) AS seguidores,
               MAX(artist_popularity) AS popularidade_artista,
               COUNT(*) AS n_faixas,
               ROUND(AVG(track_popularity), 1) AS popularidade_media_faixas,
               ROUND(SUM(duration_ms) / 60000, 1) AS total_minutos
        FROM dataset_bruto
        GROUP BY artist_name
        ORDER BY seguidores DESC
        LIMIT 10;
    """, conn)
    st.dataframe(df_top_art, width="stretch")

    st.markdown("#### 6. A duração da música influencia a popularidade?")
    df_dur = pd.read_sql("""
        SELECT CASE WHEN duration_ms < 180000 THEN '1) Curta (até 3 min)'
                    WHEN duration_ms < 240000 THEN '2) Média (3 a 4 min)'
                    ELSE '3) Longa (mais de 4 min)' END AS faixa_duracao,
               COUNT(*) AS quantidade,
               ROUND(AVG(track_popularity), 1) AS popularidade_media,
               MIN(track_popularity) AS popularidade_minima,
               MAX(track_popularity) AS popularidade_maxima
        FROM dataset_bruto
        GROUP BY faixa_duracao
        ORDER BY faixa_duracao;
    """, conn)
    st.dataframe(df_dur, width="stretch")
    st.bar_chart(df_dur.set_index("faixa_duracao")[["popularidade_media"]].astype(float))

    st.markdown("#### 7. Artistas com mais seguidores têm faixas mais populares?")
    df_seg = pd.read_sql("""
        SELECT CASE WHEN followers < 10000000 THEN '1) Até 10 milhões'
                    WHEN followers < 50000000 THEN '2) 10 a 50 milhões'
                    ELSE '3) Acima de 50 milhões' END AS faixa_seguidores,
               COUNT(*) AS quantidade_faixas,
               ROUND(AVG(track_popularity), 1) AS popularidade_media,
               MAX(track_popularity) AS popularidade_maxima
        FROM dataset_bruto
        GROUP BY faixa_seguidores
        ORDER BY faixa_seguidores;
    """, conn)
    st.dataframe(df_seg, width="stretch")
    st.bar_chart(df_seg.set_index("faixa_seguidores")[["popularidade_media"]].astype(float))
    conn.close()

# ==========================================
# 2. RANKING 
# ==========================================
elif escolha == "🏆 Ranking (IMDb da Música)":
    st.subheader("Top Músicas Avaliadas pela Comunidade (View: `vw_ranking_musicas`)")
    conn = get_conexao("musica_app")
    
    df_ranking = pd.read_sql(
        "SELECT * FROM vw_ranking_musicas WHERE n_avaliacoes > 0 "
        "ORDER BY nota_media DESC, n_avaliacoes DESC LIMIT 50;", conn)
    
    if not df_ranking.empty:
        st.dataframe(df_ranking, width="stretch")
    else:
        st.info("Ainda não há avaliações suficientes para formar um ranking.")
    conn.close()

# ==========================================
# 3. AVALIAÇÃO (Regra UNIQUE e Tabela Usuário)
# ==========================================
elif escolha == "📝 Fazer Avaliação":
    st.subheader("Avaliar uma Faixa")
    conn = get_conexao("musica_app")
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT m.id_musica, m.track_name, ar.artist_name
        FROM musica m
        JOIN album al   ON al.id_album   = m.id_album
        JOIN artista ar ON ar.id_artista = al.id_artista
        ORDER BY m.track_name ASC
        LIMIT 1000;
    """)
    musicas_db = cursor.fetchall()
    
    if musicas_db:
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
                    cursor.execute("SELECT id_usuario FROM usuario WHERE username = %s", (username,))
                    user = cursor.fetchone()
                    
                    if user:
                        id_user = user['id_usuario']
                    else:
                        cursor.execute("INSERT INTO usuario (username) VALUES (%s)", (username,))
                        id_user = cursor.lastrowid
                    
                    cursor.execute(
                        "INSERT INTO avaliacao_musica (id_usuario, id_musica, nota, comentario) VALUES (%s, %s, %s, %s)", 
                        (id_user, id_musica, nota, comentario)
                    )
                    conn.commit()
                    st.success("Avaliação registrada com sucesso!")
                
                except mysql.connector.IntegrityError:
                    conn.rollback()
                    st.error("Erro: Você já avaliou esta música! (Bloqueio do Banco de Dados)")
                except Exception as e:
                    conn.rollback()
                    st.error(f"Erro inesperado: {e}")
    else:
        st.warning("Nenhuma música cadastrada.")
    conn.close()

# ==========================================
# 4. GERENCIAR CATÁLOGO (CRUD Completo: Create, Read, Update, Delete)
# ==========================================
elif escolha == "⚙️ Gerenciar Catálogo (CRUD)":
    st.subheader("Operações de CRUD no Banco de Dados (`musica_app`)")
    conn = get_conexao("musica_app")
    cursor = conn.cursor()
    
    acao = st.selectbox("Escolha a ação desejada:", [
        "1. Inserir Nova Música (Create)", 
        "2. Consultar Registros (Read)",
        "3. Atualizar Popularidade (Update)", 
        "4. Remover Música (Delete)"
    ])
    
    # ---------------- CREATE ----------------
    if acao == "1. Inserir Nova Música (Create)":
        nome = st.text_input("Nome da Faixa")
        nome_artista = st.text_input("Nome do Artista")
        nome_album = st.text_input("Nome do Álbum")
        
        col1, col2 = st.columns(2)
        with col1:
            duracao = st.number_input("Duração (ms)", min_value=0, step=1000, value=200000)
            ano_album = st.number_input("Ano de Lançamento (se for um novo álbum)", min_value=1900, max_value=2026, step=1, value=2024)
        with col2:
            popularidade = st.slider("Popularidade Inicial", 0, 100, 0)
            explicit = st.checkbox("É uma música com conteúdo explícito?")
        
        if st.button("Inserir Registro"):
            nome, nome_artista, nome_album = nome.strip(), nome_artista.strip(), nome_album.strip()
            if not nome or not nome_artista or not nome_album:
                st.error("Por favor, preencha o nome da música, do artista e do álbum.")
            else:
                try:
                    # PASSO 1: Artista (reaproveita se já existir)
                    cursor.execute("SELECT id_artista FROM artista WHERE artist_name = %s", (nome_artista,))
                    r_art = cursor.fetchone()
                    if r_art:
                        id_art = r_art[0]
                    else:
                        cursor.execute("INSERT INTO artista (artist_name) VALUES (%s)", (nome_artista,))
                        id_art = cursor.lastrowid
                    
                    # PASSO 2: Álbum (amarrado ao artista)
                    cursor.execute("SELECT id_album FROM album WHERE album_name = %s AND id_artista = %s", (nome_album, id_art))
                    r_alb = cursor.fetchone()
                    if r_alb:
                        id_al = r_alb[0]
                    else:
                        cursor.execute("INSERT INTO album (id_artista, album_name, release_year) VALUES (%s, %s, %s)",
                                       (id_art, nome_album, ano_album))
                        id_al = cursor.lastrowid
                    
                    # PASSO 3: Música (amarrada ao álbum)
                    cursor.execute(
                        "INSERT INTO musica (id_album, track_name, duration_ms, explicit, track_popularity) VALUES (%s, %s, %s, %s, %s)", 
                        (id_al, nome, duracao, explicit, popularidade)
                    )
                    id_nova = cursor.lastrowid
                    
                    # Só confirma depois dos 3 passos darem certo
                    conn.commit()
                    st.success(f"Música '{nome}' cadastrada com o ID {id_nova} (Álbum: {nome_album}, Artista: {nome_artista}).")
                    
                    # Mostra a linha recém-criada, lida de volta do banco
                    cursor.execute("""
                        SELECT m.id_musica, m.track_name, ar.artist_name, al.album_name,
                               m.duration_ms, m.explicit, m.track_popularity
                        FROM musica m
                        JOIN album al   ON al.id_album   = m.id_album
                        JOIN artista ar ON ar.id_artista = al.id_artista
                        WHERE m.id_musica = %s;
                    """, (id_nova,))
                    colunas = [c[0] for c in cursor.description]
                    st.dataframe(pd.DataFrame(cursor.fetchall(), columns=colunas), width="stretch")
                except Exception as e:
                    conn.rollback()   # desfaz artista/álbum criados se a música falhar
                    st.error(f"Erro ao inserir no banco: {e}")
    
    # ---------------- READ ----------------
    elif acao == "2. Consultar Registros (Read)":
        tabela_read = st.radio("Selecione a tabela para consultar:",
                               ["musica", "album", "artista", "usuario", "avaliacao_musica"], horizontal=True)
        # tabela_read vem da lista fixa acima, não de texto digitado
        df_consulta = pd.read_sql(f"SELECT * FROM {tabela_read} ORDER BY 1 DESC LIMIT 100;", conn)
        st.caption("Mostrando os 100 registros mais recentes.")
        st.dataframe(df_consulta, width="stretch")
    
    # ---------------- UPDATE ----------------
    elif acao == "3. Atualizar Popularidade (Update)":
        termo = st.text_input("Buscar música ou artista (deixe vazio para ver as mais recentes)")
        musicas = buscar_musicas(cursor, termo)
        if not musicas:
            st.info("Nenhuma música encontrada.")
        else:
            opcoes_mus = {rotulo_musica(m): m[0] for m in musicas}
            alvo = st.selectbox("Música alvo", list(opcoes_mus.keys()))
            nova_pop = st.number_input("Nova Popularidade (0 a 100)", min_value=0, max_value=100, step=1)
            if st.button("Atualizar Métrica"):
                try:
                    cursor.execute("UPDATE musica SET track_popularity = %s WHERE id_musica = %s",
                                   (nova_pop, opcoes_mus[alvo]))
                    conn.commit()
                    if cursor.rowcount:
                        st.success("Popularidade atualizada com sucesso!")
                    else:
                        st.warning("Nenhuma linha alterada (a música não existe ou já tinha esse valor).")
                except Exception as e:
                    conn.rollback()
                    st.error(f"Erro ao atualizar: {e}")
    
    # ---------------- DELETE ----------------
    elif acao == "4. Remover Música (Delete)":
        termo = st.text_input("Buscar música ou artista (deixe vazio para ver as mais recentes)")
        musicas = buscar_musicas(cursor, termo)
        if not musicas:
            st.info("Nenhuma música encontrada.")
        else:
            opcoes_mus = {rotulo_musica(m): m[0] for m in musicas}
            alvo = st.selectbox("Música a remover", list(opcoes_mus.keys()))
            id_del = opcoes_mus[alvo]
            
            cursor.execute("SELECT COUNT(*) FROM avaliacao_musica WHERE id_musica = %s", (id_del,))
            n_aval = cursor.fetchone()[0]
            st.warning(f"⚠️ A exclusão não pode ser desfeita e apagará também {n_aval} avaliação(ões) desta música.")
            confirmou = st.checkbox("Confirmo que quero remover esta música")
            
            if st.button("Confirmar Exclusão"):
                if not confirmou:
                    st.error("Marque a caixa de confirmação antes de excluir.")
                else:
                    try:
                        cursor.execute("DELETE FROM musica WHERE id_musica = %s", (id_del,))
                        conn.commit()
                        if cursor.rowcount:
                            st.success(f"Música {id_del} removida do banco de dados.")
                        else:
                            st.warning("Nenhuma música foi removida (ela pode já ter sido excluída).")
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Erro ao remover: {e}")
    conn.close()

# ==========================================
# 5. VIEWS DO BANCO
# ==========================================
elif escolha == "🔎 Views do Banco":
    st.subheader("Views criadas no schema `musica_app`")
    views = {
        "vw_ranking_musicas": "Ranking das músicas pela nota média das avaliações (AVG, COUNT).",
        "vw_estatisticas_genero": "Quantidade, popularidade (AVG, MAX, MIN) e duração total (SUM) por gênero.",
        "vw_estatisticas_artista": "Álbuns, músicas, popularidade e duração total por artista.",
        "vw_avaliacoes_detalhadas": "Avaliações com usuário, música e artista (junção de 5 tabelas).",
        "vw_atividade_usuarios": "Quantas avaliações cada usuário fez e a nota média que costuma dar.",
    }
    nome_view = st.selectbox("Escolha a view:", list(views.keys()))
    st.caption(views[nome_view])
    conn = get_conexao("musica_app")
    if not view_existe(conn, nome_view):
        st.warning(f"A view `{nome_view}` não existe neste banco. "
                   "Execute `generos_e_views.sql` (ou restaure o dump final).")
    else:
        # nome_view vem da lista fixa acima, não de texto digitado pelo usuário
        df_view = pd.read_sql(f"SELECT * FROM {nome_view} LIMIT 300;", conn)
        if df_view.empty:
            st.info("Esta view ainda não tem dados.")
        else:
            st.dataframe(df_view, width="stretch")
        with st.expander("Ver o SQL da view"):
            cur = conn.cursor()
            cur.execute(f"SHOW CREATE VIEW {nome_view}")
            st.code(cur.fetchone()[1], language="sql")
            cur.close()
    conn.close()

# ==========================================
# 6. VISÃO GERAL (Tabelas)
# ==========================================
elif escolha == "🗃️ Visão Geral (Tabelas)":
    st.subheader("Explorar as Tabelas Normalizadas (Schema: musica_app)")
    conn = get_conexao("musica_app")
    tabela = st.radio("Selecione qual tabela deseja visualizar:",
                      ["artista", "album", "musica", "usuario", "avaliacao_musica", "genero"], horizontal=True)
    ordem = st.radio("Ordem:", ["Mais recentes primeiro", "Mais antigos primeiro"], horizontal=True)
    direcao = "DESC" if ordem.startswith("Mais recentes") else "ASC"
    total = pd.read_sql(f"SELECT COUNT(*) AS n FROM {tabela};", conn)["n"].iloc[0]
    df = pd.read_sql(f"SELECT * FROM {tabela} ORDER BY 1 {direcao} LIMIT 100;", conn)
    st.caption(f"Total na tabela: {total} registro(s). Exibindo {len(df)}.")
    if not df.empty:
        st.dataframe(df, width="stretch")
    else:
        st.info(f"A tabela {tabela} está vazia no momento.")
    conn.close()