# Modelagem e Análise de Dados com MySQL

Projeto de **modelagem, consulta e análise de banco de dados** com dados de músicas do Spotify. O repositório reúne o modelo relacional no MySQL, scripts de carga e consulta em Python e um **dashboard interativo em Streamlit** para explorar, analisar e manipular os dados.

## Funcionalidades

O dashboard (`dashboard.py`) possui cinco telas:

| Tela | Descrição |
|------|-----------|
| **Visão Geral** | Explora as tabelas `Artista`, `Album`, `Musica` e `Avaliacao_Musica`, com os nomes relacionados via JOIN (limite de 100 registros) |
| **Estatísticas de Artistas** | Gráfico com o Top 10 artistas por popularidade média das faixas |
| **Gerenciar Músicas (CRUD)** | Inserir nova música, atualizar popularidade e remover música |
| **Visualizar Avaliações** | Lista os comentários e notas da comunidade |
| **Nova Avaliação** | Permite avaliar uma faixa (nota de 0 a 10 e comentário), selecionando ou cadastrando um usuário |

## Modelo de dados

Banco: `engenharia_musica`

```
Artista ──< Album ──< Musica ──< avaliacao_musica >── usuario
```

- **Artista**: dados do artista (`artist_name`, ...)
- **Album**: pertence a um artista (`id_artista`), com `album_name` e `release_date`
- **Musica**: pertence a um álbum (`id_album`), com `track_name`, `duration_ms`, `explicit` e `track_popularity`
- **usuario**: `username` e `email` únicos, com data de cadastro
- **avaliacao_musica**: nota (1 a 5) e comentário de um usuário sobre uma música. Cada usuário avalia uma música uma única vez (`UNIQUE (id_usuario, id_musica)`).

## Estrutura do repositório

| Arquivo | Função |
|---------|--------|
| `dashboard.py` | Aplicação Streamlit |
| `backup_engenharia_musica.sql` | Dump do banco `engenharia_musica` |
| `criar_usuario.sql` | Cria as tabelas `usuario` e `avaliacao_musica` |
| `importar_dados.py` | Carrega `spotifydataset.csv` na tabela bruta `dataset_bruto` |
| `consultas.py` | Consultas SQL de análise em Python |
| `exemplo.py` | Exemplo de uso |
| `spotifydataset.csv` | Dataset original do Spotify |
| `spotify_dataset.db` | Versão do dataset em arquivo de banco |
| `requirements.txt` | Dependências Python |

## Como executar


### Execução local

Pré-requisitos: Python 3.10+ e MySQL 8.

1. Instale as dependências:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Crie o banco e restaure o backup:

   ```bash
   mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS engenharia_musica"
   mysql -u root -p engenharia_musica < backup_engenharia_musica.sql
   mysql -u root -p engenharia_musica < criar_usuario.sql
   ```

3. Inicie o dashboard:

   ```bash
   streamlit run dashboard.py
   ```

### Importar o dataset bruto (opcional)

Para recriar a tabela `dataset_bruto` a partir do CSV:

```bash
python importar_dados.py
```



## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
