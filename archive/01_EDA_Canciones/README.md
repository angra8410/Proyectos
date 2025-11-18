```markdown
# 01_EDA_Canciones — Ingest Spotify tracks

Este README explica cómo ejecutar el workflow de ingestión y dónde encontrar los resultados.

Cómo ejecutar el workflow manualmente (Actions)
1. Asegúrate de que los Secrets están configurados:
   - SPOTIPY_CLIENT_ID
   - SPOTIPY_CLIENT_SECRET
   - (opcional) MAX_TRACKS

   Ve a: Settings → Secrets and variables → Actions y añade/actualiza los valores.

2. En GitHub, abre la pestaña "Actions" del repositorio y selecciona
   el workflow "01-EDA — Ingest Spotify tracks (robust path + diagnostic)".

3. Haz clic en "Run workflow" y proporciona inputs de ejemplo:
   - playlists: (opcional) deja en blanco o pon IDs/URLs separadas por comas
   - artists: por ejemplo `Coldplay`
   - max_tracks: por ejemplo `50`

4. Ejecuta. Observa los pasos:
   - Spotify token diagnostic: comprobadará que las secrets producen un token (no imprime el token entero).
   - Test audio-features (diagnostic): realizará una petición a /v1/audio-features para verificar acceso.
   - Locate and run ingest script: buscará y ejecutará `ingest_spotify.py` en el repo.
   - Upload CSV artifact: subirá `spotify_tracks_csv` como artifact del run.

Descargar resultados
- Una vez finalizada la ejecución, en la página del run, en la sección "Artifacts" verás `spotify_tracks_csv`.
- Descarga el ZIP y extrae `spotify_tracks.csv`.

Notas importantes
- El runner es efímero: los archivos generados durante el job no aparecen automáticamente en el árbol del repo. Si quieres persistir resultados en el repo, añade un paso de commit/push con cuidado (recomiendo usar una rama `results/spotify`).
- Si las llamadas a `/v1/audio-features` devuelven 403/401, revisa las secrets (vuelve a copiar/pegar sin saltos de línea) o regenera Client Secret en el Spotify Developer Dashboard y actualiza el secret en GitHub.

Si necesitas, puedo:
- Preparar un PR que añada un paso opcional para commitear el CSV a `results/spotify`.
- Ajustar el script si en tu repo la carpeta es `src` en vez de `scr` (actualiza el path o renombra la carpeta).
