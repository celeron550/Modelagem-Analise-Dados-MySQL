-- ============================================================================
-- SCHEMA 1: db_analise_musica (Catálogo e Métricas Acústicas)
-- ============================================================================
CREATE DATABASE IF NOT EXISTS db_analise_musica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE db_analise_musica;

CREATE TABLE IF NOT EXISTS Artista (
    id_artista INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    INDEX idx_nome_artista (nome)
);

CREATE TABLE IF NOT EXISTS Album (
    id_album INT AUTO_INCREMENT PRIMARY KEY,
    id_artista INT NOT NULL,
    nome VARCHAR(255) NOT NULL,
    CONSTRAINT fk_album_artista
        FOREIGN KEY (id_artista) REFERENCES Artista(id_artista) ON DELETE CASCADE,
    INDEX idx_nome_album (nome)
);

CREATE TABLE IF NOT EXISTS Musica (
    id_musica INT AUTO_INCREMENT PRIMARY KEY,
    id_album INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    popularity INT DEFAULT 0,
    danceability DECIMAL(5,4),
    energy DECIMAL(5,4),
    tempo DECIMAL(6,2),
    CONSTRAINT fk_musica_album
        FOREIGN KEY (id_album) REFERENCES Album(id_album) ON DELETE CASCADE,
    INDEX idx_titulo_musica (titulo),
    INDEX idx_popularity (popularity)
);

-- Seed mínimo para validação imediata do ambiente e testes automatizados
INSERT IGNORE INTO Artista (id_artista, nome) VALUES
    (1, 'Linkin Park'),
    (2, 'Daft Punk');

INSERT IGNORE INTO Album (id_album, id_artista, nome) VALUES
    (1, 1, 'Hybrid Theory'),
    (2, 1, 'Meteora'),
    (3, 2, 'Random Access Memories');

INSERT IGNORE INTO Musica (id_musica, id_album, titulo, popularity, danceability, energy, tempo) VALUES
    (1, 1, 'In the End', 88, 0.5560, 0.8640, 105.14),
    (2, 2, 'Numb', 89, 0.4960, 0.8630, 110.02),
    (3, 3, 'Get Lucky', 85, 0.7940, 0.8110, 116.05);
