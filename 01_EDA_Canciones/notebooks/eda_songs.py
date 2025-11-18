# %% [markdown]
# EDA: Perfil de canciones (Spotify audio_features + metadata)
# Abre este archivo en JupyterLab. Las celdas están separadas por bloques.

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

sns.set(style="whitegrid")
DATA_PATH = "src/data/spotify_tracks.csv"

# %%
# Cargar datos
if not os.path.exists(DATA_PATH):
    raise SystemExit(f"No encuentro {DATA_PATH}. Ejecuta src/scripts/ingest_spotify.py primero.")
df = pd.read_csv(DATA_PATH)
print("Registros:", len(df))
df.head()

# %%
# Limpieza / columnas útiles
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
df['release_year'] = df['release_date'].dt.year
df['duration_min'] = df['duration_ms'] / 60000.0
df['decade'] = (df['release_year'] // 10) * 10
df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce').fillna(0).astype(int)
df.info()

# %%
# Visualización 1: Histograma de tempo
plt.figure(figsize=(10,5))
sns.histplot(df['tempo'].dropna(), bins=60, kde=True)
plt.title("Distribución de tempo (BPM)")
plt.xlabel("Tempo (BPM)")
plt.show()

# %%
# Visualización 2: Duración por década (boxplot)
plt.figure(figsize=(12,6))
sns.boxplot(x='decade', y='duration_min', data=df[df['decade'].notna()].sort_values('decade'))
plt.xticks(rotation=45)
plt.title("Duración de canciones por década (minutos)")
plt.show()

# %%
# Visualización 3: Popularidad promedio por año (serie temporal)
pop_by_year = df.groupby('release_year')['popularity'].mean().reset_index()
plt.figure(figsize=(12,5))
sns.lineplot(data=pop_by_year, x='release_year', y='popularity')
plt.title("Popularidad promedio por año")
plt.xlabel("Año")
plt.ylabel("Popularidad (avg)")
plt.xlim(pop_by_year['release_year'].min(), pop_by_year['release_year'].max())
plt.show()

# %%
# Visualización 4: Scatter tempo vs danceability (color por genre)
sample = df.dropna(subset=['tempo', 'danceability']).copy()
top_genres = sample['primary_artist_genre'].value_counts().nlargest(6).index.tolist()
sample['genre_top'] = sample['primary_artist_genre'].where(sample['primary_artist_genre'].isin(top_genres), 'Other')
plt.figure(figsize=(10,6))
sns.scatterplot(data=sample.sample(min(2000, len(sample))), x='tempo', y='danceability', hue='genre_top', alpha=0.6)
plt.title("Tempo vs Danceability (muestra)")
plt.show()

# %%
# Visualización 5: Heatmap correlaciones entre audio_features
features = ['danceability','energy','valence','tempo','acousticness','instrumentalness','liveness','speechiness','loudness']
corr = df[features].astype(float).corr()
plt.figure(figsize=(10,8))
sns.heatmap(corr, annot=True, fmt=".2f", cmap='vlag', center=0)
plt.title("Correlación entre audio_features")
plt.show()

# %%
# Visualización 6: Top 20 artistas por cantidad de tracks en el dataset
artist_counts = df['artist_names'].str.split(';').explode().value_counts().nlargest(20)
plt.figure(figsize=(10,6))
sns.barplot(x=artist_counts.values, y=artist_counts.index)
plt.title("Top 20 artistas por número de tracks en dataset")
plt.xlabel("Número de tracks")
plt.show()

# %%
# Conclusiones rápidas
print("Resumen estadístico audio features:")
display(df[features].describe().T)
