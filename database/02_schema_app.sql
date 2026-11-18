-- ============================================================================
-- SCHEMA 2: db_app_musica (Identidade, Avaliações, Auditoria e Views)
-- ============================================================================
CREATE DATABASE IF NOT EXISTS db_app_musica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE db_app_musica;

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
