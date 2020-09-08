import os
import calendar
import pylast
import spotipy
from datetime import datetime, timedelta, date


def init(parser):
    parser.add_argument('lastfm_username')
    parser.add_argument('playlist_ids', nargs='+')


def run(token, dry, lastfm_username, playlist_ids, **_):
    lfm_network = pylast.LastFMNetwork(api_key=os.getenv('PYLAST_API_KEY'), api_secret=os.getenv('PYLAST_API_SECRET'))
    lfm_user = lfm_network.get_user(lastfm_username)
    sp = spotipy.Spotify(auth=token)

    today = date.today()
    przypominajka_ids = {}

    for i, y in enumerate(range(today.year - 1, today.year - len(playlist_ids) - 1, -1)):
        przypominajka_ids[y] = playlist_ids[i]

    for year, playlist_id in przypominajka_ids.items():
        print('updating', year)
        
        start = datetime(year=year, month=today.month, day=(28 if today.month == 2 and today.day == 29 and not calendar.isleap(year) else today.day))
        start_ts = calendar.timegm(start.utctimetuple())
        end = start + timedelta(days=1)
        end_ts = calendar.timegm(end.utctimetuple())

        lastfm_tracks = lfm_user.get_recent_tracks(time_from=start_ts, time_to=end_ts, limit=999)
        spotify_tracks = []

        for t in lastfm_tracks:
            sr = sp.search(q=f'artist:{t.track.artist} track:{t.track.title}', type='track', limit=1, market='PL')
            if len(sr['tracks']['items']) > 0:
                spotify_tracks.append(sr['tracks']['items'][0]['id'])
        spotify_tracks.reverse()

        if not dry:
            sp.playlist_replace_items(playlist_id, spotify_tracks)
            sp.playlist_change_details(playlist_id, description=f'nutki słuchane {start.strftime("%A, %B %d, %Y")}')
