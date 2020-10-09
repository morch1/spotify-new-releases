class Config:
    TABLE_KV = 'kv'

    def __init__(self, dry, spotify, lastfm, join):
        self.dry = dry
        self.spotify = spotify
        self.lastfm = lastfm
        self.join = join
