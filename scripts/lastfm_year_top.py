import spotipy
import json
import collections
import progressbar
import time
from common import lastfm
from datetime import datetime


def init(parser):
    parser.add_argument('year', type=int)
    parser.add_argument('playlist_id')
    parser.add_argument('db_path')
    parser.add_argument('--num_tracks', default=100, type=int)


def run(token, dry, year, playlist_id, db_path, num_tracks, **_):
    sp = spotipy.Spotify(auth=token)

    year_start_ts = int(datetime(year, 1, 1).timestamp())
    year_end_ts = int(datetime(year + 1, 1, 1).timestamp())

    print(f'loading top {num_tracks} tracks from scrobble db')

    with open(db_path, 'r', encoding='utf-8') as dbf:
        lastfm_tracks = lastfm.get_top_songs(json.load(dbf), int(num_tracks * 1.2), year_start_ts, year_end_ts)

    print(f'finding tracks on spotify')

    spotify_tracks = []
    bar = progressbar.ProgressBar(maxval=num_tracks)
    bar.start()
    for (artist, track), _ in lastfm_tracks:
        time.sleep(0.1)
        sr = sp.search(q=f'artist:{artist} track:{track}', type='track', limit=1, market='PL')
        if len(sr['tracks']['items']) > 0:
            spotify_tracks.append(sr['tracks']['items'][0]['id'])
            if len(spotify_tracks) == num_tracks:
                break
        bar.update(len(spotify_tracks))
    bar.finish()

    print('updating playlist')

    if not dry:
        sp.playlist_add_items(playlist_id, spotify_tracks)
