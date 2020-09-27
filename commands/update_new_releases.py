import progressbar
import time
import random
import join
from datetime import datetime, timedelta

_DATE_FORMATS = {
    'day': '%Y-%m-%d',
    'month': '%Y-%m',
    'year': '%Y',
}


def run(config, playlist_id, num_tracks=30, newly_followed_buffer=7):
    sp = config.spotify.sp
    db = config.spotify.db['followed_artists']

    print('getting followed artists...')
    followed_artists = []
    artists = sp.current_user_followed_artists()['artists']
    while artists:
        for artist in artists['items']:
            if artist['id'] not in db.keys():
                db[artist['id']] = (datetime.now() - timedelta(days=newly_followed_buffer)).strftime('%Y-%m-%d')
            followed_artists.append(artist['id'])
        artists = sp.next(artists)['artists'] if artists['next'] else None

    for artist in list(db.keys()):
        if artist not in followed_artists:
            del db[artist]

    print('getting playlisted tracks...')
    new_albums = []
    playlisted_tracks = []
    songs = sp.playlist(playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            album = song['track']['album']
            release_date = datetime.strptime(album['release_date'], _DATE_FORMATS[album['release_date_precision']])
            new_albums.append((album['id'], release_date, album['artists'][0]['name']))
            playlisted_tracks.append((song['track']['id'], song['track']['album']['id']))
        songs = sp.next(songs) if songs['next'] else None

    print('getting new albums...')
    bar = progressbar.ProgressBar(maxval=len(followed_artists))
    bar.start()
    for i, artist in enumerate(followed_artists):
        time.sleep(0.2)
        albums = sp.artist_albums(artist, country=config.spotify.region, album_type='album,single')
        while albums:
            for album in albums['items']:
                if any(a[0] == album['id'] for a in new_albums) or album['release_date'] < db[artist]:
                    continue
                release_date = datetime.strptime(album['release_date'], _DATE_FORMATS[album['release_date_precision']])
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
        config.join.notify(f'New release(s)', f'{new_count} new release(s) by {", ".join(new_artists)}', join.GROUP_NEW_RELEASES,
            config.spotify.playlist_url(playlist_id), join.ICON_SPOTIFY)
