import pandas as pd
from sqlalchemy import create_engine
from consultas import *

# 1. Montar a string de conexão
# Formato: mysql+driver://usuario:senha@host:porta/nome_do_banco
USUARIO = "root"
SENHA = "root123"
HOST = "localhost"
PORTA = "3306"
BANCO = "engenharia_musica"

string_conexao = f"mysql+pymysql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}"

# 2. Criar a "Engine" de conexão
engine = create_engine(string_conexao)

# 3. Executar as consultas usando um gerenciador de contexto (with)
with engine.connect() as conexao:
    
    # Exemplo 1: Consulta COM filtro (passando os parâmetros)
    df_artista = pd.read_sql_query(
        sql=musicas_por_artista(), 
        con=conexao, 
        params={"nome_artista": "Adele"}
    )
    
    # Exemplo 2: Consulta SEM filtro
    df_ranking = pd.read_sql_query(
        sql=rank_popularidade(), 
        con=conexao
    )

# A partir daqui a conexão com o MySQL já foi fechada automaticamente.
# Os dados estão carregados na memória do Python e prontos para o dashboard.
print("--- Músicas do Artista ---")
print(df_artista.head())

print("\n--- Ranking de Popularidade ---")
print(df_ranking.head())