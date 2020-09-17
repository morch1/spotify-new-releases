import os
import calendar
import pylast
import spotipy
import time
from datetime import datetime, timedelta, date


def init(parser):
    parser.add_argument('lastfm_username')
    parser.add_argument('year', type=int)
    parser.add_argument('playlist_id')


def run(token, dry, lastfm_username, year, playlist_id, **_):
    lfm_network = pylast.LastFMNetwork(api_key=os.getenv('PYLAST_API_KEY'), api_secret=os.getenv('PYLAST_API_SECRET'))
    lfm_user = lfm_network.get_user(lastfm_username)
    sp = spotipy.Spotify(auth=token)

    today = date.today()

    start = datetime(year=year, month=today.month, day=(28 if today.month == 2 and today.day == 29 and not calendar.isleap(year) else today.day))
    start_ts = calendar.timegm(start.utctimetuple())
    end = start + timedelta(days=1)
    end_ts = calendar.timegm(end.utctimetuple())

    lastfm_tracks = lfm_user.get_recent_tracks(time_from=start_ts, time_to=end_ts, limit=999)
    spotify_tracks = []

    for t in lastfm_tracks:
        time.sleep(0.1)
        sr = sp.search(q=f'artist:{t.track.artist} track:{t.track.title}', type='track', limit=1, market='PL')
        if len(sr['tracks']['items']) > 0:
            spotify_tracks.append(sr['tracks']['items'][0]['id'])
    spotify_tracks.reverse()

    if not dry:
        sp.playlist_replace_items(playlist_id, spotify_tracks)
        sp.playlist_change_details(playlist_id, description=start.strftime("%A, %B %d, %Y"))
