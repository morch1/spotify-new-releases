import spotipy
import time
import progressbar


def update(token, dry, on_repat_id, playlist_id):
    sp = spotipy.Spotify(auth=token)

    print('getting playlisted tracks...')
    
    playlisted_tracks = []
    songs = sp.playlist(playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            playlisted_tracks.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    print('getting tracks from On Repeat...')

    onrepeat_tracks = []
    songs = sp.playlist(on_repat_id)['tracks']
    while songs:
        for song in songs['items']:
            onrepeat_tracks.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    print('updating playlist...')

    n_added = 0
    n_moved = 0
    
    bar = progressbar.ProgressBar(maxval=len(onrepeat_tracks))
    bar.start()
    for i, track in enumerate(onrepeat_tracks):
        bar.update(i)
        try:
            j = playlisted_tracks.index(track)
            if j != i:
                time.sleep(1)
                if not dry:
                    sp.playlist_reorder_items(playlist_id, j, i)
                playlisted_tracks.insert(i, playlisted_tracks.pop(j))
                n_moved += 1
        except ValueError:
            time.sleep(1)
            if not dry:
                sp.playlist_add_items(playlist_id, track, i)
            playlisted_tracks.insert(i, track)
            n_added += 1
    bar.finish()

    print('added', n_added, 'reordered', n_moved)
