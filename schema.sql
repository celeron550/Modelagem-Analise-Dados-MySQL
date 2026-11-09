-- =======================================================================
-- 1. SCHEMA PARA ANÁLISE DE DADOS (Dados Brutos do CSV)
-- =======================================================================
DROP DATABASE IF EXISTS musica_analise;
DROP DATABASE IF EXISTS musica_app;
CREATE DATABASE IF NOT EXISTS musica_analise;
USE musica_analise;

-- A tabela dataset_bruto será preenchida pelo Pandas (importar_dados.py), 
-- mas deixamos a estrutura base preparada aqui.
CREATE TABLE IF NOT EXISTS dataset_bruto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(100),
    artists TEXT,
    album_name VARCHAR(255),
    track_name VARCHAR(255),
    popularity INT,
    duration_ms INT,
    explicit BOOLEAN,
    danceability FLOAT,
    energy FLOAT,
    acousticness FLOAT,
    valence FLOAT,
    track_genre VARCHAR(100)
);

-- =======================================================================
-- 2. SCHEMA PARA O APLICATIVO WEB (Dados Normalizados)
-- =======================================================================
CREATE DATABASE IF NOT EXISTS musica_app;
USE musica_app;

-- Tabela de Utilizadores
CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) UNIQUE
);

-- Tabela de Artistas (com spotify_id para evitar erro de homónimos)
CREATE TABLE artista (
    id_artista INT AUTO_INCREMENT PRIMARY KEY,
    spotify_id VARCHAR(100) UNIQUE, 
    artist_name VARCHAR(255) NOT NULL
);

-- Tabela de Gêneros (Resolve o problema da 1ª Forma Normal)
CREATE TABLE genero (
    id_genero INT AUTO_INCREMENT PRIMARY KEY,
    nome_genero VARCHAR(100) NOT NULL UNIQUE
);

-- Tabela de Ligação N:M (Artista <-> Gênero)
CREATE TABLE artista_genero (
    id_artista INT NOT NULL,
    id_genero INT NOT NULL,
    PRIMARY KEY (id_artista, id_genero),
    FOREIGN KEY (id_artista) REFERENCES artista(id_artista) ON DELETE CASCADE,
    FOREIGN KEY (id_genero) REFERENCES genero(id_genero) ON DELETE CASCADE
);

-- Tabela de Álbuns (Com datas separadas e bem formatadas)
CREATE TABLE album (
    id_album INT AUTO_INCREMENT PRIMARY KEY,
    id_artista INT NOT NULL,
    album_name VARCHAR(255) NOT NULL,
    release_year INT,
    release_date DATE NULL,
    FOREIGN KEY (id_artista) REFERENCES artista(id_artista) ON DELETE CASCADE
);

-- Tabela de Músicas (Com NOT NULL nas colunas obrigatórias)
CREATE TABLE musica (
    id_musica INT AUTO_INCREMENT PRIMARY KEY,
    id_album INT NOT NULL,
    track_name VARCHAR(255) NOT NULL,
    duration_ms INT NOT NULL,
    explicit BOOLEAN DEFAULT FALSE,
    track_popularity INT DEFAULT 0,
    FOREIGN KEY (id_album) REFERENCES album(id_album) ON DELETE CASCADE
);

-- Tabela de Avaliações (Com a regra UNIQUE pedida pela análise)
CREATE TABLE avaliacao_musica (
    id_avaliacao INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_musica INT NOT NULL,
    nota TINYINT NOT NULL CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    data_avaliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_usuario, id_musica), -- Impede o mesmo utilizador de dar 2 notas à mesma música
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_musica) REFERENCES musica(id_musica) ON DELETE CASCADE
);

-- =======================================================================
-- 3. VIEWS (Requisito do Enunciado)
-- =======================================================================
CREATE VIEW vw_ranking_musicas AS
SELECT 
    m.id_musica, 
    m.track_name, 
    ar.artist_name,       
    ROUND(AVG(a.nota), 2) AS nota_media, 
    COUNT(a.id_avaliacao) AS n_avaliacoes
FROM musica m
JOIN album al ON al.id_album = m.id_album
JOIN artista ar ON ar.id_artista = al.id_artista
LEFT JOIN avaliacao_musica a ON a.id_musica = m.id_musica
GROUP BY m.id_musica, m.track_name, ar.artist_name;