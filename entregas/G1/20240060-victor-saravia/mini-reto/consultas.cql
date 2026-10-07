CONSISTENCY QUORUM;
USE spotify_20240060;

-- C1. Perfil del usuario u116.
SELECT usuario_id, nombre, pais, plan
FROM perfil_usuario
WHERE usuario_id = 'u116';

-- C2. Diez reproducciones más recientes del usuario u031.
SELECT reproducida_en, titulo, artista
FROM reproducciones_recientes_por_usuario
WHERE usuario_id = 'u031'
ORDER BY reproducida_en DESC
LIMIT 10;

-- C3. Canciones de la playlist p15, en orden.
SELECT posicion, titulo, artista
FROM canciones_por_playlist_orden
WHERE playlist_id = 'p15'
ORDER BY posicion ASC;

-- C4. Reproducciones de c017 durante el 9 de septiembre de 2026 (UTC).
SELECT COUNT(*) AS reproducciones
FROM reproducciones_por_cancion_dia
WHERE cancion_id = 'c017' AND dia = '2026-09-09';
