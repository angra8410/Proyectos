#!/usr/bin/env python3
"""
Descarga metadata y audio_features desde Spotify y guarda CSV.
Soporta:
 - playlists (lista de playlist ids o URLs)
 - artistas (por nombre: toma top tracks)
 - archivo de track ids (one id per line)

Mejoras:
 - acepta playlist URL o id
 - captura errores 404 (playlist no encontrada) y no explota el proceso
 - crea la carpeta de salida relativa al script si no existe
"""
import os
import argparse
import time
import re
from typing import List
import pandas as pd
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
MAX_TRACKS = int(os.getenv("MAX_TRACKS", "2000"))

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    raise SystemExit("Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in environment or .env")

def init_spotify():
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                            client_secret=SPOTIPY_CLIENT_SECRET)
    sp = Spotify(auth_manager=auth_manager, requests_timeout=10, retries=3)
    return sp

def extract_playlist_id(input_str: str) -> str:
    """
    Dado un id o una URL/URI de playlist, devuelve solo el id.
    Examples:
      https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M -> 37i9dQZF1DXcBWIGoYBM5M
      spotify:playlist:37i9dQZF1DXcBWIGoYBM5M -> 37i9dQZF1DXcBWIGoYBM5M
    """
    if not input_str:
        return ""
    input_str = input_str.strip()
    # Buscar patrón playlist/<id>
    m = re.search(r'(?:playlist/|spotify:playlist:)([A-Za-z0-9]+)', input_str)
    if m:
        return m.group(1)
    # Si solo es un id (alfanumérico), devolverlo
    simple = re.match(r'^[A-Za-z0-9]+$', input_str)
    if simple:
        return input_str
    # Fallback: devolver lo mismo (podría fallar al llamar API)
    return input_str

def get_playlist_track_ids(sp: Spotify, playlist_id: str, limit=1000) -> List[str]:
    """
    Obtiene los track ids de una playlist.
    Maneja playlists públicas; si la playlist no existe / no es accesible devuelve [] y printa un mensaje.
    """
    pid = extract_playlist_id(playlist_id)
    if not pid:
        print(f"Invalid playlist id or url: {playlist_id}")
        return []

    track_ids = []
    try:
        results = sp.playlist_items(pid, fields='items.track.id,total,next', additional_types=['track'], limit=100)
    except SpotifyException as e:
        # Manejo explícito de 404 (no encontrada) y otros errores
        status = getattr(e, 'http_status', None)
        if status == 404 or '404' in str(e):
            print(f"Playlist not found or not accessible (404) for id/url: {playlist_id} (extracted id: {pid}). Skipping.")
            return []
        else:
            print(f"SpotifyException when fetching playlist {pid}: {e}")
            # Rethrow para errores inesperados
            raise
    except Exception as e:
        # Capturar otros errores de requests/timeout
        print(f"Error fetching playlist {pid}: {e}")
        return []

    items = results.get('items', [])
    for item in items:
        tid = item.get('track', {}).get('id')
        if tid:
            track_ids.append(tid)
        if len(track_ids) >= limit:
            break

    # páginas adicionales
    while results.get('next') and len(track_ids) < limit:
        try:
            results = sp.next(results)
        except SpotifyException as e:
            print(f"Error paginating playlist {pid}: {e}")
            break
        for item in results.get('items', []):
            tid = item.get('track', {}).get('id')
            if tid:
                track_ids.append(tid)
            if len(track_ids) >= limit:
                break
    return track_ids

def get_artist_top_tracks_by_name(sp: Spotify, artist_name: str, country='US') -> List[str]:
    results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
    items = results.get('artists', {}).get('items', [])
    if not items:
        print(f"Artist not found: {artist_name}")
        return []
    artist_id = items[0]['id']
    top = sp.artist_top_tracks(artist_id, country=country)
    return [t['id'] for t in top.get('tracks', [])]

def chunked(iterable, n):
    for i in range(0, len(iterable), n):
        yield iterable[i:i+n]

