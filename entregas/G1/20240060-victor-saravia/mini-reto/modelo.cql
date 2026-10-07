CREATE KEYSPACE IF NOT EXISTS spotify_20240060
WITH replication = {'class': 'NetworkTopologyStrategy', 'dc-g1': 3}
AND durable_writes = true;

CREATE TABLE IF NOT EXISTS spotify_20240060.perfil_usuario (
    usuario_id text PRIMARY KEY,
    nombre text,
    pais text,
    plan text
);

CREATE TABLE IF NOT EXISTS spotify_20240060.reproducciones_recientes_por_usuario (
    usuario_id text,
    reproducida_en timestamp,
    reproduccion_id int,
    titulo text,
    artista text,
    PRIMARY KEY ((usuario_id), reproducida_en, reproduccion_id)
) WITH CLUSTERING ORDER BY (reproducida_en DESC, reproduccion_id ASC);

CREATE TABLE IF NOT EXISTS spotify_20240060.canciones_por_playlist_orden (
    playlist_id text,
    posicion int,
    cancion_id text,
    titulo text,
    artista text,
    PRIMARY KEY ((playlist_id), posicion, cancion_id)
) WITH CLUSTERING ORDER BY (posicion ASC, cancion_id ASC);

CREATE TABLE IF NOT EXISTS spotify_20240060.reproducciones_por_cancion_dia (
    cancion_id text,
    dia date,
    reproduccion_id int,
    PRIMARY KEY ((cancion_id, dia), reproduccion_id)
);
