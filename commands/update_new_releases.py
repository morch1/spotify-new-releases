import progressbar
import time
import random
from services import Join
from datetime import datetime, timedelta

_DATE_FORMATS = {
    'day': '%Y-%m-%d',
    'month': '%Y-%m',
    'year': '%Y',
}


def shorten_track_name(name):
    return name.split(' - ')[0].split(' (')[0].split(' [')[0]


def normalize_track_name(name):
    return name.lower().replace('&', 'and').strip()


def run(config, playlist_id, num_tracks=50, newly_followed_buffer=7, include_past_releases=False):
    sp = config.spotify.sp
    db = config.spotify.db['followed_artists']

    print('getting followed artists...')
    followed_artists = {}
    artists = sp.current_user_followed_artists()['artists']
    while artists:
        for artist in artists['items']:
            if artist['id'] not in db.keys():
                db[artist['id']] = (datetime.now() - timedelta(days=newly_followed_buffer)).strftime('%Y-%m-%d')
            followed_artists[artist['id']] = artist['name']
        artists = sp.next(artists)['artists'] if artists['next'] else None

    for artist in list(db.keys()):
        if artist not in followed_artists:
            del db[artist]

    print('getting playlisted tracks...')
    playlisted_tracks = []
    songs = sp.playlist(playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            playlisted_tracks.append((song['track']['id'], song['track']['album']['id'], song['track']['artists'][0]['id'], song['track']['name'], song['track']['album']['release_date']))
        songs = sp.next(songs) if songs['next'] else None

    print('finding new tracks and albums...')
    potential_tracks = dict(((artist, track_name), (album_id, release_date, track_id)) for (track_id, album_id, artist, track_name, release_date) in playlisted_tracks)
    bar = progressbar.ProgressBar(maxval=len(followed_artists))
    bar.start()
    for i, artist in enumerate(followed_artists.keys()):
        time.sleep(0.2)
        albums = sp.artist_albums(artist, country=config.spotify.region, album_type='album,single')
        while albums:
            for album in albums['items']:
                release_date = album['release_date']
                songs = sp.album_tracks(album['id'])
                while songs:
                    for track in songs['items']:
                        track_name = normalize_track_name(track['name'])
                        if ((artist, track_name) not in potential_tracks or release_date < potential_tracks[(artist, track_name)][1]):
                            potential_tracks[(artist, track_name)] = (album['id'], release_date, track['id'])
                    songs = sp.next(songs) if songs['next'] else None
            albums = sp.next(albums) if albums['next'] else None
        albums = sp.artist_albums(artist, country=config.spotify.region, album_type='compilation')
        while albums:
            for album in albums['items']:
                release_date = album['release_date']
                songs = sp.album_tracks(album['id'])
                while songs:
                    for track in songs['items']:
                        track_name = normalize_track_name(track['name'])
                        shortname = shorten_track_name(track_name)
                        if artist in [a['id'] for a in track['artists']] and not any(artist == pt[0] and shortname == shorten_track_name(pt[1]) for pt in potential_tracks):
                            potential_tracks[(artist, shortname)] = (album['id'], release_date, track['id'])
                    songs = sp.next(songs) if songs['next'] else None
            albums = sp.next(albums) if albums['next'] else None
        albums = sp.artist_albums(artist, country=config.spotify.region, album_type='appears_on')
        while albums:
            for album in albums['items']:
                release_date = album['release_date']
                if release_date < db[artist] and not include_past_releases:
                    continue
                songs = sp.album_tracks(album['id'])
                while songs:
                    for track in songs['items']:
                        track_name = normalize_track_name(track['name'])
                        shortname = shorten_track_name(track_name)
                        if artist in [a['id'] for a in track['artists']] and not any(artist == pt[0] and shortname == shorten_track_name(pt[1]) for pt in potential_tracks):
                            potential_tracks[(artist, shortname)] = (album['id'], release_date, track['id'])
                    songs = sp.next(songs) if songs['next'] else None
            albums = sp.next(albums) if albums['next'] else None
        bar.update(i)
    potential_tracks = list(set((a, rd, t) for (artist, _), (a, rd, t) in potential_tracks.items() if rd >= db[artist] or include_past_releases))
    new_albums_set = set((album, release_date) for (album, release_date, _) in potential_tracks)
    new_albums = list(reversed(sorted([(album, release_date, [t for (a, rd, t) in potential_tracks if (a, rd) == (album, release_date)]) for (album, release_date) in new_albums_set], key=lambda a: a[1])))[:num_tracks]
    bar.finish()

    print('finding most popular tracks in new albums...')
    bar = progressbar.ProgressBar(maxval=len(new_albums))
    bar.start()
    new_tracks = []
    new_count = 0
    new_artists = set()
    for i, (album, release_date, album_track_ids) in enumerate(new_albums):
        existing = [t[0] for t in playlisted_tracks if t[1] == album]
        if len(existing) > 0:
            new_tracks.append(existing[0])
        else:
            time.sleep(0.2)
            album_tracks = []
            top_track_pop = 0
            for t in album_track_ids:
                song = sp.track(t)
                top_track_pop = max(top_track_pop, song['popularity'])
                album_tracks.append((song['id'], song['popularity'], [a['id'] for a in song['artists']]))
            album_track = random.choice([(t[0], t[2]) for t in album_tracks if t[1] == top_track_pop])
            new_tracks.append(album_track[0])
            new_count += 1
            new_artists.update({followed_artists[a] for a in album_track[1] if a in followed_artists})
        bar.update(i)
    bar.finish()

    print('updating playlist...')
    if not config.dry:
        if len(playlisted_tracks) > 0:
            sp.playlist_replace_items(playlist_id, new_tracks)
        else:
            bar = progressbar.ProgressBar(maxval=len(new_tracks))
            bar.start()
            for i, t in enumerate(reversed(new_tracks)):
                time.sleep(1)
                sp.playlist_add_items(playlist_id, [t], 0)
                bar.update(i)
            bar.finish()
    if new_count > 0:
        config.join.notify(f'New release(s)', f'{new_count} new release(s) by {", ".join(new_artists)}', Join.GROUP_NEW_RELEASES,
            config.spotify.playlist_url(playlist_id), Join.ICON_SPOTIFY)
