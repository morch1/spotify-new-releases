import pylast
import os
import json
from pprint import pprint
from pathlib import Path
from datetime import datetime


def init(parser):
    parser.add_argument('lastfm_username')
    parser.add_argument('db_path')


def run(token, dry, lastfm_username, db_path, **_):
    lfm_network = pylast.LastFMNetwork(api_key=os.getenv('PYLAST_API_KEY'), api_secret=os.getenv('PYLAST_API_SECRET'))
    lfm_user = lfm_network.get_user(lastfm_username)
    db_path = Path(db_path)

    if db_path.exists():
        if not db_path.is_file():
            raise FileExistsError('invalid db path')
        with open(db_path, 'r', encoding='utf-8') as dbf:
            scrobbles = [tuple(s) for s in  json.load(dbf)]
            time_from = scrobbles[-1][0]
            scrobbles = set(scrobbles)
    else:
        scrobbles = set()
        time_from = 0

    print(f'loaded {len(scrobbles)} scrobbles')
    
    n_new = 0
    time_to = int(datetime.now().timestamp())
    while True:
        new_scrobbles = lfm_user.get_recent_tracks(limit=999, time_from=time_from, time_to=time_to)
        if len(new_scrobbles) == 0:
            break
        for s in new_scrobbles:
            scrobble = (s.timestamp, s.track.artist.name, s.album, s.track.title)
            if scrobble not in scrobbles:
                n_new += 1
                scrobbles.add(scrobble)
        time_to = int(s.timestamp)
        print(f'+ {n_new} new scrobbles ({len(scrobbles)} total)')

    scrobbles = sorted(scrobbles, key=lambda s: s[0])
    
    if not dry:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(scrobbles, f)

    print(f'saved {len(scrobbles)} scrobbles')
