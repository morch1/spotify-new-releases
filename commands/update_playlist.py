import progressbar
import time


def run(config, playlist_id, src_playlist_id, liked_only=False):
    sp = config.spotify.sp

    print('getting playlisted tracks...')
    playlisted_tracks = []
    songs = sp.playlist(playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            playlisted_tracks.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    if liked_only:
        print('getting saved tracks...')
        liked_tracks = set()
        songs = sp.current_user_saved_tracks()
        while songs:
            for song in songs['items']:
                liked_tracks.add((song['track']['artists'][0]['id'], song['track']['name']))
            songs = sp.next(songs) if songs['next'] else None

    print('getting tracks from source playlist...')
    src_tracks = []
    songs = sp.playlist(src_playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            if not liked_only or (song['track']['artists'][0]['id'], song['track']['name']) in liked_tracks:
                src_tracks.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    print('updating playlist...')
    n_added = 0
    n_moved = 0
    bar = progressbar.ProgressBar(maxval=len(src_tracks))
    bar.start()
    for i, track in enumerate(src_tracks):
        bar.update(i)
        try:
            j = playlisted_tracks.index(track)
            if j != i:
                time.sleep(0.1)
                if not config.dry:
                    sp.playlist_reorder_items(playlist_id, j, i)
                playlisted_tracks.insert(i, playlisted_tracks.pop(j))
                n_moved += 1
        except ValueError:
            time.sleep(1)
            if not config.dry:
                sp.playlist_add_items(playlist_id, [track], i)
            playlisted_tracks.insert(i, track)
            n_added += 1
    bar.finish()
    print('added', n_added, 'reordered', n_moved)
