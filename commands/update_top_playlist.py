from datetime import datetime

def run(config, playlist_id, date_end=None, num_days=None, num_tracks=100):
    sp = config.spotify.sp

    ts_to = date_end if date_end is not None else int(datetime.now().timestamp())
    ts_from = ts_to - (num_days * 24 * 60 * 60) if num_days is not None else 0

    print(f'loading top {num_tracks} tracks ({ts_from} - {ts_to}) from scrobble db')
    lastfm_tracks = config.lastfm.get_top_songs(int(num_tracks * 1.2), ts_from, ts_to)

    print(f'finding tracks on spotify')
    spotify_tracks = config.spotify.bulk_search([(a, t) for (a, t), _ in lastfm_tracks], num_tracks, True)

    print('updating playlist')
    if not config.dry:
        sp.playlist_replace_items(playlist_id, spotify_tracks)
    print(f'added {len(spotify_tracks)}')
