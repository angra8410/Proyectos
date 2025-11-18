#!/usr/bin/env python3
"""
Versión con diagnóstico ampliado y manejo de 403 en audio_features.
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
import requests

load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
MAX_TRACKS = int(os.getenv("MAX_TRACKS", "2000"))

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    raise SystemExit("Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in environment or .env")

def init_spotify():
    # Diagnóstico: confirmar que las variables existen (sin imprimir valores sensibles)
    print(f"DEBUG: SPOTIPY_CLIENT_ID present_len={len(SPOTIPY_CLIENT_ID)}")
    print(f"DEBUG: SPOTIPY_CLIENT_SECRET present_len={len(SPOTIPY_CLIENT_SECRET)}")
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                            client_secret=SPOTIPY_CLIENT_SECRET)
    sp = Spotify(auth_manager=auth_manager, requests_timeout=10, retries=3)
    # Diagnóstico opcional: obtener token via curl-like (no mostrar token completo)
    try:
        token_info = auth_manager.get_access_token(as_dict=True)
        if token_info and 'access_token' in token_info:
            print(f"DEBUG: Obtained access_token length={len(token_info['access_token'])}")
    except Exception as e:
        print(f"WARNING: no token obtained via auth_manager.get_access_token(): {e}")
    return sp

# ... (misma lógica de extracción y helpers que tenías antes) ...

def extract_playlist_id(input_str: str) -> str:
    if not input_str:
        return ""
    input_str = input_str.strip()
    m = re.search(r'(?:playlist/|spotify:playlist:)([A-Za-z0-9]+)', input_str)
    if m:
        return m.group(1)
    simple = re.match(r'^[A-Za-z0-9]+$', input_str)
    if simple:
        return input_str
    return input_str

def get_playlist_track_ids(sp: Spotify, playlist_id: str, limit=1000) -> List[str]:
    pid = extract_playlist_id(playlist_id)
    if not pid:
        print(f"Invalid playlist id or url: {playlist_id}")
        return []
    track_ids = []
    try:
        results = sp.playlist_items(pid, fields='items.track.id,total,next', additional_types=['track'], limit=100)
    except SpotifyException as e:
        status = getattr(e, 'http_status', None)
        print(f"SpotifyException when fetching playlist {pid}: status={status}, msg={e}")
        if status == 404:
            print(f"Playlist not found (404): {pid}")
            return []
        raise
    except Exception as e:
        print(f"Error fetching playlist {pid}: {e}")
        return []
    items = results.get('items', [])
    for item in items:
        tid = item.get('track', {}).get('id')
        if tid:
            track_ids.append(tid)
        if len(track_ids) >= limit:
            break
    while results.get('next') and len(track_ids) < limit:
        try:
            results = sp.next(results)
        except Exception as e:
            print(f"Error paginating: {e}")
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

def try_audio_features(sp: Spotify, ids_batch: List[str], retry_on_403=True):
    """Intenta obtener audio_features, con manejo de errores y diagnóstico."""
    try:
        return sp.audio_features(ids_batch)
    except SpotifyException as e:
        status = getattr(e, 'http_status', None)
        print(f"SpotifyException audio_features: status={status}, msg={e}")
        # Si es 403 y retry_on_403=True, intentar renovar token y reintentar
        if status == 403 and retry_on_403:
            print("Got 403 Forbidden on audio_features, attempting to refresh token and retry...")
            try:
                # Crear un nuevo Spotify client con nuevo token
                auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                        client_secret=SPOTIPY_CLIENT_SECRET)
                sp_new = Spotify(auth_manager=auth_manager, requests_timeout=10, retries=3)
                # Reintentar con nuevo cliente (sin recursión infinita)
                return sp_new.audio_features(ids_batch)
            except Exception as e2:
                print(f"Retry with fresh token failed: {e2}")
        return None
    except Exception as e:
        print(f"Error calling audio_features: {e}")
        # intentemos con requests para capturar body si es un 403
        try:
            # construir token desde client credentials (requests) — no imprimir token
            resp = requests.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET),
                timeout=10
            )
            print(f"Token endpoint status: {resp.status_code}")
            if resp.status_code != 200:
                print("Token endpoint response body:", resp.text)
        except Exception as e2:
            print("Error obtaining token via requests for diagnosis:", e2)
        return None

def fetch_tracks_and_features(sp: Spotify, track_ids: List[str]) -> pd.DataFrame:
    records = []
    unique_ids = list(dict.fromkeys([tid for tid in track_ids if tid]))
    if not unique_ids:
        return pd.DataFrame(records)
    # metadata
    for ids_batch in chunked(unique_ids, 50):
        retry = 0
        max_retries = 5
        while retry < max_retries:
            try:
                tracks = sp.tracks(ids_batch).get('tracks', [])
                break
            except Exception as e:
                retry += 1
                if retry >= max_retries:
                    print(f"Error fetching tracks batch metadata after {max_retries} retries: {e}. Skipping batch.")
                    tracks = []
                    break
                wait = min(60, 2 ** retry)
                print(f"Error fetching tracks batch metadata: {e}. Retry {retry}/{max_retries} in {wait}s")
                time.sleep(wait)
        for t in tracks:
            if not t:
                continue
            records.append({
                'track_id': t.get('id'),
                'track_name': t.get('name'),
                'album': t.get('album', {}).get('name'),
                'release_date': t.get('album', {}).get('release_date'),
                'artist_names': ";".join([a.get('name') for a in t.get('artists', [])]),
                'artist_ids': ";".join([a.get('id') for a in t.get('artists', []) if a.get('id')]),
                'popularity': t.get('popularity'),
                'duration_ms': t.get('duration_ms'),
                'explicit': t.get('explicit')
            })
    df_meta = pd.DataFrame(records)
    if df_meta.empty:
        return df_meta

    # audio features: intentamos y si falla guardamos la metadata sin features
    features_rows = []
    for ids_batch in chunked(df_meta['track_id'].tolist(), 100):
        feats = try_audio_features(sp, ids_batch, retry_on_403=True)
        if feats is None:
            print("Warning: audio_features batch failed for ids:", ids_batch[:5], "...")
            # intentamos en modo batch de 1 para diagnosticar
            for tid in ids_batch:
                single = try_audio_features(sp, [tid], retry_on_403=False)
                if single:
                    features_rows.extend(single)
                else:
                    print(f"audio_features not available for track {tid}")
            # si después de intentar singles no hay features, continuamos (no fallamos)
        else:
            features_rows.extend([f for f in feats if f])
    df_feats = pd.DataFrame([f for f in features_rows if f])
    if not df_feats.empty:
        df = df_meta.merge(df_feats, left_on='track_id', right_on='id', how='left')
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
    else:
        print("No audio_features collected; returning metadata only.")
        df = df_meta
    # artist genres (intento)
    artist_genres = {}
    all_artist_ids = set()
    for ids in df.get('artist_ids', pd.Series()).dropna():
        for aid in str(ids).split(";"):
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
    df['primary_artist_genre'] = df.get('artist_ids', pd.Series()).apply(get_primary_genre)
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
        with open(args.track_ids_file, "r", encoding='utf8') as f:
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

    out_path = args.out
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} records to {out_path}")

if __name__ == "__main__":
    main()
