import sys
import collections
import pylast
import sqlite3
import time
from datetime import datetime, timedelta

_TABLE_SCROBBLES = 'lastfm_scrobbles'


class LastFM:
    def __init__(self, db, api_key=None, api_secret=None, username=None, password_hash=None, update_scrobbles=True):
        self.db = db
        c = db.cursor()
        c.execute(f'''CREATE TABLE IF NOT EXISTS {_TABLE_SCROBBLES} (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER, artist_name TEXT, album_name TEXT, song_name TEXT,
                UNIQUE(timestamp, artist_name, album_name, song_name)
            )''')

        if (api_key is None and api_secret is None) or not update_scrobbles:
            return

        self.network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret, username=username, password_hash=password_hash)
        self.user = self.network.get_user(username)

        print('updating scrobbles...')

        c.execute(f'SELECT COUNT(id), MAX(timestamp) FROM {_TABLE_SCROBBLES}')
        scrob_count, last_timestamp = c.fetchone()

        time_from = 0 if scrob_count == 0 else last_timestamp
        time_to = int(datetime.now().timestamp())
        new_scrobbles = []

        while True:
            r = self.user.get_recent_tracks(limit=100, time_from=time_from, time_to=time_to)
            if len(r) == 0:
                break
            for s in r:
                scrobble = (int(s.timestamp), s.track.artist.name, s.album, s.track.title)
                new_scrobbles.append(scrobble)
            time_to = s.timestamp
            # print(len(new_scrobbles))

        n_new = 0
        for s in reversed(new_scrobbles):
            try:
                c.execute(f'INSERT INTO {_TABLE_SCROBBLES} (timestamp, artist_name, album_name, song_name) VALUES (?, ?, ?, ?)', s)
                n_new += 1
            except sqlite3.IntegrityError:
                pass
        scrob_count += n_new

        print(f'+ {n_new} new scrobbles ({scrob_count} total)')


    def get_scrobbles(self, ts_from=0, ts_to=sys.maxsize):
        c = self.db.cursor()
        c.execute(f'SELECT timestamp, artist_name, album_name, song_name FROM {_TABLE_SCROBBLES} WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp ASC', (ts_from, ts_to))
        return c.fetchall()


    def get_top_songs(self, n, ts_from=0, ts_to=sys.maxsize, scrobbles=None):
        if scrobbles is None:
            scrobbles = self.get_scrobbles(ts_from, ts_to)
        song_counter = collections.Counter([(s[1], s[3]) for s in scrobbles])
        song_max = song_counter.most_common(1)[0][1]
        artist_counter = collections.Counter([s[1] for s in scrobbles])
        artist_max = artist_counter.most_common(1)[0][1]
        days_counter = collections.Counter(dict(((artist, song), len(set(datetime.fromtimestamp(int(s[0])).strftime('%Y%m%d') for s in scrobbles if (s[1], s[3]) == (artist, song)))) for (artist, song) in song_counter))
        days_max = days_counter.most_common(1)[0][1]
        scores = {}
        for (artist, song), count in song_counter.items():
            scores[(artist, song)] = int(((count / song_max) * 0.8 + (days_counter[(artist, song)] / days_max) * 0.15 + (artist_counter[artist] / artist_max) * 0.05) * 100000)
        return collections.Counter(scores).most_common(n)
