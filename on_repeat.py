import spotipy
import time
import progressbar

class Track:
    def __init__(self, song):
        self.artist_id = song['track']['artists'][0]['id']
        self.name = song['track']['name'].lower()
        self.id = song['track']['id']

    def __hash__(self):
        return hash(self.artist_id + self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)


def update(token, on_repat_id, playlist_id, liked_only):
    sp = spotipy.Spotify(auth=token)

    if liked_only:
        print('getting saved tracks...')

        saved_tracks = set()
        songs = sp.current_user_saved_tracks()
        while songs:
            for song in songs['items']:
                saved_tracks.add(Track(song))
            songs = sp.next(songs) if songs['next'] else None

    print('getting playlisted tracks...')
    
    playlisted_tracks = []
    songs = sp.playlist(playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            playlisted_tracks.append(Track(song))
        songs = sp.next(songs) if songs['next'] else None

    print('getting tracks from On Repeat...')

    onrepeat_tracks = []
    songs = sp.playlist(on_repat_id)['tracks']
    while songs:
        for song in songs['items']:
            onrepeat_tracks.append(Track(song))
        songs = sp.next(songs) if songs['next'] else None

    print('updating playlist...')

    n_added = 0
    n_moved = 0
    
    bar = progressbar.ProgressBar(maxval=len(onrepeat_tracks))
    bar.start()
    for i, track in enumerate(onrepeat_tracks):
        bar.update(i)
        if liked_only and track not in saved_tracks:
            continue
        try:
            j = playlisted_tracks.index(track)
            # print(track.name, i, j)
            if j != i:
                time.sleep(1)
                sp.playlist_reorder_items(playlist_id, j, i)
                playlisted_tracks.insert(i, playlisted_tracks.pop(j))
                n_moved += 1
        except ValueError:
            time.sleep(1)
            sp.playlist_add_items(playlist_id, [track.id], i)
            playlisted_tracks.insert(i, track)
            n_added += 1
    bar.finish()

    print('added', n_added, 'reordered', n_moved)
