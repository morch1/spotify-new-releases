import progressbar
import time
import random
from services import Join
from datetime import datetime, timedelta

_TABLE_FOLLOWED_ARTISTS = 'spotify_followed_artists'
_TABLE_NEW_RELEASES = 'spotify_new_releases'


def shorten_track_name(name):
    return name.split(' - ')[0].split(' (')[0].split(' [')[0]


def normalize_track_name(name):
    return name.lower().replace('&', 'and').strip()


def run(config, playlist_id, num_days=30):
    sp = config.spotify.sp
    db = config.spotify.db
    now = datetime.utcnow().strftime('%Y-%m-%d')

    c = db.cursor()
    c.execute(f'CREATE TABLE IF NOT EXISTS {_TABLE_FOLLOWED_ARTISTS} (id TEXT, name TEXT, PRIMARY KEY(id))')
    c.execute(f'CREATE TABLE IF NOT EXISTS {_TABLE_NEW_RELEASES} (id INTEGER PRIMARY KEY AUTOINCREMENT, artist TEXT, track TEXT, album TEXT, release_date TEXT, track_name TEXT, playlisted INTEGER)')
    last_releases_update = config.get_kv('last_releases_update', now)
    cutoff_date = (datetime.strptime(last_releases_update, '%Y-%m-%d') - timedelta(days=num_days)).strftime('%Y-%m-%d')

    print('getting followed artists...')
    followed_artists = {}
    artists = sp.current_user_followed_artists()['artists']
    while artists:
        for artist in artists['items']:
            followed_artists[artist['id']] = artist['name']
        artists = sp.next(artists)['artists'] if artists['next'] else None
    
    c.execute(f'SELECT id FROM {_TABLE_FOLLOWED_ARTISTS}')
    db_followed_artists = [r[0] for r in c.fetchall()]
    for artist in db_followed_artists:
        if artist not in followed_artists:
            c.execute(f'DELETE FROM {_TABLE_FOLLOWED_ARTISTS} WHERE id = ?', (artist,))
            c.execute(f'DELETE FROM {_TABLE_NEW_RELEASES} WHERE artist = ?', (artist,))
    
    print('finding new tracks and albums...')
    bar = progressbar.ProgressBar(maxval=len(followed_artists))
    bar.start()
    for i, (artist, artist_name) in enumerate(followed_artists.items()):
        time.sleep(0.2)
        c.execute(f'SELECT id FROM {_TABLE_FOLLOWED_ARTISTS} WHERE id = ?', (artist,))
        new_artist = c.fetchone() is None
        if new_artist:
            c.execute(f'INSERT INTO {_TABLE_FOLLOWED_ARTISTS} (id, name) values (?, ?)', (artist, artist_name))
        albums = sp.artist_albums(artist, country=config.spotify.region, album_type='album,single')
        while albums:
            for album in albums['items']:
                release_date = album['release_date']
                if not new_artist and release_date < cutoff_date:
                    continue
                songs = sp.album_tracks(album['id'])
                while songs:
                    for track in songs['items']:
                        if artist not in [a['id'] for a in track['artists']]:
                            continue
                        track_name = normalize_track_name(track['name'])
                        c.execute(f'SELECT release_date FROM {_TABLE_NEW_RELEASES} WHERE artist = ? AND track_name = ?', (artist, track_name))
                        db_release_date = (c.fetchone() or (None,))[0]
                        if db_release_date is None or release_date < db_release_date:
                            c.execute(f'DELETE FROM {_TABLE_NEW_RELEASES} WHERE artist = ? AND track_name = ?', (artist, track_name))
                            c.execute(f'INSERT INTO {_TABLE_NEW_RELEASES} (artist, track, album, release_date, track_name, playlisted) VALUES (?, ?, ?, ?, ?, ?)',
                                (artist, track['id'], album['id'], release_date, track_name, 0))
                    songs = sp.next(songs) if songs['next'] else None
            albums = sp.next(albums) if albums['next'] else None
        albums = sp.artist_albums(artist, country=config.spotify.region, album_type='compilation,appears_on')
        while albums:
            for album in albums['items']:
                release_date = album['release_date']
                if not new_artist and release_date < cutoff_date:
                    continue
                songs = sp.album_tracks(album['id'])
                while songs:
                    for track in songs['items']:
                        if artist not in [a['id'] for a in track['artists']]:
                            continue
                        track_name = normalize_track_name(track['name'])
                        short_name = shorten_track_name(track_name)
                        c.execute(f'SELECT id FROM {_TABLE_NEW_RELEASES} WHERE artist = ? AND track_name LIKE ?', (artist, short_name + '%'))
                        exists = c.fetchone() is not None
                        if not exists:
                            c.execute(f'INSERT INTO {_TABLE_NEW_RELEASES} (artist, track, album, release_date, track_name, playlisted) VALUES (?, ?, ?, ?, ?, ?)',
                                (artist, track['id'], album['id'], release_date, track_name, 0))
                    songs = sp.next(songs) if songs['next'] else None
            albums = sp.next(albums) if albums['next'] else None
        bar.update(i)
    bar.finish()

    c.execute(f'SELECT track, album, release_date FROM {_TABLE_NEW_RELEASES} WHERE release_date > ? AND playlisted = ?', (cutoff_date, 0))
    r = c.fetchall()
    new_albums = dict((album, (release_date, [a[0] for a in r if a[1] == album])) for album, release_date in set((a[1], a[2]) for a in r))

    print('finding most popular tracks in new albums...')
    bar = progressbar.ProgressBar(maxval=len(new_albums))
    bar.start()
    new_tracks = []
    new_artists = set()
    for i, (album, (release_date, album_track_ids)) in enumerate(new_albums.items()):
        time.sleep(0.2)
        album_tracks = []
        top_track_pop = 0
        for t in album_track_ids:
            song = sp.track(t)
            top_track_pop = max(top_track_pop, song['popularity'])
            album_tracks.append((song['id'], song['popularity'], [a['id'] for a in song['artists']]))
        album_track = random.choice([(t[0], t[2]) for t in album_tracks if t[1] == top_track_pop])
        new_tracks.append((album_track[0], release_date))
        new_artists.update({followed_artists[a] for a in album_track[1] if a in followed_artists})
        c.execute(f'UPDATE {_TABLE_NEW_RELEASES} SET playlisted = ? WHERE album = ?', (1, album))
        bar.update(i)
    new_tracks = [track[0] for track in reversed(sorted(new_tracks, key=lambda t: t[1]))]
    bar.finish()

    print('updating playlist...')
    if len(new_tracks) > 0:
        for i in range(0, len(new_tracks) // 100 + 1):
            sp.playlist_add_items(playlist_id, new_tracks[i * 100 : (i + 1) * 100], 0)
        config.join.notify(f'New release(s)', f'{len(new_tracks)} new release(s) by {", ".join(new_artists)}', Join.GROUP_NEW_RELEASES,
            config.spotify.playlist_url(playlist_id), Join.ICON_SPOTIFY)
