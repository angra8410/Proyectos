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

## Cómo ejecutar el workflow de GitHub Actions

El repositorio incluye un workflow automatizado para ingestar datos de Spotify sin necesidad de configurar un entorno local.

### Pasos para ejecutar:

1. Ve a la pestaña **Actions** en GitHub
2. Selecciona el workflow **"01-EDA — Ingest Spotify tracks (robust path + diagnostic)"**
3. Haz clic en **"Run workflow"** (botón derecho)
4. Completa los inputs:
   - **artists**: Nombres de artistas separados por comas (ejemplo: `Coldplay,Adele`)
   - **max_tracks**: Número máximo de tracks a obtener (ejemplo: `50`)
   - **playlists**: (Opcional) IDs o URLs de playlists de Spotify
5. Haz clic en **"Run workflow"** (botón verde)

### Ejemplo de inputs recomendados:
- `artists=Coldplay`
- `max_tracks=50`

### Descargar resultados:

1. Una vez que el workflow termine con éxito (✓), ve a la sección **Artifacts** al final de la página del workflow run
2. Descarga el artifact llamado **spotify_tracks_csv**
3. Descomprime el archivo ZIP para obtener `spotify_tracks.csv`

El archivo CSV contendrá las siguientes columnas principales:
- `track_id`: ID único del track en Spotify
- `track_name`: Nombre de la canción
- `artist_names`: Nombres de los artistas
- `release_date`: Fecha de lanzamiento
- `tempo`: Tempo de la canción (BPM)
- `danceability`: Nivel de bailabilidad (0.0 - 1.0)
- Y otras características de audio...

## Cómo empezar (local)

1. Crear entorno:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r 01_EDA_Canciones/requirements.txt
   ```
2. Configurar credenciales Spotify en `.env` (copia `.env.example` a `.env`)
3. Ejecutar ingesta (ejemplo con playlist pública):
   ```bash
   python 01_EDA_Canciones/scr/scripts/ingest_spotify.py --artists Coldplay --out 01_EDA_Canciones/scr/data/spotify_tracks.csv --max_tracks 200
   ```
4. Abrir notebook:
   ```bash
   jupyter lab
   # abrir 01_EDA_Canciones/notebooks/eda_songs.py
   ```

Notas
- No subir `.env` ni datos sin sanitizar.
- Si usas Authorization Code Flow más adelante registra redirect URI http://127.0.0.1:8888/callback en el dashboard de Spotify.
- El workflow de GitHub Actions maneja automáticamente las credenciales mediante GitHub Secrets

