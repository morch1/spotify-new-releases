import sqlite3
from services import Join
from datetime import datetime


def run(config, playlist_ids):
    sp = config.spotify.sp
    username = config.spotify.username
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    last_notification_update = config.get_kv('last_notification_update', now)

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

    config.set_kv('last_notification_update', now)
    config.db.commit()
