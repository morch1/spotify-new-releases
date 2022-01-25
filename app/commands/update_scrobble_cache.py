from config import Config

def run(config: Config):
    config.lastfm.update_scrobble_cache()
