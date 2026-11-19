-- ============================================================================
-- SCHEMA 1: db_analise_musica (Catálogo, Métricas Acústicas e Gêneros)
-- ============================================================================
-- Executado primeiro pelo docker-entrypoint-initdb.d (ordem alfabética)
-- e pelo CI (.github/workflows/ci.yml).
-- ============================================================================

CREATE DATABASE IF NOT EXISTS db_analise_musica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE db_analise_musica;

-- ---------------------------------------------------------------------------
-- Tabela de dados brutos importados do CSV Spotify (1000 faixas)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dataset_bruto (
    `Unnamed: 0`       BIGINT DEFAULT NULL,
    artist_name        TEXT,
    genres             TEXT,
    followers          BIGINT DEFAULT NULL,
    artist_popularity  BIGINT DEFAULT NULL,
    artist_url         TEXT,
    track_name         TEXT,
    album_name         TEXT,
    release_date       TEXT,
    duration_ms        BIGINT DEFAULT NULL,
    explicit           TINYINT(1) DEFAULT NULL,
    track_popularity   BIGINT DEFAULT NULL,
    danceability       DOUBLE DEFAULT NULL,
    energy             DOUBLE DEFAULT NULL,
    `key`              BIGINT DEFAULT NULL,
    loudness           DOUBLE DEFAULT NULL,
    `mode`             BIGINT DEFAULT NULL,
    speechiness        DOUBLE DEFAULT NULL,
    acousticness       DOUBLE DEFAULT NULL,
    instrumentalness   DOUBLE DEFAULT NULL,
    liveness           DOUBLE DEFAULT NULL,
    valence            DOUBLE DEFAULT NULL,
    tempo              DOUBLE DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Tabelas normalizadas do catálogo
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Artista (
    id_artista INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    INDEX idx_nome_artista (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Album (
    id_album INT AUTO_INCREMENT PRIMARY KEY,
    id_artista INT NOT NULL,
    nome VARCHAR(255) NOT NULL,
    CONSTRAINT fk_album_artista
        FOREIGN KEY (id_artista) REFERENCES Artista(id_artista) ON DELETE CASCADE,
    INDEX idx_nome_album (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Musica (
    id_musica INT AUTO_INCREMENT PRIMARY KEY,
    id_album INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    popularity INT DEFAULT 0,
    danceability DECIMAL(5,4),
    energy DECIMAL(5,4),
    tempo DECIMAL(6,2),
    duration_ms INT DEFAULT NULL,
    explicit TINYINT(1) DEFAULT 0,
    CONSTRAINT fk_musica_album
        FOREIGN KEY (id_album) REFERENCES Album(id_album) ON DELETE CASCADE,
    INDEX idx_titulo_musica (titulo),
    INDEX idx_popularity (popularity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Tabelas de gêneros (normalização N:M da coluna genres do CSV)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS genero (
    id_genero INT AUTO_INCREMENT PRIMARY KEY,
    nome_genero VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS artista_genero (
    id_artista INT NOT NULL,
    id_genero INT NOT NULL,
    PRIMARY KEY (id_artista, id_genero),
    CONSTRAINT fk_ag_artista
        FOREIGN KEY (id_artista) REFERENCES Artista(id_artista) ON DELETE CASCADE,
    CONSTRAINT fk_ag_genero
        FOREIGN KEY (id_genero) REFERENCES genero(id_genero) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
