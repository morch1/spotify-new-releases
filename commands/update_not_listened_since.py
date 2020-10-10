from datetime import datetime

def run(config, playlist_id, since, num_tracks=100):
    sp = config.spotify.sp

    print(f'loading scrobbles')
    scrobbles = config.lastfm.get_scrobbles()

    print(f'filtering')
    tracks = {}
    for [timestamp, artist, album, track] in scrobbles:
        tracks[(artist, track)] = (timestamp, album)
    
    for t in list(tracks):
        if int(tracks[t][0]) > since:
            del tracks[t]

    lastfm_tracks = config.lastfm.get_top_songs(int(num_tracks * 1.2), scrobbles=[[ts, a, alb, t] for (a, t), (ts, alb) in tracks.items()])

    # for (a, t), c in lastfm_tracks:
    #     print(a, ' - ', t, ': ', c)

    print(f'finding tracks on spotify')
    spotify_tracks = config.spotify.bulk_search([(artist, None, track) for (artist, track), _ in lastfm_tracks], num_tracks, True)

    print('updating playlist')
    sp.playlist_replace_items(playlist_id, spotify_tracks)
    print(f'added {len(spotify_tracks)}')
