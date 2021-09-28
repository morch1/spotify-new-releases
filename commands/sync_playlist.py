from config import Config
import time

_SYNC_MODES = ['update', 'update_retain_order', 'mirror']
_TABLE_SYNCED_PLAYLISTS = 'spotify_synced_playlists'


def run(config: Config, dst_playlist_id: str, src_playlist_id: str, sync_mode: str, liked_only: bool = False, readd_removed: bool = False):
    """
    syncs dst_playlist_id with src_playlist_id
    
    available sync_modes:
    - update: only sync additions, not removals
    - update_retain_order: only sync additions and order the destination playlist the same way the source playlist is ordered
    - mirror: sync both additions and removals and keep the order

    if liked_only=True, only saved tracks will be synced (otherwise, all tracks)

    if readd_removed=True, tracks that were removed from destination playlist will be readded to it (otherwise, removed tracks won't be readded)
    """
    if sync_mode not in _SYNC_MODES:
        raise ValueError('invalid sync mode')

    sp = config.spotify
    db = config.db

    c = db.cursor()
    c.execute(f'CREATE TABLE IF NOT EXISTS {_TABLE_SYNCED_PLAYLISTS} (dst_playlist_id TEXT, track_id TEXT, removed INTEGER, PRIMARY KEY(dst_playlist_id, track_id))')
    db.commit()

    dst_playlist = sp.get_playlist(dst_playlist_id)
    src_playlist = sp.get_playlist(src_playlist_id)

    print(f'checking destination playlist ({dst_playlist})...')
    dst_tracks = []
    for t in dst_playlist.get_tracks():
        dst_tracks.append(t)
        c.execute(f'REPLACE INTO {_TABLE_SYNCED_PLAYLISTS} (dst_playlist_id, track_id, removed) VALUES (?, ?, ?)', (dst_playlist_id, t.id, 0))

    c.execute(f'SELECT track_id, removed FROM {_TABLE_SYNCED_PLAYLISTS} WHERE dst_playlist_id = ?', (dst_playlist_id,))
    db_dst_tracks = dict(c.fetchall())
    for track, removed in list(db_dst_tracks.items()):
        if track not in dst_tracks and not removed:
            db_dst_tracks[track] = 1
            c.execute(f'UPDATE {_TABLE_SYNCED_PLAYLISTS} SET removed = ? WHERE dst_playlist_id = ? AND track_id = ?', (1, dst_playlist_id, track))

    print(f'checking source playlist ({src_playlist})...')
    src_tracks = []
    for t in src_playlist.get_tracks():
        if (not liked_only or t.version_saved) and (readd_removed or not db_dst_tracks.get(t.id, 0)):
            src_tracks.append(t)

    print('updating destination playlist...')
    if sync_mode in ['update_retain_order', 'mirror']:
        n_added, n_moved, n_removed = 0, 0, 0
        for i, track in enumerate(src_tracks):
            c.execute(f'REPLACE INTO {_TABLE_SYNCED_PLAYLISTS} (dst_playlist_id, track_id, removed) VALUES (?, ?, ?)', (dst_playlist_id, track.id, 0))
            try:
                j = next(k for k, t in enumerate(dst_tracks) if t == track and k >= i)
                if j > i:
                    time.sleep(0.1)
                    dst_playlist.swap_tracks(j, i)
                    dst_tracks.insert(i, dst_tracks.pop(j))
                    n_moved += 1
            except StopIteration:
                time.sleep(1)
                dst_playlist.add_tracks([track], i)
                dst_tracks.insert(i, track)
                n_added += 1
        if sync_mode == 'mirror':
            to_remove = [(t, p) for p, t in list(enumerate(dst_tracks))[len(src_tracks):]]
            n_removed = len(to_remove)
            c.executemany(f'DELETE FROM {_TABLE_SYNCED_PLAYLISTS} WHERE dst_playlist_id = ? AND track_id = ?', [(dst_playlist_id, t.id) for t, _ in to_remove if t not in src_tracks])
            dst_playlist.remove_occurences_of_tracks(to_remove)
        print('added', n_added, 'reordered', n_moved, 'removed', n_removed)
    elif sync_mode == 'update':
        to_add = [t for t in src_tracks if t not in dst_tracks]
        c.executemany(f'REPLACE INTO {_TABLE_SYNCED_PLAYLISTS} (dst_playlist_id, track_id, removed) VALUES (?, ?, ?)', [(dst_playlist_id, t.id, 0) for t in to_add])
        dst_playlist.add_tracks(to_add)
        print('added', len(to_add))
    db.commit()
