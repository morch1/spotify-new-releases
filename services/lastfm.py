import sys
import collections
from typing import Iterable, Tuple
import pylast
import sqlite3
import time
from sqlite3.dbapi2 import Connection
from dataclasses import dataclass
from datetime import datetime, timedelta

_TABLE_SCROBBLES = 'lastfm_scrobbles'


@dataclass(frozen=True)
class Scrobble:
    timestamp: int
    artist_name: str
    track_name: str
    album_name: str = None


class LastFM:
    def __init__(self, db: Connection, api_key: str = None, api_secret: str = None, username: str = None, password_hash: str = None, update_scrobbles: bool = True):
        self.db = db
        c = db.cursor()
        c.execute(f'''CREATE TABLE IF NOT EXISTS {_TABLE_SCROBBLES} (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER, artist_name TEXT, album_name TEXT, song_name TEXT,
                UNIQUE(timestamp, artist_name, album_name, song_name)
            )''')
        db.commit()

        if (api_key is None and api_secret is None) or not update_scrobbles:
            return

        self.network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret, username=username, password_hash=password_hash)
        self.user = self.network.get_user(username)

        c.execute(f'SELECT COUNT(id), MAX(timestamp) FROM {_TABLE_SCROBBLES}')
        scrob_count, last_timestamp = c.fetchone()

        time_from = 0 if scrob_count == 0 else last_timestamp
        time_to = int(datetime.now().timestamp())
        new_scrobbles: list[Scrobble] = []

        while True:
            r = self.user.get_recent_tracks(limit=100, time_from=time_from, time_to=time_to)
            if len(r) == 0:
                break
            for s in r:
                scrobble = Scrobble(int(s.timestamp), s.track.artist.name, s.track.title, s.album)
                new_scrobbles.append(scrobble)
            time_to = s.timestamp

        n_new = 0
        for s in reversed(new_scrobbles):
            try:
                c.execute(f'INSERT INTO {_TABLE_SCROBBLES} (timestamp, artist_name, album_name, song_name) VALUES (?, ?, ?, ?)', (s.timestamp, s.artist_name, s.album_name, s.track_name))
                n_new += 1
            except sqlite3.IntegrityError:
                pass
        scrob_count += n_new

        print(f'+ {n_new} new scrobbles ({scrob_count} total)')
        db.commit()


    def get_scrobbles(self, ts_from: int = 0, ts_to: int = sys.maxsize) -> Iterable[Scrobble]:
        """
        returns a generator that yields scrobbles between ts_from and ts_to (timestamps) as Scrobble objects
        """
        c = self.db.cursor()
        c.execute(f'SELECT timestamp, artist_name, album_name, song_name FROM {_TABLE_SCROBBLES} WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp ASC', (ts_from, ts_to))
        for timestamp, artist_name, album_name, song_name in c.fetchall():
            yield Scrobble(int(timestamp), artist_name, song_name, album_name)


    def get_top_songs(self, n: int, ts_from: int = 0, ts_to: int = sys.maxsize) -> Iterable[Tuple[Tuple[str, str], int]]:
        """
        returns a list of top songs between ts_from and ts_to (timestamps) with their play counts
        """
        scrobbles = self.get_scrobbles(ts_from, ts_to)
        song_counter = collections.Counter([(s.artist_name, s.track_name) for s in scrobbles])
        return song_counter.most_common(n)
