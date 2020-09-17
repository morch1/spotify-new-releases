import os
import calendar
import pylast
import spotipy
import time
import progressbar
import json
from common import lastfm, spotify_bulk_search
from datetime import datetime, timedelta, date


def init(parser):
    parser.add_argument('year', type=int)
    parser.add_argument('playlist_id')
    parser.add_argument('db_path')


def run(token, dry, year, playlist_id, db_path, **_):
    sp = spotipy.Spotify(auth=token)

    today = date.today()

    start = datetime(year=year, month=today.month, day=(28 if today.month == 2 and today.day == 29 and not calendar.isleap(year) else today.day))
    start_ts = int(start.timestamp())
    end = start + timedelta(days=1)
    end_ts = int(end.timestamp())

    print('loading tracks from scrobble db')

    with open(db_path, 'r', encoding='utf-8') as dbf:
        lastfm_tracks = lastfm.get_scrobbles(json.load(dbf), start_ts, end_ts)

    print('finding tracks on spotify')

    spotify_tracks = spotify_bulk_search(sp, [(a, t) for (_, a, _, t) in lastfm_tracks], os.getenv('SPOTIFY_REGION'), None, True)
    spotify_tracks.reverse()

    print('updating playlist')

    if not dry:
        sp.playlist_replace_items(playlist_id, spotify_tracks)
        sp.playlist_change_details(playlist_id, description=start.strftime("%A, %B %d, %Y"))
