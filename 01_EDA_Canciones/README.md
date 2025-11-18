# 01 - EDA: Perfil de canciones (Spotify)

Objetivo
- Realizar un EDA reproducible con audio_features + metadata usando la Spotify API.

Entregables (MVP)
- notebooks/eda_songs.ipynb
- src/data/spotify_tracks.csv (o instrucciones para obtenerlo)
- scripts/ingest_spotify.py
- requirements.txt
- README con pasos para reproducir

Estructura interna
- src/
  - scripts/ingest_spotify.py
  - notebooks/eda_songs.ipynb
  - data/spotify_tracks.csv

Cómo empezar (local)
1. Crear entorno:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Configurar credenciales Spotify en `.env` (SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
3. Ejecutar ingesta:
   ```bash
   python src/scripts/ingest_spotify.py --playlists 37i9dQZF1DXcBWIGoYBM5M --out src/data/spotify_tracks.csv
   ```
4. Abrir notebook y ejecutar celdas.

Notas
- Trabajaremos en ramas feature/01-... y registraremos milestones en Issues.
- Mantén datos sensibles fuera del repo (.env en .gitignore).
