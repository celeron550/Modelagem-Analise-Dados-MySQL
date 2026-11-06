# Modelagem-Analise-Dados-MySQL
Repositório dedicado ao projeto de Modelagem, consulta e análise de banco de dados.

# 🎵 Spotify DB - Plataforma de Análise e Avaliação Musical

![Status do Projeto](https://img.shields.io/badge/Status-Concluído-success)
![Python Version](https://img.shields.io/badge/Python-3.12-blue)
![MySQL Version](https://img.shields.io/badge/MySQL-8.0-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)

## 🚀 Como Executar o Projeto Localmente

### 1. Pré-requisitos
Certifique-se de ter instalado em sua máquina:
- [Python 3.10+](https://www.python.org/downloads/)
- [MySQL Server](https://dev.mysql.com/downloads/mysql/)

### 2. Configurando o Banco de Dados
Para facilitar a avaliação, o repositório inclui um arquivo de *dump* completo. 

1. Acesse o seu MySQL via terminal ou interface gráfica (ex: MySQL Workbench / SQLTools).
2. Importe o arquivo de backup que já contém a criação dos dois schemas e todos os dados normalizados:
   ```bash
   mysql -u root -p < backup_final_spotify.sql

Recomenda-se o uso de um ambiente virtual. No terminal, execute:

python3 -m venv ambiente_bd
source ambiente_bd/bin/activate

pip install streamlit pandas mysql-connector-python sqlalchemy

streamlit run dashboard.py
