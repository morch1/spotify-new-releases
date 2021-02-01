import progressbar
import time
import spotipy
import util
from unidecode import unidecode
from spotipy.oauth2 import SpotifyOAuth

_AUTH_SCOPE = 'playlist-read-private playlist-read-collaborative user-library-read playlist-modify-private playlist-modify-public user-follow-read'


class Spotify:
    def __init__(self, db, client_id, client_secret, redirect_uri, region, username, update_likes=True, chromedriver_path=None):
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id, client_secret, redirect_uri, scope=_AUTH_SCOPE, username=username))
        self.sp = sp
        self.username = username
        self.region = region
        self.db = db
        self.chromedriver_path = chromedriver_path

        self.liked_tracks = []
        songs = sp.current_user_saved_tracks()
        while songs:
            for song in songs['items']:
                self.liked_tracks.append(([a['id'] for a in song['track']['artists']], song['track']['id'], [a['name'] for a in song['track']['artists']], song['track']['name']))
            songs = sp.next(songs) if songs['next'] else None

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

    def is_song_liked(self, artist_id, track_name):
        for artist_ids, _, _, t_name in self.liked_tracks:
            if artist_id in artist_ids and util.normalize_name(t_name) == util.normalize_name(track_name):
                return True
        return False
