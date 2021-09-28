import argparse
import hjson
import services
import sqlite3
from commands import COMMANDS
from pathlib import Path
from config import Config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file')
    args = parser.parse_args()

    with open(args.config_file, 'r', encoding='utf-8') as cf:
        config = hjson.load(cf)

    db_path = Path(config['db']['path'])
    db = sqlite3.connect(db_path)

    lastfm = services.LastFM(db, **config.get('lastfm', {}))
    join = services.Join(**config.get('join', {}))
    spotify = services.Spotify(db, **config['spotify'])
    configObj = Config(db, spotify, lastfm, join)

    for task in config['tasks']:
        print('>>> cmd: ', task['cmd'])
        print('    args: {')
        args = task.get('args', dict())
        for arg, value in args.items():
            print('      ', arg, ': ', value)
        print('}')
        print('    comment: "', task.get('comment', ''), '"')
        COMMANDS[task['cmd']](configObj, **args)

    db.close()

if __name__ == '__main__':
    main()
