import progressbar
import time

_SYNC_MODES = ['update', 'update_retain_order', 'mirror']
_TABLE_SYNCED_PLAYLISTS = 'spotify_synced_playlists'


def run(config, dst_playlist_id, src_playlist_id, sync_mode, liked_only=False, readd_removed=False):
    if sync_mode not in _SYNC_MODES:
        raise ValueError('invalid sync mode')

    spotify = config.spotify
    sp = spotify.sp
    db = config.db

    c = db.cursor()
    c.execute(f'''CREATE TABLE IF NOT EXISTS {_TABLE_SYNCED_PLAYLISTS} (
            dst_playlist_id TEXT, track_id TEXT, removed INTEGER,
            PRIMARY KEY(dst_playlist_id, track_id))
        ''')
    db.commit()

    print('checking destination playlist...')
    dst_tracks = []
    songs = sp.playlist(dst_playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            dst_tracks.append(song['track']['id'])
            c.execute(f'REPLACE INTO {_TABLE_SYNCED_PLAYLISTS} (dst_playlist_id, track_id, removed) VALUES (?, ?, ?)', (dst_playlist_id, song['track']['id'], 0))
        songs = sp.next(songs) if songs['next'] else None

    c.execute(f'SELECT track_id, removed FROM {_TABLE_SYNCED_PLAYLISTS} WHERE dst_playlist_id = ?', (dst_playlist_id,))
    db_dst_tracks = dict(c.fetchall())
    for track, removed in list(db_dst_tracks.items()):
        if track not in dst_tracks and not removed:
            db_dst_tracks[track] = 1
            c.execute(f'UPDATE {_TABLE_SYNCED_PLAYLISTS} SET removed = ? WHERE dst_playlist_id = ? AND track_id = ?', (1, dst_playlist_id, track))

    print('checking source playlist...')
    src_tracks = []
    songs = sp.playlist(src_playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            if (not liked_only or spotify.is_song_liked(song['track']['artists'][0]['id'], song['track']['name'])) and (readd_removed or not db_dst_tracks.get(song['track']['id'], 0)):
                src_tracks.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    print('updating playlist...')
    if sync_mode in ['update_retain_order', 'mirror']:
        n_added, n_moved, n_removed = 0, 0, 0
        bar = progressbar.ProgressBar(maxval=len(src_tracks))
        bar.start()
        for i, track in enumerate(src_tracks):
            bar.update(i)
            c.execute(f'REPLACE INTO {_TABLE_SYNCED_PLAYLISTS} (dst_playlist_id, track_id, removed) VALUES (?, ?, ?)', (dst_playlist_id, track, 0))
            try:
                j = next(k for k, t in enumerate(dst_tracks) if t == track and k >= i)
                if j > i:
                    time.sleep(0.1)
                    sp.playlist_reorder_items(dst_playlist_id, j, i)
                    dst_tracks.insert(i, dst_tracks.pop(j))
                    n_moved += 1
            except StopIteration:
                time.sleep(1)
                sp.playlist_add_items(dst_playlist_id, [track], i)
                dst_tracks.insert(i, track)
                n_added += 1
        if sync_mode == 'mirror':
            to_remove = [{'uri': t, 'positions': [p]} for p, t in list(enumerate(dst_tracks))[len(src_tracks):]]
            n_removed = len(to_remove)
            if n_removed > 0:
                for i in range(0, len(to_remove) // 100 + 1):
                    tracks = to_remove[i * 100 : (i + 1) * 100]
                    c.executemany(f'DELETE FROM {_TABLE_SYNCED_PLAYLISTS} WHERE dst_playlist_id = ? AND track_id = ?', [(dst_playlist_id, track['uri']) for track in tracks if track not in src_tracks])
                    sp.playlist_remove_specific_occurrences_of_items(dst_playlist_id, tracks)
        bar.finish()
        print('added', n_added, 'reordered', n_moved, 'removed', n_removed)
    elif sync_mode == 'update':
        to_add = [t for t in src_tracks if t not in dst_tracks]
        if len(to_add) > 0:
            for i in range(0, len(to_add) // 100 + 1):
                tracks = to_add[i * 100 : (i + 1) * 100]
                c.executemany(f'REPLACE INTO {_TABLE_SYNCED_PLAYLISTS} (dst_playlist_id, track_id, removed) VALUES (?, ?, ?)', [(dst_playlist_id, track, 0) for track in tracks])
                sp.playlist_add_items(dst_playlist_id, tracks)
        print('added', len(to_add))
    db.commit()
