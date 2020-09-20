import progressbar
import time
import spotipy
import spotipy.util as util
import random
import calendar
import re
import itertools
from join import Join
from lastfm import LastFM
from datetime import datetime, timedelta, date

AUTH_SCOPE = 'playlist-read-private playlist-read-collaborative user-library-read playlist-modify-private playlist-modify-public user-follow-read'
REMIX_REGEX = re.compile(r".*(?: - | \(| \[)(.*)(?:remix| mix|cover|remastered|remaster|edit|live|instrumental)")


class Spotify:
    def __init__(self, db, dry, lastfm: LastFM, join: Join, client_id, client_secret, redirect_uri, region, username):
        token = util.prompt_for_user_token(username, AUTH_SCOPE, client_id, client_secret, redirect_uri)
        self.sp = spotipy.Spotify(auth=token)
        self.username = username
        self.region = region
        self.db = db
        self.dry = dry
        self.lastfm = lastfm
        self.join = join


    def bulk_search(self, queries, limit=None, show_progressbar=False):
        spotify_tracks = []
        if show_progressbar:
            bar = progressbar.ProgressBar(maxval=limit if limit is not None else len(queries))
            bar.start()
        for (artist, track) in queries:
            time.sleep(0.1)
            sr = self.sp.search(q=f'artist:{artist} track:{track}', type='track', limit=1, market=self.region)
            if len(sr['tracks']['items']) > 0:
                spotify_tracks.append(sr['tracks']['items'][0]['id'])
                if limit is not None and len(spotify_tracks) == limit:
                    break
            if show_progressbar:
                bar.update(len(spotify_tracks))
        if show_progressbar:
            bar.finish()
        return spotify_tracks


    def playlist_url(self, playlist_id):
        return f'https%3A%2F%2Fopen.spotify.com%2Fplaylist%2F{playlist_id}'


    def update_new_releases(self, playlist_id, num_tracks):
        print('>>> update_new_releases')
        sp = self.sp

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
            albums = sp.artist_albums(artist, country=self.region, album_type='album,single')
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
        if not self.dry:
            sp.playlist_replace_items(playlist_id, new_tracks)
        if new_count > 0:
            self.join.notify(f'New release(s)', f'{new_count} new track(s) by {", ".join(new_artists)}', 'Spotify new releases',
                self.playlist_url(playlist_id), self.join.ICON_SPOTIFY)


    def update_on_repeat(self, playlist_id, on_repeat_id):
        print('>>> update_on_repeat')
        sp = self.sp

        print('getting playlisted tracks...')
        playlisted_tracks = []
        songs = sp.playlist(playlist_id)['tracks']
        while songs:
            for song in songs['items']:
                playlisted_tracks.append(song['track']['id'])
            songs = sp.next(songs) if songs['next'] else None

        print('getting tracks from On Repeat...')
        onrepeat_tracks = []
        songs = sp.playlist(on_repeat_id)['tracks']
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
                    if not self.dry:
                        sp.playlist_reorder_items(playlist_id, j, i)
                    playlisted_tracks.insert(i, playlisted_tracks.pop(j))
                    n_moved += 1
            except ValueError:
                time.sleep(1)
                if not self.dry:
                    sp.playlist_add_items(playlist_id, [track], i)
                playlisted_tracks.insert(i, track)
                n_added += 1
        bar.finish()
        print('added', n_added, 'reordered', n_moved)


    def update_likes_playlist(self, playlist_id, check_albums, by_name_part, other_playlists):
        print('>>> update_likes_playlist')
        sp = self.sp

        playlisted_tracks = {}

        if check_albums:
            print('getting tracks from saved albums...')
            saved_albums = sp.current_user_saved_albums()
            while saved_albums:
                for album in saved_albums['items']:
                    for track in album['album']['tracks']['items']:
                        playlisted_tracks[track['id']] = (track['artists'][0]['id'], track['name'].lower())
                saved_albums = sp.next(saved_albums) if saved_albums['next'] else None

        print('getting tracks from playlists...')
        for gpid in other_playlists:
            gp = sp.playlist(gpid)
            songs = gp['tracks']
            while songs:
                for song in songs['items']:
                    playlisted_tracks[song['track']['id']] = (song['track']['artists'][0]['id'], song['track']['name'].lower())
                songs = sp.next(songs) if songs['next'] else None

        print('getting saved tracks and comparing...')
        to_add = []
        songs = sp.current_user_saved_tracks()
        while songs:
            for song in songs['items']:
                on_both = song['track']['id'] in playlisted_tracks \
                    or any(s1[0] == song['track']['artists'][0]['id'] and s1[1] == song['track']['name'].lower() for _, s1 in playlisted_tracks.items()) \
                    or (by_name_part and any(s1[0] == song['track']['artists'][0]['id'] and (s1[1] in song['track']['name'].lower() or song['track']['name'].lower() in s1[1]) for _, s1 in playlisted_tracks.items()))
                if not on_both:
                    to_add.append(song['track']['id'])
            songs = sp.next(songs) if songs['next'] else None

        to_remove = []
        songs = sp.playlist(playlist_id)['tracks']
        while songs:
            for song in songs['items']:
                if song['track']['id'] in to_add:
                    to_add.remove(song['track']['id'])
                else:
                    to_remove.append(song['track']['id'])
            songs = sp.next(songs) if songs['next'] else None

        print('updating playlist...')
        if not self.dry:
            if len(to_add) > 0:
                for i in range(0, len(to_add) // 100 + 1):
                    sp.playlist_add_items(playlist_id, to_add[i * 100 : (i + 1) * 100])
            if len(to_remove) > 0:
                for i in range(0, len(to_remove) // 100 + 1):
                    sp.playlist_remove_all_occurrences_of_items(playlist_id, to_remove[i * 100 : (i + 1) * 100])
        print('added', len(to_add), 'removed', len(to_remove))


    def remove_duplicates(self, playlist_ids):
        print('>>> remove_duplicates')
        sp = self.sp

        for playlist_id in playlist_ids:
            print(f'checking {playlist_id}')
            print('getting playlisted tracks...')
            tracks = []
            songs = sp.playlist(playlist_id)['tracks']
            while songs:
                for song in songs['items']:
                    name = song['track']['name'].lower()
                    shortname = name.split(' - ')[0].split(' (')[0].split(' [')[0]
                    remix_re = re.search(REMIX_REGEX, name)
                    rmxartist = remix_re.group(1) if remix_re else None
                    tracks.append((song['track']['id'], song['track']['artists'][0]['name'], name, shortname, rmxartist, song['added_at'], song['added_by']['id']))
                songs = sp.next(songs) if songs['next'] else None

            print('finding duplicates...')
            duplicates = []
            for (i, (t1_id, t1_artist, t1_name, t1_short, t1_rmxartist, t1_added_at, t1_added_by)), (j, (t2_id, t2_artist, t2_name, t2_short, t2_rmxartist, t2_added_at, t2_added_by)) in itertools.product(enumerate(tracks), enumerate(tracks)):
                if i != j and t1_artist == t2_artist and t1_short == t2_short and t1_rmxartist == t2_rmxartist and t1_added_at <= t2_added_at and not any(x['uri'] == t1_id and i in x['positions'] for x in duplicates):
                    duplicates.append({'uri': t2_id, 'positions': [j]})
                    print(t1_added_at, t1_added_by, t1_artist, '-', t1_name)
                    print(t2_added_at, t2_added_by, t2_artist, '-', t2_name, '[ DUPLICATE ]')
                    print()

            print('updating playlist...')
            if not self.dry and len(duplicates) > 0:
                for i in range(0, len(duplicates) // 100 + 1):
                    sp.playlist_remove_specific_occurrences_of_items(playlist_id, duplicates[i * 100 : (i + 1) * 100])
            print('removed', len(duplicates))


    def update_top_playlist(self, playlist_id, date_end, num_days, num_tracks):
        print('>>> update_top_playlist')
        sp = self.sp

        ts_to = date_end if date_end is not None else int(datetime.now().timestamp())
        ts_from = ts_to - (num_days * 24 * 60 * 60) if num_days is not None else 0

        print(f'loading top {num_tracks} tracks ({ts_from} - {ts_to}) from scrobble db')
        lastfm_tracks = self.lastfm.get_top_songs(int(num_tracks * 1.2), ts_from, ts_to)

        print(f'finding tracks on spotify')
        spotify_tracks = self.bulk_search([(a, t) for (a, t), _ in lastfm_tracks], num_tracks, True)

        print('updating playlist')
        if not self.dry:
            sp.playlist_replace_items(playlist_id, spotify_tracks)
        print(f'added {len(spotify_tracks)}')


    def update_on_this_day(self, **playlist_ids):
        print('>>> update_on_this_day')
        sp = self.sp

        today = date.today()

        for year, playlist_id in playlist_ids.items():
            year = int(year)

            start = datetime(year=year, month=today.month, day=(28 if today.month == 2 and today.day == 29 and not calendar.isleap(year) else today.day))
            start_ts = int(start.timestamp())
            end = start + timedelta(days=1)
            end_ts = int(end.timestamp())

            print(f'loading {year} tracks from scrobble db')
            lastfm_tracks = self.lastfm.get_scrobbles(start_ts, end_ts)

            print('finding tracks on spotify')
            spotify_tracks = self.bulk_search([(a, t) for (_, a, _, t) in lastfm_tracks], None, True)
            spotify_tracks.reverse()

            print('updating playlist')
            if not self.dry:
                sp.playlist_replace_items(playlist_id, spotify_tracks)
                sp.playlist_change_details(playlist_id, description=start.strftime("%A, %B %d, %Y"))
            print(f'added {len(spotify_tracks)}')


    def update_playlist_notifications(self, playlist_ids):
        print('>>> update_playlist_notifications')
        sp = self.sp
        username = sp.me()['id']

        db = self.db['watched_playlists']

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
                self.join.notify(f'{playlist["name"]} updated', '{new_songs} track(s) added by {", ".join(added_by)}', 'Spotify playlist updates',
                    self.playlist_url(playlist_id), self.join.ICON_SPOTIFY)
