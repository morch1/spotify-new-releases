from services.spotify import SpotifyTrack
from config import Config

def run(config: Config, dst_playlist_id: str, other_playlists: list[str], check_albums: bool = False, check_followed_artists: bool = False, by_name_part: bool = False):
    """
    adds saved tracks for which all of these conditions are met to playlist_id:
    1. the track is not on any of the other_playlists
    2. check_albums is False, or the track is not in any of the saved albums
    3. check_followed_artists is False, or the track is not by any of the followed artists
    4. by_name_part is False, or the track's name is not a part of another track's name (and vice versa) that doesn't meet these conditions by the same artist
    """
    sp = config.spotify

    excluded_tracks: set[SpotifyTrack] = set()

    if check_albums:
        print('getting tracks from saved albums...')
        for alb in sp.get_saved_albums():
            excluded_tracks.update(alb.get_tracks())
    
    if check_followed_artists:
        print('getting followed artists...')
        followed_artists = sp.get_followed_artists()

    print('getting tracks from playlists...')
    for pid in other_playlists:
        other_playlist = sp.get_playlist(pid)
        excluded_tracks.update(other_playlist.get_tracks())

    print('getting saved tracks and comparing...')
    to_add = []
    for t in sp.get_saved_tracks():
        if check_followed_artists and any(a in followed_artists for a in t.artists):
            continue
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
