import spotipy
import json
import requests
import os
from pathlib import Path


def init(parser):
    parser.add_argument('device_ids')
    parser.add_argument('config_path')
    parser.add_argument('db_path')


def run(token, dry, device_ids, config_path, db_path, **_):
    sp = spotipy.Spotify(auth=token)
    username = sp.me()['id']

    db_path = Path(db_path)

    if db_path.exists():
        if not db_path.is_file():
            raise FileExistsError('invalid db path')
        with open(db_path, 'r', encoding='utf-8') as dbf:
            db = json.load(dbf)
    else:
        db = {}

    with open(config_path, 'r') as config_file:
        playlists = [sp.playlist(line.strip().split()[0]) for line in config_file.readlines() if len(line.strip()) > 0]

    for playlist in playlists:
        print(f'checking playlist {playlist["name"]}')
        songs = playlist['tracks']
        new_playlist = playlist['id'] not in db
        if new_playlist:
            db[playlist['id']] = []
        else:
            new_songs = 0
            added_by = set()
        while songs:
            for song in songs['items']:
                if not new_playlist and song['track']['id'] not in db[playlist['id']] and song['added_by']['id'] != username:
                    new_songs += 1
                    added_by.add(song['added_by']['id'])
                db[playlist['id']].append(song['track']['id'])
            songs = sp.next(songs) if songs['next'] else None
        if not new_playlist and new_songs > 0:
            added_by = [sp.user(uid)['display_name'] for uid in added_by]
            print(f'{new_songs} track(s) added to {playlist["name"]} by {", ".join(added_by)}')
            url = f'https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?deviceIds={device_ids}&apikey={os.getenv("JOIN_API_KEY")}' + \
                f'&url=https%3A%2F%2Fopen.spotify.com%2Fplaylist%2F{playlist["id"]}&group=Spotify playlist updates' + \
                f'&title={playlist["name"]} updated&text={new_songs} track(s) added by {", ".join(added_by)}&dismissOnTouch=true'
            requests.get(url)

    if not dry:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f)
