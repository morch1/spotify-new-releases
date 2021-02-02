import progressbar
import time
import random
import util
from services import Join
from datetime import datetime, timedelta
from selenium import webdriver

_TABLE_FOLLOWED_ARTISTS = 'spotify_followed_artists'
_TABLE_NEW_RELEASES = 'spotify_new_releases'


def get_other_users_follows(user_id, chromedriver_path):
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.headless = True
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chromeOptions)
    driver.get(f'https://open.spotify.com/user/{user_id}/following')
    elems = driver.find_elements_by_tag_name('a')
    links = [(elem.get_attribute("href"), elem.text) for elem in elems]
    driver.quit()
    return dict((link.split('/')[-1], text) for link, text in links if 'open.spotify.com/artist/' in link)


def run(config, playlist_id, num_days=30, num_tracks=None, user_id=None):
    spotify = config.spotify
    sp = spotify.sp
    db = spotify.db
    now = datetime.utcnow().strftime('%Y-%m-%d')

    if user_id is None:
        table_follow_artists = _TABLE_FOLLOWED_ARTISTS
        table_new_releases = _TABLE_NEW_RELEASES
    else:
        table_follow_artists = f'{_TABLE_FOLLOWED_ARTISTS}_{user_id}'
        table_new_releases = f'{_TABLE_NEW_RELEASES}_{user_id}'

    c = db.cursor()
    c.execute(f'CREATE TABLE IF NOT EXISTS {table_follow_artists} (id TEXT, name TEXT, PRIMARY KEY(id))')
    c.execute(f'CREATE TABLE IF NOT EXISTS {table_new_releases} (id INTEGER PRIMARY KEY AUTOINCREMENT, artist TEXT, track TEXT, album TEXT, release_date TEXT, track_name TEXT, playlisted INTEGER)')
    db.commit()

    last_releases_update = config.get_kv('last_releases_update', now)
    cutoff_date = (datetime.strptime(last_releases_update, '%Y-%m-%d') - timedelta(days=num_days)).strftime('%Y-%m-%d')

    print('getting followed artists...')
    if user_id is None:
        followed_artists = {}
        artists = sp.current_user_followed_artists()['artists']
        while artists:
            for artist in artists['items']:
                followed_artists[artist['id']] = artist['name']
            artists = sp.next(artists)['artists'] if artists['next'] else None
    else:
        followed_artists = get_other_users_follows(user_id, spotify.chromedriver_path)

    
    c.execute(f'SELECT id FROM {table_follow_artists}')
    db_followed_artists = [r[0] for r in c.fetchall()]
    for artist in db_followed_artists:
        if artist not in followed_artists:
            c.execute(f'DELETE FROM {table_follow_artists} WHERE id = ?', (artist,))
            c.execute(f'DELETE FROM {table_new_releases} WHERE artist = ?', (artist,))
    
    print('finding new tracks and albums...')
    bar = progressbar.ProgressBar(maxval=len(followed_artists))
    bar.start()
    for i, (artist, artist_name) in enumerate(followed_artists.items()):
        time.sleep(0.2)
        c.execute(f'SELECT id FROM {table_follow_artists} WHERE id = ?', (artist,))
        new_artist = c.fetchone() is None
        if new_artist:
            c.execute(f'INSERT INTO {table_follow_artists} (id, name) values (?, ?)', (artist, artist_name))
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
                        track_name = util.normalize_name(track['name'])
                        c.execute(f'SELECT release_date FROM {table_new_releases} WHERE artist = ? AND track_name = ?', (artist, track_name))
                        db_release_date = (c.fetchone() or (None,))[0]
                        if db_release_date is None or release_date < db_release_date:
                            c.execute(f'DELETE FROM {table_new_releases} WHERE artist = ? AND track_name = ?', (artist, track_name))
                            c.execute(f'INSERT INTO {table_new_releases} (artist, track, album, release_date, track_name, playlisted) VALUES (?, ?, ?, ?, ?, ?)',
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
                        track_name = util.normalize_name(track['name'])
                        short_name = util.shorten_name(track['name'])
                        c.execute(f'SELECT id FROM {table_new_releases} WHERE artist = ? AND track_name LIKE ?', (artist, short_name + '%'))
                        exists = c.fetchone() is not None
                        if not exists:
                            c.execute(f'INSERT INTO {table_new_releases} (artist, track, album, release_date, track_name, playlisted) VALUES (?, ?, ?, ?, ?, ?)',
                                (artist, track['id'], album['id'], release_date, track_name, 0))
                    songs = sp.next(songs) if songs['next'] else None
            albums = sp.next(albums) if albums['next'] else None
        bar.update(i)
    bar.finish()

    db.commit()

    c.execute(f'SELECT track, album, release_date FROM {table_new_releases} WHERE release_date > ? AND playlisted = ?', (cutoff_date, 0))
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
        c.execute(f'UPDATE {table_new_releases} SET playlisted = ? WHERE album = ?', (1, album))
        bar.update(i)
    new_tracks = [track[0] for track in reversed(sorted(new_tracks, key=lambda t: t[1]))]
    bar.finish()

    print('updating playlist...')
    if len(new_tracks) > 0:
        for i in range(0, len(new_tracks) // 100 + 1):
            sp.playlist_add_items(playlist_id, new_tracks[i * 100 : (i + 1) * 100], 0)
        if user_id is None:
            config.join.notify(f'New release(s)', f'{len(new_tracks)} new release(s) by {", ".join(new_artists)}', Join.GROUP_NEW_RELEASES,
                config.spotify.playlist_url(playlist_id), Join.ICON_SPOTIFY)

    if num_tracks is not None:
        songs = sp.playlist(playlist_id)['tracks']
        song_counter = 0
        to_remove = []
        while songs:
            for song in songs['items']:
                if song_counter >= num_tracks:
                    to_remove.append({'uri': song['track']['id'], 'positions': [song_counter]})
                song_counter += 1
            songs = sp.next(songs) if songs['next'] else None
        sp.playlist_remove_specific_occurrences_of_items(playlist_id, to_remove)
    
    config.set_kv('last_releases_update', now)
    db.commit()
