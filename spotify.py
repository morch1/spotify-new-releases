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


class Spotify:
    def __init__(self, db, client_id, client_secret, redirect_uri, region, username):
        token = util.prompt_for_user_token(username, AUTH_SCOPE, client_id, client_secret, redirect_uri)
        self.sp = spotipy.Spotify(auth=token)
        self.username = username
        self.region = region
        self.db = db


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
