import progressbar
import time
import spotipy
import spotipy.util as util
import random
import calendar
import re
import itertools
from datetime import datetime, timedelta, date
from spotipy.oauth2 import SpotifyOAuth

_TABLE_LIKES = 'spotify_likes'
_AUTH_SCOPE = 'playlist-read-private playlist-read-collaborative user-library-read playlist-modify-private playlist-modify-public user-follow-read'


class Spotify:
    def __init__(self, db, client_id, client_secret, redirect_uri, region, username, update_likes=True, chromedriver_path=None):
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id, client_secret, redirect_uri, scope=_AUTH_SCOPE, username=username))
        self.sp = sp
        self.username = username
        self.region = region
        self.db = db
        self.chromedriver_path = chromedriver_path

        c = db.cursor()
        c.execute(f'CREATE TABLE IF NOT EXISTS {_TABLE_LIKES} (track_id TEXT, artist_id TEXT, track_name TEXT, PRIMARY KEY(track_id))')

        if not update_likes:
            return

        print('updating spotify likes...')
        liked_tracks = []
        liked_track_ids = set()
        songs = sp.current_user_saved_tracks()
        while songs:
            for song in songs['items']:
                liked_tracks.append((song['track']['id'], song['track']['artists'][0]['id'], self.normalize_track_name(song['track']['name'])))
                liked_track_ids.add(song['track']['id'])
            songs = sp.next(songs) if songs['next'] else None

        n_removed = 0
        c.execute(f'SELECT track_id FROM {_TABLE_LIKES}')
        for (t,) in c.fetchall():
            if t not in liked_track_ids:
                c.execute(f'DELETE FROM {_TABLE_LIKES} WHERE track_id = ?', (t,))
                n_removed += 1

        c.executemany(f'INSERT OR IGNORE INTO {_TABLE_LIKES} (track_id, artist_id, track_name) VALUES (?, ?, ?)', liked_tracks)
        print('added', c.rowcount, 'removed', n_removed)

    def bulk_search(self, queries, limit=None, show_progressbar=False):
        spotify_tracks = []
        if show_progressbar:
            bar = progressbar.ProgressBar(maxval=limit if limit is not None else len(queries))
            bar.start()
        for (artist, album, track) in queries:
            time.sleep(0.1)
            sr = self.sp.search(q=f'artist:{artist} {album if album is not None else ""} track:{track}', type='track', limit=10, market=self.region)
            if len(sr['tracks']['items']) == 0 and album is not None:
                sr = self.sp.search(q=f'artist:{artist} track:{track}', type='track', limit=10, market=self.region)
            sr2 = [s for s in sr['tracks']['items'] if s['name'] == track]
            if len(sr2) == 0:
                sr2 = sr['tracks']['items']
            if len(sr2) > 0:
                spotify_tracks.append(sr2[0]['id'])
                if limit is not None and len(spotify_tracks) == limit:
                    break
            if show_progressbar:
                bar.update(len(spotify_tracks))
        if show_progressbar:
            bar.finish()
        return spotify_tracks

    def playlist_url(self, playlist_id):
        return f'https%3A%2F%2Fopen.spotify.com%2Fplaylist%2F{playlist_id}'

    def shorten_track_name(self, name):
        return name.split(' - ')[0].split(' (')[0].split(' [')[0]

    def normalize_track_name(self, name):
        return name.lower().replace('&', 'and').strip()

    def is_song_liked(self, artist_id, track_name):
        c = self.db.cursor()
        c.execute(f'SELECT track_id FROM {_TABLE_LIKES} WHERE artist_id = ? AND track_name = ?', (artist_id, self.normalize_track_name(track_name)))
        return c.fetchone() is not None

    def get_likes(self):
        c = self.db.cursor()
        c.execute(f'SELECT track_id, artist_id, track_name FROM {_TABLE_LIKES}')
        return c.fetchall()
