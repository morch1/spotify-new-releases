from services.spotify import ICON_SPOTIFY, JOIN_GROUP_PLAYLIST_UPDATES
from config import Config
from datetime import datetime


def run(config: Config, followed_only: bool = False):
    """
    sends a Join notification if someone added tracks to one of the user's saved or collaborative playlists
    if followed_only is True only notifies about tracks added by followed users
    """
    sp = config.spotify
    username = sp.username
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    last_notification_update = config.get_kv('last_notification_update', now)

    for playlist in sp.get_playlists():
        if playlist.owner == username and not playlist.is_collaborative or playlist.owner == 'spotify':
            continue
        print(f'checking playlist {playlist}...')
        new_songs = 0
        added_by = set()
        for t in playlist.get_tracks():
            if t.date_added >= last_notification_update and t.added_by != username and sp.is_following_user(t.added_by):
                new_songs += 1
                added_by.add(sp.get_user(t.added_by).name)
        if new_songs > 0:
            config.join.notify(playlist.name, f'{new_songs} track(s) added by {", ".join(added_by)}', JOIN_GROUP_PLAYLIST_UPDATES, playlist.url, ICON_SPOTIFY)

    config.set_kv('last_notification_update', now)
    config.db.commit()
