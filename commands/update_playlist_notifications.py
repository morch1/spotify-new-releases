import sqlite3
from services import Join
from datetime import datetime


def run(config, playlist_ids):
    sp = config.spotify.sp
    username = config.spotify.username
    db = config.spotify.db
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    c = db.cursor()
    c.execute(f'SELECT v FROM {config.TABLE_KV} WHERE k = ?', ('last_notification_update',))
    last_notification_update = (c.fetchone() or (now,))[0]

    for playlist_id in playlist_ids:
        print(f'checking playlist {playlist_id}')
        playlist = sp.playlist(playlist_id)
        songs = playlist['tracks']
        new_songs = 0
        added_by = set()
        while songs:
            for song in songs['items']:
                if song['added_at'] >= last_notification_update and song['added_by']['id'] != username:
                    new_songs += 1
                    added_by.add(song['added_by']['id'])
            songs = sp.next(songs) if songs['next'] else None
        if new_songs > 0:
            added_by = [sp.user(uid)['display_name'] for uid in added_by]
            config.join.notify(playlist["name"], f'{new_songs} track(s) added by {", ".join(added_by)}', Join.GROUP_PLAYLIST_UPDATES,
                config.spotify.playlist_url(playlist_id), Join.ICON_SPOTIFY)

    c.execute(f'REPLACE INTO {config.TABLE_KV} (k, v) values (?, ?)', ('last_notification_update', now))
