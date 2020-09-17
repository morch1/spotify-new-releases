import spotipy
import json
import collections
import progressbar
import time
import os
from common import lastfm, spotify_bulk_search
from datetime import datetime, timedelta


def init(parser):
    parser.add_argument('playlist_id')
    parser.add_argument('db_path')
    parser.add_argument('--days', default=365, type=int)
    parser.add_argument('--num_tracks', default=100, type=int)


def run(token, dry, playlist_id, db_path, days, num_tracks, **_):
    sp = spotipy.Spotify(auth=token)

    start_ts = (datetime.now() - timedelta(days=days)).timestamp()


    print(f'loading top {num_tracks} tracks from scrobble db')

    with open(db_path, 'r', encoding='utf-8') as dbf:
        lastfm_tracks = lastfm.get_top_songs(json.load(dbf), int(num_tracks * 1.2), start_ts)

    print(f'finding tracks on spotify')

    spotify_tracks = spotify_bulk_search(sp, [(a, t) for (a, t), _ in lastfm_tracks], os.getenv('SPOTIFY_REGION'), num_tracks, True)

    print('updating playlist')

    if not dry:
        sp.playlist_replace_items(playlist_id, spotify_tracks)
