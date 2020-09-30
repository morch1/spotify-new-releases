import calendar
from datetime import datetime, date, timedelta


def run(config, **playlist_ids):
    sp = config.spotify.sp

    today = date.today()

    for year, playlist_id in playlist_ids.items():
        year = int(year)

        start = datetime(year=year, month=today.month, day=(28 if today.month == 2 and today.day == 29 and not calendar.isleap(year) else today.day))
        start_ts = int(start.timestamp())
        end = start + timedelta(days=1)
        end_ts = int(end.timestamp())

        print(f'loading {year} tracks from scrobble db')
        lastfm_tracks = config.lastfm.get_scrobbles(start_ts, end_ts)

        print('finding tracks on spotify')
        spotify_tracks = config.spotify.bulk_search([(artist, album, track) for (_, artist, album, track) in lastfm_tracks], None, True)
        spotify_tracks.reverse()

        print('updating playlist')
        if not config.dry:
            sp.playlist_replace_items(playlist_id, spotify_tracks)
            sp.playlist_change_details(playlist_id, description=start.strftime("%A, %B %d, %Y"))
        print(f'added {len(spotify_tracks)}')
