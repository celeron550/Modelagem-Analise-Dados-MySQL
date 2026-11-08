USE musica_app;


-- Usuarios de exemplo

INSERT IGNORE INTO usuario (username, email) VALUES
  ('ana_souza',      'ana.souza@exemplo.com'),
  ('bruno_lima',     'bruno.lima@exemplo.com'),
  ('carla_mendes',   'carla.mendes@exemplo.com'),
  ('diego_alves',    'diego.alves@exemplo.com'),
  ('elisa_ramos',    'elisa.ramos@exemplo.com'),
  ('fabio_costa',    'fabio.costa@exemplo.com'),
  ('gabi_nunes',     'gabi.nunes@exemplo.com'),
  ('henrique_dias',  'henrique.dias@exemplo.com'),
  ('isabela_rocha',  'isabela.rocha@exemplo.com'),
  ('joao_pereira',   'joao.pereira@exemplo.com'),
  ('karen_martins',  'karen.martins@exemplo.com'),
  ('lucas_ferreira', 'lucas.ferreira@exemplo.com');


-- 2) Avaliacoes

INSERT IGNORE INTO avaliacao_musica
       (id_usuario, id_musica, nota, comentario, data_avaliacao)
SELECT t.id_usuario,
       t.id_musica,
       t.nota,
       -- 3 comentarios possiveis por nota (indice 1..15)
       ELT(3 * (t.nota - 1) + 1 + (CRC32(CONCAT(t.id_usuario, 'c', t.id_musica)) % 3),
           'Nao me agradou.',               'Muito repetitiva para o meu gosto.',  'Nao voltaria a ouvir.',
           'Abaixo do que eu esperava.',    'Tem uma boa ideia, mas nao me pegou.', 'So ok, esqueco rapido.',
           'Boa, mas nada demais.',         'Agradavel de ouvir no dia a dia.',     'Cumpre o que promete.',
           'Muito boa, ja entrou na playlist.', 'Refrao viciante, gostei bastante!', 'Otima producao e bom ritmo.',
           'Obra-prima, ouco em loop!',     'Uma das melhores que ja ouvi.',        'Perfeita do comeco ao fim.'),
       DATE_SUB(NOW(), INTERVAL (CRC32(CONCAT(t.id_usuario, 'd', t.id_musica)) % 60) DAY)
FROM (
    SELECT u.id_usuario,
           m.id_musica,
           GREATEST(1, LEAST(5, ROUND(
               1 + 4 * m.track_popularity / 100                         -- base: popularidade
                 + (CAST(CRC32(u.username) % 3 AS SIGNED) - 1) * 0.5                  -- vies do usuario (-0.5, 0, +0.5)
                 + (CAST(CRC32(CONCAT(u.id_usuario, 'n', m.id_musica)) % 3 AS SIGNED) - 1)  -- ruido (-1, 0, +1)
           ))) AS nota
    FROM usuario u
    JOIN musica  m
      ON (CRC32(CONCAT(u.username, '-', m.id_musica)) % 100) <
         CASE WHEN m.track_popularity >= 70 THEN 12
              WHEN m.track_popularity >= 40 THEN 5
              ELSE 2 END
    WHERE u.email LIKE '%@exemplo.com'
) t;


-- 3) Conferencia

SELECT (SELECT COUNT(*) FROM usuario)          AS usuarios,
       (SELECT COUNT(*) FROM avaliacao_musica) AS avaliacoes,
       (SELECT COUNT(DISTINCT id_musica) FROM avaliacao_musica) AS musicas_avaliadas;

-- Distribuicao das notas
SELECT nota, COUNT(*) AS qtd
FROM avaliacao_musica
GROUP BY nota
ORDER BY nota;

-- Top 10 do ranking (nota media, minimo de 2 avaliacoes)
SELECT m.track_name, ar.artist_name,
       ROUND(AVG(a.nota), 2) AS nota_media,
       COUNT(*)              AS n_avaliacoes
FROM avaliacao_musica a
JOIN musica  m  ON m.id_musica  = a.id_musica
JOIN album   al ON al.id_album  = m.id_album
JOIN artista ar ON ar.id_artista = al.id_artista
GROUP BY m.id_musica, m.track_name, ar.artist_name
HAVING COUNT(*) >= 2
ORDER BY nota_media DESC, n_avaliacoes DESC
LIMIT 10;


-- LIMPEZA 
-- as avaliacoes saem junto por causa do ON DELETE CASCADE)
-- DELETE FROM usuario WHERE email LIKE '%@exemplo.com';