```markdown
# 01 - EDA: Perfil de canciones (Spotify)

Objetivo
- Realizar un EDA reproducible con audio_features + metadata usando la Spotify API.

Entregables (MVP)
- notebooks/eda_songs.py (celdas Jupyter)
- src/data/spotify_tracks.csv (o instrucciones para obtenerlo)
- src/scripts/ingest_spotify.py
- requirements.txt
- README con pasos para reproducir

Estructura interna
- src/
  - scripts/ingest_spotify.py
  - notebooks/eda_songs.py
  - data/spotify_tracks.csv

Cómo empezar (local)
1. Crear entorno:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r projects/01_EDA_Canciones/requirements.txt
   ```
2. Configurar credenciales Spotify en `.env` (copia `.env.example` a `.env`)
3. Ejecutar ingesta (ejemplo con playlist pública):
   ```bash
   python projects/01_EDA_Canciones/src/scripts/ingest_spotify.py --playlists 37i9dQZF1DXcBWIGoYBM5M --out projects/01_EDA_Canciones/src/data/spotify_tracks.csv --max_tracks 200
   ```
4. Abrir notebook:
   ```bash
   jupyter lab
   # abrir projects/01_EDA_Canciones/notebooks/eda_songs.py
   ```

Notas
- No subir `.env` ni datos sin sanitizar.
- Si usas Authorization Code Flow más adelante registra redirect URI http://127.0.0.1:8888/callback en el dashboard de Spotify.
