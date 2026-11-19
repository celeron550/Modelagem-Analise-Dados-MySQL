-- ============================================================================
-- SCHEMA 2: db_app_musica (Identidade, Avaliações, Auditoria e Views)
-- ============================================================================
-- Deve ser executado APÓS 01_schema_analise.sql e 02_dados_spotify.sql
-- pois as views e FKs fazem referência cruzada a db_analise_musica.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS db_app_musica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE db_app_musica;

-- ---------------------------------------------------------------------------
-- Tabelas de identidade e avaliações
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    role ENUM('USER', 'ADMIN') NOT NULL DEFAULT 'USER',
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Avaliacao_Musica (
    id_avaliacao INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_musica INT NOT NULL,
    nota DECIMAL(3,1) NOT NULL,
    comentario TEXT,
    data_avaliacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_avaliacao_usuario
        FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_avaliacao_musica
        FOREIGN KEY (id_musica) REFERENCES db_analise_musica.Musica(id_musica) ON DELETE CASCADE,
    CONSTRAINT uq_usuario_musica UNIQUE (id_usuario, id_musica),
    CONSTRAINT chk_nota_intervalo CHECK (nota >= 0.0 AND nota <= 10.0),
    INDEX idx_avaliacao_musica (id_musica)
);

CREATE TABLE IF NOT EXISTS Log_Avaliacoes (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    id_avaliacao INT NOT NULL,
    nota_antiga DECIMAL(3,1),
    nota_nova DECIMAL(3,1),
    data_alteracao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Trigger de auditoria
-- ---------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_auditoria_avaliacao;
DELIMITER //
CREATE TRIGGER trg_auditoria_avaliacao
AFTER UPDATE ON Avaliacao_Musica
FOR EACH ROW
BEGIN
    IF OLD.nota <> NEW.nota THEN
        INSERT INTO Log_Avaliacoes (id_avaliacao, nota_antiga, nota_nova)
        VALUES (OLD.id_avaliacao, OLD.nota, NEW.nota);
    END IF;
END //
DELIMITER ;

-- ---------------------------------------------------------------------------
-- Stored Procedure para inserir avaliações com validação
-- ---------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_inserir_avaliacao;
DELIMITER //
CREATE PROCEDURE sp_inserir_avaliacao(
    IN p_id_usuario INT,
    IN p_id_musica INT,
    IN p_nota DECIMAL(3,1),
    IN p_comentario TEXT
)
BEGIN
    IF p_nota < 0.0 OR p_nota > 10.0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Operação negada: A nota deve estar entre 0.0 e 10.0';
    ELSE
        INSERT INTO Avaliacao_Musica (id_usuario, id_musica, nota, comentario)
        VALUES (p_id_usuario, p_id_musica, p_nota, p_comentario);
    END IF;
END //
DELIMITER ;

-- ---------------------------------------------------------------------------
-- Seed: usuários e avaliações de demonstração
-- ---------------------------------------------------------------------------
INSERT IGNORE INTO Usuario (id_usuario, username, email, senha_hash, role) VALUES
    (1, 'Carlos_Silvano', 'carlos@demo.com',  'pbkdf2_demo_hash_1', 'ADMIN'),
    (2, 'Mariana_Rock',   'mariana@demo.com', 'pbkdf2_demo_hash_2', 'USER'),
    (3, 'Lucas_Pop',      'lucas@demo.com',   'pbkdf2_demo_hash_3', 'USER');

INSERT IGNORE INTO Avaliacao_Musica (id_usuario, id_musica, nota, comentario) VALUES
    (1, 1, 9.0,  'Produção impecável da Ariana Grande!'),
    (1, 31, 10.0, 'Cruel Summer é perfeita!'),
    (2, 41, 8.5,  'I Wanna Be Yours é uma obra-prima.'),
    (2, 71, 9.5,  'Dancing Queen nunca envelhece!'),
    (3, 91, 8.0,  'Back In Black é atemporal.');

-- ---------------------------------------------------------------------------
-- Views consolidadas (catálogo + app)
-- ---------------------------------------------------------------------------

-- View: Ranking da comunidade (avaliações agregadas por faixa)
CREATE OR REPLACE VIEW vw_ranking_comunidade AS
SELECT
    m.id_musica,
    ar.nome AS artista,
    m.titulo AS faixa,
    COUNT(av.id_avaliacao) AS total_avaliacoes,
    ROUND(AVG(av.nota), 1) AS nota_media,
    MAX(av.nota) AS maior_nota,
    MIN(av.nota) AS menor_nota
FROM db_analise_musica.Musica m
JOIN db_analise_musica.Album al ON m.id_album = al.id_album
JOIN db_analise_musica.Artista ar ON al.id_artista = ar.id_artista
JOIN db_app_musica.Avaliacao_Musica av ON m.id_musica = av.id_musica
GROUP BY m.id_musica, ar.nome, m.titulo
HAVING total_avaliacoes > 0
ORDER BY nota_media DESC;

-- View: Ranking de músicas (todas, incluindo sem avaliação)
CREATE OR REPLACE VIEW vw_ranking_musicas AS
SELECT
    m.id_musica,
    m.titulo AS track_name,
    ar.nome AS artist_name,
    ROUND(AVG(a.nota), 2) AS nota_media,
    COUNT(a.id_avaliacao) AS n_avaliacoes
FROM db_analise_musica.Musica m
JOIN db_analise_musica.Album al ON al.id_album = m.id_album
JOIN db_analise_musica.Artista ar ON ar.id_artista = al.id_artista
LEFT JOIN db_app_musica.Avaliacao_Musica a ON a.id_musica = m.id_musica
GROUP BY m.id_musica, m.titulo, ar.nome;

-- View: Estatísticas por gênero (COUNT, AVG, MAX, MIN, SUM)
CREATE OR REPLACE VIEW vw_estatisticas_genero AS
SELECT
    g.nome_genero,
    COUNT(DISTINCT ar.id_artista)              AS n_artistas,
    COUNT(m.id_musica)                         AS total_musicas,
    ROUND(AVG(m.popularity), 2)                AS popularidade_media,
    MAX(m.popularity)                          AS popularidade_maxima,
    MIN(m.popularity)                          AS popularidade_minima,
    ROUND(SUM(m.duration_ms) / 60000.0, 2)     AS duracao_total_minutos
FROM db_analise_musica.genero g
JOIN db_analise_musica.artista_genero ag ON ag.id_genero  = g.id_genero
JOIN db_analise_musica.Artista ar        ON ar.id_artista = ag.id_artista
JOIN db_analise_musica.Album al          ON al.id_artista = ar.id_artista
JOIN db_analise_musica.Musica m          ON m.id_album    = al.id_album
GROUP BY g.id_genero, g.nome_genero;

-- View: Estatísticas por artista
CREATE OR REPLACE VIEW vw_estatisticas_artista AS
SELECT
    ar.id_artista,
    ar.nome AS artist_name,
    COUNT(DISTINCT al.id_album)                AS n_albuns,
    COUNT(m.id_musica)                         AS n_musicas,
    ROUND(AVG(m.popularity), 2)                AS popularidade_media,
    MAX(m.popularity)                          AS popularidade_maxima,
    MIN(m.popularity)                          AS popularidade_minima,
    ROUND(SUM(m.duration_ms) / 60000.0, 1)     AS total_minutos
FROM db_analise_musica.Artista ar
JOIN db_analise_musica.Album al ON al.id_artista = ar.id_artista
JOIN db_analise_musica.Musica m ON m.id_album    = al.id_album
GROUP BY ar.id_artista, ar.nome;

-- View: Avaliações detalhadas (nome do usuário, música e artista)
CREATE OR REPLACE VIEW vw_avaliacoes_detalhadas AS
SELECT
    a.id_avaliacao,
    u.username        AS usuario,
    m.titulo          AS musica,
    ar.nome           AS artista,
    a.nota,
    a.comentario,
    a.data_avaliacao
FROM db_app_musica.Avaliacao_Musica a
JOIN db_app_musica.Usuario u           ON u.id_usuario = a.id_usuario
JOIN db_analise_musica.Musica m        ON m.id_musica  = a.id_musica
JOIN db_analise_musica.Album al        ON al.id_album  = m.id_album
JOIN db_analise_musica.Artista ar      ON ar.id_artista = al.id_artista;

-- View: Atividade dos usuários (quem avalia mais e como avalia)
CREATE OR REPLACE VIEW vw_atividade_usuarios AS
SELECT
    u.id_usuario,
    u.username,
    COUNT(a.id_avaliacao)            AS n_avaliacoes,
    ROUND(AVG(a.nota), 2)            AS nota_media,
    MAX(a.nota)                      AS nota_maxima,
    MIN(a.nota)                      AS nota_minima
FROM db_app_musica.Usuario u
LEFT JOIN db_app_musica.Avaliacao_Musica a ON a.id_usuario = u.id_usuario
GROUP BY u.id_usuario, u.username;
