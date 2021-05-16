
def run(config, playlist_id, src_playlist_id):
    spotify = config.spotify
    sp = spotify.sp

    print('getting playlisted tracks...')

    playlisted_tracks = []
    dst_playlist = sp.playlist(playlist_id)
    songs = dst_playlist['tracks']
    while songs:
        for song in songs['items']:
            playlisted_tracks.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    print('getting album tracks...')

    all_albums = []
    to_add = []
    src_playlist = sp.playlist(src_playlist_id)
    songs = src_playlist['tracks']
    while songs:
        for song in songs['items']:
            album_id = song['track']['album']['id']
            all_albums.append(album_id)
            album_tracks = sp.album_tracks(album_id)
            while album_tracks:
                for album_track in album_tracks['items']:
                    if album_track['id'] not in playlisted_tracks:
                        to_add.append(album_track['id'])
                album_tracks = sp.next(album_tracks) if album_tracks['next'] else None
        songs = sp.next(songs) if songs['next'] else None

    to_remove = []
    songs = dst_playlist['tracks']
    while songs:
        for song in songs['items']:
            if song['track']['album']['id'] not in all_albums:
                to_remove.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    if len(to_add) > 0:
        for i in range(0, len(to_add) // 100 + 1):
            sp.playlist_add_items(playlist_id, to_add[i * 100 : (i + 1) * 100])
    if len(to_remove) > 0:
        for i in range(0, len(to_remove) // 100 + 1):
            sp.playlist_remove_all_occurrences_of_items(playlist_id, to_remove[i * 100 : (i + 1) * 100])
    print('added', len(to_add), 'removed', len(to_remove))
