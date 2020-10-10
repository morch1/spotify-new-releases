import argparse
import hjson
import json
import services
import sqlite3
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
    db = sqlite3.connect(db_path)

    lastfm = services.LastFM(db, **config.get('lastfm', {}))
    join = services.Join(**config.get('join', {}))
    spotify = services.Spotify(db, **config['spotify'])
    configObj = Config(args.dry, db, spotify, lastfm, join)

    for task in config['tasks']:
        print('>>> ', task['cmd'], task['args'])
        COMMANDS[task['cmd']](configObj, **task['args'])

    if not args.dry and not config['db'].get('readonly', False):
        db.commit()
    db.close()

if __name__ == '__main__':
    main()
