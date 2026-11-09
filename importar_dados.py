import pandas as pd
from sqlalchemy import create_engine
import mysql.connector

# ---------------------------------------------------------
# 1. CARREGAR E LIMPAR DADOS DO CSV (Pandas)
# ---------------------------------------------------------
print("1. Lendo e limpando o arquivo CSV...")
df = pd.read_csv("spotifydataset.csv")

# Limpeza 1: Remover valores nulos nas colunas principais
df = df.dropna(subset=['artist_name', 'track_name', 'album_name'])

# Limpeza 2: Remover o artista genérico 'A' que distorce os dados
df = df[df['artist_name'] != 'A']

# Limpeza 3: Remover faixas duplicadas (mesma música do mesmo artista)
df = df.drop_duplicates(subset=['artist_name', 'track_name'])


# ---------------------------------------------------------
# 2. POPULAR SCHEMA DE ANÁLISE (Dados Brutos)
# ---------------------------------------------------------
print("2. Enviando dados brutos para a base 'musica_analise'...")
engine = create_engine('mysql+mysqlconnector://root:123456@localhost/musica_analise')
df.to_sql('dataset_bruto', con=engine, if_exists='replace', index=False)


# ---------------------------------------------------------
# 3. POPULAR SCHEMA DA APLICAÇÃO (Normalização via SQL)
# ---------------------------------------------------------
print("3. A migrar e normalizar dados para a base 'musica_app'...")
conn = mysql.connector.connect(host="localhost", user="root", password="123456")
cursor = conn.cursor()

# >>> NOVO BLOCO: Limpar as tabelas antes de inserir os dados novos! <<<
cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
cursor.execute("TRUNCATE TABLE musica_app.avaliacao_musica;")
cursor.execute("TRUNCATE TABLE musica_app.musica;")
cursor.execute("TRUNCATE TABLE musica_app.album;")
cursor.execute("TRUNCATE TABLE musica_app.artista;")
cursor.execute("TRUNCATE TABLE musica_app.usuario;")
cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
# >>> FIM DO NOVO BLOCO <<<

# 3.1 Inserir Artistas Únicos
cursor.execute("""
    INSERT INTO musica_app.artista (artist_name)
    SELECT DISTINCT artist_name FROM musica_analise.dataset_bruto;
""")

# 3.2 Inserir Álbuns Únicos (Pegando apenas os 4 primeiros dígitos da data para o 'release_year')
cursor.execute("""
    INSERT INTO musica_app.album (id_artista, album_name, release_year)
    SELECT DISTINCT a.id_artista, d.album_name, CAST(SUBSTRING(d.release_date, 1, 4) AS UNSIGNED)
    FROM musica_analise.dataset_bruto d
    JOIN musica_app.artista a ON d.artist_name = a.artist_name;
""")

# 3.3 Inserir Músicas (Ligando aos IDs e populando os atributos)
cursor.execute("""
    INSERT INTO musica_app.musica (id_album, track_name, duration_ms, explicit, track_popularity)
    SELECT DISTINCT al.id_album, d.track_name, d.duration_ms, d.explicit, d.track_popularity 
    FROM musica_analise.dataset_bruto d
    JOIN musica_app.artista ar ON d.artist_name = ar.artist_name
    JOIN musica_app.album al ON d.album_name = al.album_name AND al.id_artista = ar.id_artista;
""")
# ... (código anterior) ...
# 3.3 Inserir Músicas (Ligando aos IDs e populando os atributos)
cursor.execute("""
    INSERT INTO musica_app.musica (id_album, track_name, duration_ms, explicit, track_popularity)
    SELECT DISTINCT al.id_album, d.track_name, d.duration_ms, d.explicit, d.track_popularity 
    FROM musica_analise.dataset_bruto d
    JOIN musica_app.artista ar ON d.artist_name = ar.artist_name
    JOIN musica_app.album al ON d.album_name = al.album_name AND al.id_artista = ar.id_artista;
""")

# =========================================================
# 4. CRIAR DADOS SEMENTE (Seed Data para Avaliações)
# =========================================================
print("4. A gerar utilizadores e avaliações de teste (Seed Data)...")

# 4.1 Criar 3 utilizadores fictícios (usamos INSERT IGNORE para não duplicar se rodares o script 2 vezes)
usuarios_mock = [("Carlos_Silvano",), ("Mariana_Rock",), ("Lucas_Pop",)]
cursor.executemany("INSERT IGNORE INTO musica_app.usuario (username) VALUES (%s)", usuarios_mock)

# 4.2 Ir buscar os IDs dos utilizadores criados
cursor.execute("SELECT id_usuario FROM musica_app.usuario LIMIT 3;")
ids_usuarios = cursor.fetchall()

# 4.3 Ir buscar 3 IDs de músicas reais que acabaram de ser importadas
cursor.execute("SELECT id_musica FROM musica_app.musica LIMIT 3;")
ids_musicas = cursor.fetchall()

# 4.4 Inserir as avaliações cruzando os utilizadores com as músicas
if len(ids_musicas) >= 3 and len(ids_usuarios) >= 3:
    avaliacoes_mock = [
        (ids_usuarios[0][0], ids_musicas[0][0], 5, "Obra-prima! Produção impecável, não paro de ouvir."),
        (ids_usuarios[1][0], ids_musicas[1][0], 4, "A batida é excelente, mas a letra é um pouco repetitiva."),
        (ids_usuarios[2][0], ids_musicas[2][0], 3, "Música legalzinha, mas não adicionaria na minha playlist favorita.")
    ]
    
    cursor.executemany("""
        INSERT IGNORE INTO musica_app.avaliacao_musica (id_usuario, id_musica, nota, comentario) 
        VALUES (%s, %s, %s, %s)
    """, avaliacoes_mock)

# Salva tudo de uma vez no banco de dados!
conn.commit()
print("Sucesso! Os dados foram limpos, divididos e as avaliações de teste criadas perfeitamente.")
