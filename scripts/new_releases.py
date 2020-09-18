import spotipy
import random
import time
import progressbar
import os
from datetime import datetime, timedelta


def init(parser):
    parser.add_argument('playlist_id')
    parser.add_argument('--num_tracks', type=int, default=30)


def run(token, dry, playlist_id, num_tracks, **_):
    sp = spotipy.Spotify(auth=token)

    print('getting followed artists...')

    followed_artists = []
    artists = sp.current_user_followed_artists()['artists']
    while artists:
        for artist in artists['items']:
            followed_artists.append(artist['id'])
        artists = sp.next(artists)['artists'] if artists['next'] else None

    print('getting playlisted tracks...')

    playlisted_albums = set()
    playlisted_tracks = []
    songs = sp.playlist(playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            playlisted_albums.add(song['track']['album']['id'])
            playlisted_tracks.append((song['track']['id'], song['track']['album']['id']))
        songs = sp.next(songs) if songs['next'] else None

    print('getting new albums...')

    bar = progressbar.ProgressBar(maxval=len(followed_artists))
    bar.start()
    new_albums = []
    for i, artist in enumerate(followed_artists):
        time.sleep(0.2)
        albums = sp.artist_albums(artist, country=os.getenv('SPOTIFY_REGION'), album_type='album,single')
        while albums:
            for album in albums['items']:
                if any(a[0] == album['id'] for a in new_albums):
                    continue
                formats = {
                    'day': '%Y-%m-%d',
                    'month': '%Y-%m',
                    'year': '%Y',
                }
                release_date = datetime.strptime(album['release_date'], formats[album['release_date_precision']])
                new_albums.append((album['id'], release_date))
            albums = sp.next(albums) if albums['next'] else None
        bar.update(i)
    new_albums = list(reversed(sorted(new_albums, key=lambda a: a[1])))[:num_tracks]
    bar.finish()

    print('getting top tracks from new albums...')

    bar = progressbar.ProgressBar(maxval=len(new_albums))
    bar.start()
    new_tracks = []
    for i, (album, release_date) in enumerate(new_albums):
        existing = [t[0] for t in playlisted_tracks if t[1] == album]
        if len(existing) > 0:
            new_tracks.append(existing[0])
        else:
            time.sleep(0.2)
            album_tracks = []
            top_track_pop = 0
            songs = sp.album_tracks(album)
            while songs:
                for song in songs['items']:
                    song = sp.track(song['id'])
                    top_track_pop = max(top_track_pop, song['popularity'])
                    album_tracks.append((song['id'], song['popularity']))
                songs = sp.next(songs) if songs['next'] else None
            new_tracks.append(random.choice([t[0] for t in album_tracks if t[1] == top_track_pop]))
        bar.update(i)
    bar.finish()

    print('updating playlist...')

    if not dry:
        sp.playlist_replace_items(playlist_id, new_tracks)
