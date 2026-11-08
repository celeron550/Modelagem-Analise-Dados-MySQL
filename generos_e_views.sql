USE musica_app;

DELETE FROM artista_genero;
DELETE FROM genero;
ALTER TABLE genero AUTO_INCREMENT = 1;

INSERT IGNORE INTO genero (nome_genero)
SELECT DISTINCT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(d.genres, ',', n.i), ',', -1))
FROM (SELECT DISTINCT genres
      FROM musica_analise.dataset_bruto
      WHERE genres IS NOT NULL AND genres <> '') d
JOIN (SELECT 1 AS i UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
      UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
      UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
      UNION ALL SELECT 13 UNION ALL SELECT 14 UNION ALL SELECT 15 UNION ALL SELECT 16
      UNION ALL SELECT 17 UNION ALL SELECT 18 UNION ALL SELECT 19 UNION ALL SELECT 20) n
  ON n.i <= 1 + LENGTH(d.genres) - LENGTH(REPLACE(d.genres, ',', ''));

INSERT IGNORE INTO artista_genero (id_artista, id_genero)
SELECT DISTINCT ar.id_artista, ge.id_genero
FROM (SELECT DISTINCT artist_name, genres
      FROM musica_analise.dataset_bruto
      WHERE genres IS NOT NULL AND genres <> '') d
JOIN (SELECT 1 AS i UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
      UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
      UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
      UNION ALL SELECT 13 UNION ALL SELECT 14 UNION ALL SELECT 15 UNION ALL SELECT 16
      UNION ALL SELECT 17 UNION ALL SELECT 18 UNION ALL SELECT 19 UNION ALL SELECT 20) n
  ON n.i <= 1 + LENGTH(d.genres) - LENGTH(REPLACE(d.genres, ',', ''))
JOIN artista ar ON ar.artist_name = d.artist_name
JOIN genero  ge ON ge.nome_genero = TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(d.genres, ',', n.i), ',', -1));


-- Estatísticas por gênero (COUNT, AVG, MAX, MIN, SUM)
CREATE OR REPLACE VIEW vw_estatisticas_genero AS
SELECT g.nome_genero,
       COUNT(DISTINCT ar.id_artista)              AS n_artistas,
       COUNT(m.id_musica)                         AS total_musicas,
       ROUND(AVG(m.track_popularity), 2)          AS popularidade_media,
       MAX(m.track_popularity)                    AS popularidade_maxima,
       MIN(m.track_popularity)                    AS popularidade_minima,
       ROUND(SUM(m.duration_ms) / 60000.0, 2)     AS duracao_total_minutos
FROM genero g
JOIN artista_genero ag ON ag.id_genero  = g.id_genero
JOIN artista ar        ON ar.id_artista = ag.id_artista
JOIN album al          ON al.id_artista = ar.id_artista
JOIN musica m          ON m.id_album    = al.id_album
GROUP BY g.id_genero, g.nome_genero;

-- Estatísticas por artista
CREATE OR REPLACE VIEW vw_estatisticas_artista AS
SELECT ar.id_artista,
       ar.artist_name,
       COUNT(DISTINCT al.id_album)                AS n_albuns,
       COUNT(m.id_musica)                         AS n_musicas,
       ROUND(AVG(m.track_popularity), 2)          AS popularidade_media,
       MAX(m.track_popularity)                    AS popularidade_maxima,
       MIN(m.track_popularity)                    AS popularidade_minima,
       ROUND(SUM(m.duration_ms) / 60000.0, 1)     AS total_minutos
FROM artista ar
JOIN album al ON al.id_artista = ar.id_artista
JOIN musica m ON m.id_album    = al.id_album
GROUP BY ar.id_artista, ar.artist_name;

-- Avaliações com nome do usuário, da música e do artista
CREATE OR REPLACE VIEW vw_avaliacoes_detalhadas AS
SELECT a.id_avaliacao,
       u.username        AS usuario,
       m.track_name      AS musica,
       ar.artist_name    AS artista,
       a.nota,
       a.comentario,
       a.data_avaliacao
FROM avaliacao_musica a
JOIN usuario u ON u.id_usuario = a.id_usuario
JOIN musica  m ON m.id_musica  = a.id_musica
JOIN album  al ON al.id_album  = m.id_album
JOIN artista ar ON ar.id_artista = al.id_artista;

-- Atividade dos usuários (quem avalia mais e como avalia)
CREATE OR REPLACE VIEW vw_atividade_usuarios AS
SELECT u.id_usuario,
       u.username,
       COUNT(a.id_avaliacao)            AS n_avaliacoes,
       ROUND(AVG(a.nota), 2)            AS nota_media,
       MAX(a.nota)                      AS nota_maxima,
       MIN(a.nota)                      AS nota_minima
FROM usuario u
LEFT JOIN avaliacao_musica a ON a.id_usuario = u.id_usuario
GROUP BY u.id_usuario, u.username;


SELECT (SELECT COUNT(*) FROM musica)          AS musicas,
       (SELECT COUNT(*) FROM album)           AS albuns,
       (SELECT COUNT(*) FROM artista)         AS artistas,
       (SELECT COUNT(*) FROM genero)          AS generos,
       (SELECT COUNT(*) FROM artista_genero)  AS ligacoes_artista_genero;