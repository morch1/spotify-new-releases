from services.spotify import SpotifyTrack
from config import Config

def run(config: Config, dst_playlist_id: str, ignore_suffix: str, by_name_part: bool = False):
    """
    adds to playlist_id all saved tracks that are not on any playlist that has ignore_suffix at the end of its description
    """

    sp = config.spotify

    excluded_tracks: set[SpotifyTrack] = set()

    other_playlists = (p for p in sp.get_playlists() if p.owner == sp.username and p.description.endswith(ignore_suffix))

    print('getting tracks from playlists...')
    for other_playlist in other_playlists:
        excluded_tracks.update(other_playlist.get_tracks())

    print('getting saved tracks and comparing...')
    to_add = []
    for t in sp.get_saved_tracks():
        if not t in excluded_tracks and not any(exc_t.artists[0] == t.artists[0] and exc_t.normalized_name == t.normalized_name for exc_t in excluded_tracks) \
            and not (by_name_part and any(exc_t.artists[0] == t.artists[0] and (exc_t.shortened_name in t.normalized_name or t.shortened_name in exc_t.normalized_name) for exc_t in excluded_tracks)):
            to_add.append(t)

    to_remove = []
    dst_playlist = sp.get_playlist(dst_playlist_id)
    for t in dst_playlist.get_tracks():
        if t in to_add:
            to_add.remove(t)
        else:
            to_remove.append(t)

    dst_playlist.add_tracks(to_add)
    dst_playlist.remove_tracks(to_remove)
    print(dst_playlist, len(to_add), 'added', len(to_remove), 'removed')
