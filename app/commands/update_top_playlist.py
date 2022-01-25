from services.spotify import SpotifySearchQuery
from config import Config
from datetime import datetime

def run(config: Config, playlist_id: str, date_end: int = None, num_days: int = None, num_tracks: int = 100):
    """
    replaces playlist content with num_tracks most listened tracks in given time period (num_days days ending at date_end)
    if date_end is Null then the current date is used
    """
    sp = config.spotify
    playlist = sp.get_playlist(playlist_id)

    ts_to = date_end if date_end is not None else int(datetime.now().timestamp())
    ts_from = ts_to - (num_days * 24 * 60 * 60) if num_days is not None else 0

    print(f'loading top {num_tracks} tracks ({ts_from} - {ts_to}) from scrobble db...')
    lastfm_tracks = config.lastfm.get_top_songs(int(num_tracks * 1.2), ts_from, ts_to)

    print(f'finding tracks on spotify...')
    spotify_tracks = sp.bulk_search([SpotifySearchQuery(artist, None, track) for (artist, track), _ in lastfm_tracks], num_tracks)

    print('updating playlist...')
    playlist.replace_tracks(spotify_tracks)
