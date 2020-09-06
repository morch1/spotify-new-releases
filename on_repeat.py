import spotipy


def update(token, username, on_repat_id, playlist_id, liked_only):
    sp = spotipy.Spotify(auth=token)

    saved_tracks = []
    songs = sp.current_user_saved_tracks()
    while songs:
        for song in songs['items']:
            saved_tracks.append((song['track']['artists'][0]['id'], song['track']['name'].lower()))
        songs = sp.next(songs) if songs['next'] else None
    
    playlisted_tracks = set()
    songs = sp.user_playlist(username, playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            playlisted_tracks.add(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    new_tracks = set()
    songs = sp.user_playlist(username, on_repat_id)['tracks']
    while songs:
        for song in songs['items']:
            if song['track']['id'] not in playlisted_tracks and (not liked_only or any(song['track']['artists'][0]['id'] == ss[0] and (song['track']['name'].lower() in ss[1] or ss[1] in song['track']['name'].lower()) for ss in saved_tracks)):
                new_tracks.add(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    new_tracks = list(new_tracks)

    if len(new_tracks) > 0:
        for i in range(0, len(new_tracks) // 100 + 1):
            sp.user_playlist_add_tracks(username, playlist_id, new_tracks[i * 100 : (i + 1) * 100])

    print('added', len(new_tracks))
