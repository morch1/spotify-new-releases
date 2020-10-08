import argparse
import hjson
import json
import services
from commands import COMMANDS
from pathlib import Path
from config import Config

SCOPE = 'playlist-read-private playlist-read-collaborative user-library-read playlist-modify-private playlist-modify-public user-follow-read'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file')
    parser.add_argument('--dry', action='store_true')
    args = parser.parse_args()

    with open(args.config_file, 'r', encoding='utf-8') as cf:
        config = hjson.load(cf)

    db_path = Path(config['db']['path'])
    if db_path.exists():
        if not db_path.is_file():
            raise FileExistsError('invalid db path')
        with open(db_path, 'r', encoding='utf-8') as dbf:
            db = json.load(dbf)
    else:
        db = {
            'spotify': {
                'last_notification_update': '0000-00-00T00:00:00Z',
                'followed_artists': {},
            },
            'lastfm': {
                'scrobbles': [],
            },
        }

    lastfm = services.LastFM(db['lastfm'], **config.get('lastfm', {}))
    join = services.Join(**config.get('join', {}))
    spotify = services.Spotify(db['spotify'], **config['spotify'])
    configObj = Config(args.dry, spotify, lastfm, join)

    for task in config['tasks']:
        print('>>> ', task['cmd'], task['args'])
        COMMANDS[task['cmd']](configObj, **task['args'])

    if not args.dry and not config['db'].get('readonly', False):
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f)


if __name__ == '__main__':
    main()
