import pandas as pd
from sqlalchemy import create_engine

# Lê o arquivo local
df = pd.read_csv('spotifydataset.csv')

# Conecta ao MySQL (usuario root, senha 123456, banco engenharia_musica)
engine = create_engine('mysql+mysqlconnector://root:123456@localhost/engenharia_musica')

# Envia os dados inteiros para a tabela temporária
df.to_sql('dataset_bruto', con=engine, if_exists='replace', index=False)
print("Tabela dataset_bruto criada e populada com sucesso!")