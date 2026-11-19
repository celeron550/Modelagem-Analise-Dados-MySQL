USE musica_app;

-- tabela de Gêneros
INSERT IGNORE INTO genero (nome_genero)
SELECT DISTINCT genres 
FROM musica_analise.dataset_bruto 
WHERE genres IS NOT NULL AND genres != '';

-- tabela de Artistas
INSERT IGNORE INTO artista (artist_name)
SELECT DISTINCT artist_name 
FROM musica_analise.dataset_bruto 
WHERE artist_name IS NOT NULL AND artist_name != '';

-- tabela de Álbuns
INSERT IGNORE INTO album (album_name, id_artista)
SELECT DISTINCT db.album_name, ar.id_artista
FROM musica_analise.dataset_bruto db
JOIN artista ar ON db.artist_name = ar.artist_name
WHERE db.album_name IS NOT NULL;

-- tabela de Músicas
INSERT IGNORE INTO musica (track_name, duration_ms, explicit, track_popularity, id_album)
SELECT DISTINCT db.track_name, db.duration_ms, IF(db.explicit = 'True' OR db.explicit = 1, 1, 0), db.track_popularity, al.id_album
FROM musica_analise.dataset_bruto db
JOIN artista ar ON db.artist_name = ar.artist_name
JOIN album al ON db.album_name = al.album_name AND al.id_artista = ar.id_artista;

-- tabela de relacionamento Artista-Gênero
INSERT IGNORE INTO artista_genero (id_artista, id_genero)
SELECT DISTINCT ar.id_artista, g.id_genero
FROM musica_analise.dataset_bruto db
JOIN artista ar ON db.artist_name = ar.artist_name
JOIN genero g ON db.genres = g.nome_genero;

-- A View esteja apontando para as tabelas corretas com LEFT JOIN
CREATE OR REPLACE VIEW vw_estatisticas_genero AS
SELECT 
    g.nome_genero,
    COUNT(m.id_musica) AS total_musicas,
    ROUND(AVG(m.track_popularity), 2) AS popularidade_media,
    MAX(m.track_popularity) AS popularidade_maxima,
    MIN(m.track_popularity) AS popularidade_minima,
    ROUND(SUM(m.duration_ms) / 60000.0, 2) AS duracao_total_minutos
FROM genero g
LEFT JOIN artista_genero ag ON g.id_genero = ag.id_genero
LEFT JOIN artista ar ON ag.id_artista = ar.id_artista
LEFT JOIN album al ON ar.id_artista = al.id_artista
LEFT JOIN musica m ON al.id_album = m.id_album
GROUP BY g.id_genero, g.nome_genero;
