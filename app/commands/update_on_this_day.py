import calendar
from services.spotify import SpotifySearchQuery
from config import Config
from datetime import datetime, date, timedelta


def run(config: Config, **playlist_ids: dict[str, str]):
    """
    replaces playlist content with tracks you listened to on this day each year
    playlist_ids should be a dict like so:
    {
        '2016': 'playlist id',
        '2017': 'another playlist id',
        ...
    }
    """
    sp = config.spotify
    today = date.today()
    
    for year, playlist_id in playlist_ids.items():
        year = int(year)
        playlist = sp.get_playlist(playlist_id)

        start = datetime(year=year, month=today.month, day=(28 if today.month == 2 and today.day == 29 and not calendar.isleap(year) else today.day))
        start_ts = int(start.timestamp())
        end = start + timedelta(days=1)
        end_ts = int(end.timestamp())

        print(f'loading {year} tracks from scrobble db...')
        lastfm_tracks = config.lastfm.get_scrobbles(start_ts, end_ts)

        print('finding tracks on spotify...')
        spotify_tracks = sp.bulk_search(SpotifySearchQuery(scrobble.artist_name, scrobble.album_name, scrobble.track_name) for scrobble in lastfm_tracks)

        print('updating playlist...')
        playlist.replace_tracks(spotify_tracks)
        playlist.edit(description=start.strftime("%A, %B %d, %Y"))
