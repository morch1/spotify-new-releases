import join
from datetime import datetime


def run(config, playlist_ids):
    sp = config.spotify.sp
    username = config.spotify.username
    db = config.spotify.db

    for playlist_id in playlist_ids:
        print(f'checking playlist {playlist_id}')
        playlist = sp.playlist(playlist_id)
        songs = playlist['tracks']
        new_songs = 0
        added_by = set()
        while songs:
            for song in songs['items']:
                if song['added_at'] >= db['last_notification_update'] and song['added_by']['id'] != username:
                    new_songs += 1
                    added_by.add(song['added_by']['id'])
            songs = sp.next(songs) if songs['next'] else None
        if new_songs > 0:
            added_by = [sp.user(uid)['display_name'] for uid in added_by]
            config.join.notify(f'{playlist["name"]} updated', f'{new_songs} track(s) added by {", ".join(added_by)}', join.GROUP_PLAYLIST_UPDATES,
                config.spotify.playlist_url(playlist_id), join.ICON_SPOTIFY)

    db['last_notification_update'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
