import join


def run(config, playlist_ids):
    sp = config.spotify.sp
    username = config.spotify.username

    db = config.spotify.watched_playlists

    for playlist_id in playlist_ids:
        print(f'checking playlist {playlist_id}')
        playlist = sp.playlist(playlist_id)
        songs = playlist['tracks']
        new_playlist = playlist['id'] not in db
        current_tracks = []
        if new_playlist:
            db[playlist['id']] = []
        else:
            new_songs = 0
            added_by = set()
        while songs:
            for song in songs['items']:
                if not new_playlist and song['track']['id'] not in db[playlist['id']] and song['added_by']['id'] != username:
                    new_songs += 1
                    added_by.add(song['added_by']['id'])
                current_tracks.append(song['track']['id'])
            songs = sp.next(songs) if songs['next'] else None
        db[playlist['id']] = current_tracks
        if not new_playlist and new_songs > 0:
            added_by = [sp.user(uid)['display_name'] for uid in added_by]
            config.join.notify(f'{playlist["name"]} updated', '{new_songs} track(s) added by {", ".join(added_by)}', join.GROUP_PLAYLIST_UPDATES,
                config.spotify.playlist_url(playlist_id), join.ICON_SPOTIFY)
