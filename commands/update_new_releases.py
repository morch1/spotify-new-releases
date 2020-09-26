import progressbar
import time
import random
import join
from datetime import datetime


def run(config, playlist_id, num_tracks):
    sp = config.spotify.sp

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
        albums = sp.artist_albums(artist, country=config.spotify.region, album_type='album,single')
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
                new_albums.append((album['id'], release_date, album['artists'][0]['name']))
            albums = sp.next(albums) if albums['next'] else None
        bar.update(i)
    new_albums = list(reversed(sorted(new_albums, key=lambda a: a[1])))[:num_tracks]
    bar.finish()

    print('getting top tracks from new albums...')
    bar = progressbar.ProgressBar(maxval=len(new_albums))
    bar.start()
    new_tracks = []
    new_count = 0
    new_artists = set()
    for i, (album, release_date, artist_name) in enumerate(new_albums):
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
            new_count += 1
            new_artists.add(artist_name)
        bar.update(i)
    bar.finish()

    print('updating playlist...')
    if not config.dry:
        sp.playlist_replace_items(playlist_id, new_tracks)
    if new_count > 0:
        config.join.notify(f'New release(s)', f'{new_count} new track(s) by {", ".join(new_artists)}', join.GROUP_NEW_RELEASES,
            config.spotify.playlist_url(playlist_id), join.ICON_SPOTIFY)
