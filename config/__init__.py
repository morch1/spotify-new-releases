class Config:
    TABLE_KV = 'kv'

    def __init__(self, db, spotify, lastfm, join):
        self.db = db
        self.spotify = spotify
        self.lastfm = lastfm
        self.join = join
        c = db.cursor()
        c.execute(f'CREATE TABLE IF NOT EXISTS {self.TABLE_KV} (k TEXT, v TEXT, PRIMARY KEY(k))')

    def set_kv(self, k, v):
        c = self.db.cursor()
        c.execute(f'REPLACE INTO {self.TABLE_KV} (k, v) values (?, ?)', (k, v))
    
    def get_kv(self, k, default=None):
        c = self.db.cursor()
        c.execute(f'SELECT v FROM {self.TABLE_KV} WHERE k = ?', ('last_notification_update',))
        return (c.fetchone() or (default,))[0]
