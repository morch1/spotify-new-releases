import progressbar
import time

def spotify_bulk_search(sp, queries, country, limit=None, show_progressbar=False):
    spotify_tracks = []
    if show_progressbar:
        bar = progressbar.ProgressBar(maxval=limit if limit is not None else len(queries))
        bar.start()
    for (artist, track) in queries:
        time.sleep(0.1)
        sr = sp.search(q=f'artist:{artist} track:{track}', type='track', limit=1, market=country)
        if len(sr['tracks']['items']) > 0:
            spotify_tracks.append(sr['tracks']['items'][0]['id'])
            if limit is not None and len(spotify_tracks) == limit:
                break
        if show_progressbar:
            bar.update(len(spotify_tracks))
    if show_progressbar:
        bar.finish()
    return spotify_tracks
