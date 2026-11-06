def query_musica() -> str:
    """Busca os detalhes globais de uma música específica."""
    return """
    SELECT 
        m.track_name AS faixa,
        ar.artist_name AS artista,
        al.album_name AS album,
        m.track_popularity AS popularidade_global
    FROM Musica m
    JOIN Album al ON m.id_album = al.id_album
    JOIN Artista ar ON al.id_artista = ar.id_artista
    WHERE m.track_name = %(nome_musica)s;
    """

def query_album() -> str:
    """Lista as músicas e os dados globais de um álbum específico."""
    return """
    SELECT 
        al.album_name AS album,
        al.release_date AS data_lancamento,
        ar.artist_name AS artista,
        m.track_name AS faixa,
        m.track_popularity AS popularidade,
        m.tempo AS bpm
    FROM Album al
    JOIN Artista ar ON al.id_artista = ar.id_artista
    LEFT JOIN Musica m ON al.id_album = m.id_album
    WHERE al.album_name = %(nome_album)s
    ORDER BY m.track_name;
    """

def rank_artistas() -> str:
    """Gera o ranking de artistas por popularidade global."""
    return """
    SELECT 
        artist_name AS artista,
        genres AS generos,
        followers AS seguidores,
        artist_popularity AS popularidade
    FROM Artista
    ORDER BY artist_popularity DESC
    LIMIT 10;
    """

def musicas_por_artista() -> str:
    """Filtra as métricas musicais dado um determinado artista."""
    return """
    SELECT 
        m.track_name AS musica,
        al.album_name AS album,
        m.track_popularity AS popularidade,
        m.danceability,
        m.energy
    FROM Musica m
    JOIN Album al ON m.id_album = al.id_album
    JOIN Artista ar ON al.id_artista = ar.id_artista
    WHERE ar.artist_name = %(nome_artista)s
    ORDER BY m.track_popularity DESC;
    """

def musicas_por_album() -> str:
    """Filtra as características acústicas dado um determinado álbum."""
    return """
    SELECT 
        m.track_name AS faixa,
        m.tempo AS bpm,
        m.energy,
        m.danceability
    FROM Musica m
    JOIN Album al ON m.id_album = al.id_album
    WHERE al.album_name = %(nome_album)s
    ORDER BY m.track_name;
    """

def rank_popularidade() -> str:
    """Top 10 artistas com maior popularidade média (Dados Globais)."""
    return """
    SELECT 
        ar.artist_name AS artista,
        COUNT(m.id_musica) AS total_faixas,
        ROUND(AVG(m.track_popularity), 2) AS popularidade_media
    FROM Artista ar
    JOIN Album al ON ar.id_artista = al.id_artista
    JOIN Musica m ON al.id_album = m.id_album
    GROUP BY ar.id_artista, ar.artist_name
    HAVING COUNT(m.id_musica) > 5 
    ORDER BY popularidade_media DESC
    LIMIT 10;
    """

def analise_audio() -> str:
    """Relação entre energia, danceability e popularidade nas faixas de maior sucesso."""
    return """
    SELECT 
        m.track_name AS musica,
        ar.artist_name AS artista,
        m.danceability,
        m.energy,
        m.track_popularity AS popularidade
    FROM Musica m
    JOIN Album al ON m.id_album = al.id_album
    JOIN Artista ar ON al.id_artista = ar.id_artista
    WHERE m.track_popularity >= 60 
    ORDER BY m.track_popularity DESC;
    """

def ritmo_album() -> str:
    """Extrai as estatísticas de BPM por álbum de cada artista."""
    return """
    SELECT 
        ar.artist_name AS artista,
        al.album_name AS album,
        COUNT(m.id_musica) AS qtd_musicas,
        ROUND(AVG(m.tempo), 1) AS bpm_medio,
        ROUND(MIN(m.tempo), 1) AS bpm_minimo,
        ROUND(MAX(m.tempo), 1) AS bpm_maximo
    FROM Album al
    JOIN Artista ar ON al.id_artista = ar.id_artista
    JOIN Musica m ON al.id_album = m.id_album
    GROUP BY ar.artist_name, al.album_name
    ORDER BY ar.artist_name, bpm_medio DESC;
    """