def fetch_tracks_and_features(sp: Spotify, track_ids: List[str]) -> pd.DataFrame:
    records = []
    unique_ids = list(dict.fromkeys([tid for tid in track_ids if tid]))
    if not unique_ids:
        return pd.DataFrame(records)

    # metadata
    for ids_batch in chunked(unique_ids, 50):
        retry = 0
        while True:
            try:
                tracks = sp.tracks(ids_batch).get('tracks', [])
                break
            except Exception as e:
                retry += 1
                wait = min(60, 2 ** retry)
                print(f"Error fetching tracks batch: {e}. Retry in {wait}s")
                time.sleep(wait)
        for t in tracks:
            if not t:
                continue
            track_id = t.get('id')
            name = t.get('name')
            album = t.get('album', {}).get('name')
            release_date = t.get('album', {}).get('release_date')
            artists = [a.get('name') for a in t.get('artists', [])]
            artist_ids = [a.get('id') for a in t.get('artists', [])]
            popularity = t.get('popularity')
            duration_ms = t.get('duration_ms')
            explicit = t.get('explicit')
            records.append({
                'track_id': track_id,
                'track_name': name,
                'album': album,
                'release_date': release_date,
                'artist_names': ";".join(artists),
                'artist_ids': ";".join([aid for aid in artist_ids if aid]),
                'popularity': popularity,
                'duration_ms': duration_ms,
                'explicit': explicit
            })
    df_meta = pd.DataFrame(records)
    if df_meta.empty:
        return df_meta

    # audio features
    features_list = []
    for ids_batch in chunked(df_meta['track_id'].tolist(), 100):
        retry = 0
        while True:
            try:
                feats = sp.audio_features(ids_batch)
                break
            except Exception as e:
                retry += 1
                wait = min(60, 2 ** retry)
                print(f"Error fetching audio_features: {e}. Retry in {wait}s")
                time.sleep(wait)
        features_list.extend(feats)
    df_feats = pd.DataFrame([f for f in features_list if f])
    df = df_meta.merge(df_feats, left_on='track_id', right_on='id', how='left')
    # artist genres
    artist_genres = {}
    all_artist_ids = set()
    for ids in df['artist_ids'].dropna():
        for aid in ids.split(";"):
            if aid:
                all_artist_ids.add(aid)
    for aid_chunk in chunked(list(all_artist_ids), 50):
        try:
            artists = sp.artists(aid_chunk).get('artists', [])
        except Exception as e:
            artists = []
            print(f"Warning: error fetching artist batch {aid_chunk}: {e}")
        for art in artists:
            artist_genres[art['id']] = art.get('genres', [])
    def get_primary_genre(artist_ids_str):
        if not artist_ids_str:
            return None
        for aid in artist_ids_str.split(";"):
            if aid and aid in artist_genres and artist_genres[aid]:
                return artist_genres[aid][0]
        return None
    df['primary_artist_genre'] = df['artist_ids'].apply(get_primary_genre)
    if 'id' in df.columns:
        df = df.drop(columns=['id'])
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--playlists", help="Comma separated playlist ids or URLs", default=None)
    parser.add_argument("--artists", help="Comma separated artist names", default=None)
    parser.add_argument("--track_ids_file", help="File with track ids (one per line)", default=None)
    parser.add_argument("--out", help="Output CSV path", default="src/data/spotify_tracks.csv")
    parser.add_argument("--max_tracks", type=int, default=MAX_TRACKS)
    args = parser.parse_args()

    sp = init_spotify()
    track_ids = []

    if args.playlists:
        for pid in args.playlists.split(","):
            pid = pid.strip()
            if not pid:
                continue
            print(f"Fetching playlist {pid}...")
            tids = get_playlist_track_ids(sp, pid, limit=args.max_tracks)
            print(f" -> {len(tids)} tracks")
            track_ids.extend(tids)

    if args.artists:
        for aname in args.artists.split(","):
            aname = aname.strip()
            if not aname:
                continue
            print(f"Searching top tracks for artist '{aname}'...")
            tids = get_artist_top_tracks_by_name(sp, aname)
            print(f" -> {len(tids)} tracks")
            track_ids.extend(tids)

    if args.track_ids_file:
        with open(args.track_ids_file, "r", encoding="utf8") as f:
            for line in f:
                tid = line.strip()
                if tid:
                    track_ids.append(tid)

    track_ids = list(dict.fromkeys([t for t in track_ids if t]))
    if not track_ids:
        print("No track ids collected. Exiting without error. Try using --artists or a different playlist id/url.")
        return

    if len(track_ids) > args.max_tracks:
        print(f"Truncating to max_tracks={args.max_tracks}")
        track_ids = track_ids[:args.max_tracks]

    print(f"Total unique tracks to fetch: {len(track_ids)}")
    df = fetch_tracks_and_features(sp, track_ids)

    # asegurar que la carpeta de salida existe
    out_path = args.out
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} records to {out_path}")

if __name__ == "__main__":
    main()
