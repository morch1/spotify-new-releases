from config import Config


def run(config: Config, dst_playlist_id: str, src_playlist_id: str):
    """
    for each track on src_playlist_id, adds all tracks from its album to dst_playlist_id
    """
    sp = config.spotify

    dst_playlist = sp.get_playlist(dst_playlist_id)
    src_playlist = sp.get_playlist(src_playlist_id)

    print('getting already playlisted tracks...')
    already_playlisted = set(dst_playlist.get_tracks())

    print('getting album tracks...')
    all_albums = []
    to_add = []
    for t in src_playlist.get_tracks():
        all_albums.append(t.album)
        for at in t.album.get_tracks():
            if at not in already_playlisted:
                to_add.append(at)

    to_remove = []
    for t in already_playlisted:
        if t.album not in all_albums:
            to_remove.append(t)

    dst_playlist.add_tracks(to_add)
    dst_playlist.remove_tracks(to_remove)
    print(dst_playlist, len(to_add), 'added', len(to_remove), 'removed')
