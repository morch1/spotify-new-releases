import argparse
import spotipy
import spotipy.util as util
import scripts
import hjson
import json
from pathlib import Path
from spotify import Spotify
from lastfm import LastFM
from join import Join

SCOPE = 'playlist-read-private playlist-read-collaborative user-library-read playlist-modify-private playlist-modify-public user-follow-read'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file')
    parser.add_argument('--dry', action='store_true')
    args = parser.parse_args()

    with open(args.config_file, 'r', encoding='utf-8') as cf:
        config = hjson.load(cf)

    db_path = Path(config['db_path'])
    if db_path.exists():
        if not db_path.is_file():
            raise FileExistsError('invalid db path')
        with open(db_path, 'r', encoding='utf-8') as dbf:
            db = json.load(dbf)
    else:
        db = {
            'spotify': {
                'watched_playlists': {}
            },
            'lastfm': {
                'scrobbles': [],
            },
        }

    lastfm = LastFM(db['lastfm'], **config['lastfm'])
    join = Join(**config['join'])
    spotify = Spotify(db['spotify'], args.dry, lastfm, join, **config['spotify'])

    for task in config['tasks']:
        getattr(spotify, task['cmd'])(**task['args'])

    if not args.dry:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f)


if __name__ == '__main__':
    main()
