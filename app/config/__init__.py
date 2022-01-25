from sqlite3.dbapi2 import Connection
from services.spotify import Spotify
from services.lastfm import LastFM
from services.join import Join


_TABLE_KV = 'kv'

class Config:
    def __init__(self, db: Connection, spotify: Spotify, lastfm: LastFM, join: Join):
        self.db = db
        self.spotify = spotify
        self.lastfm = lastfm
        self.join = join
        c = db.cursor()
        c.execute(f'CREATE TABLE IF NOT EXISTS {_TABLE_KV} (k TEXT, v TEXT, PRIMARY KEY(k))')
        db.commit()

    def set_kv(self, k, v):
        c = self.db.cursor()
        c.execute(f'REPLACE INTO {_TABLE_KV} (k, v) values (?, ?)', (k, v))
    
    def get_kv(self, k, default=None):
        c = self.db.cursor()
        c.execute(f'SELECT v FROM {_TABLE_KV} WHERE k = ?', (k,))
        return (c.fetchone() or (default,))[0]
