import os
import spotipy
from datetime import datetime


def run(token, username, playlist1, playlist2, by_name, by_name_part, find_missing):
    sp = spotipy.Spotify(auth=token)

    tracks1 = {}
    common_tracks = []

    print('getting tracks from playlist 1...')

    songs = sp.playlist(playlist1)['tracks']
    while songs:
        for song in songs['items']:
            tracks1[song['track']['id']] = (song['track']['artists'][0]['id'], song['track']['name'])
        songs = sp.next(songs) if songs['next'] else None

    print('getting tracks from playlist 2 and comparing...')

    songs = sp.playlist(playlist2)['tracks']
    while songs:
        for song in songs['items']:
            on_both = song['track']['id'] in tracks1 \
                or (by_name and any(s1[0] == song['track']['artists'][0]['id'] and s1[1] == song['track']['name'] for _, s1 in tracks1.items())) \
                or (by_name_part and any(s1[0] == song['track']['artists'][0]['id'] and (s1[1].lower() in song['track']['name'].lower() or song['track']['name'].lower() in s1[1].lower()) for _, s1 in tracks1.items()))
            if (not find_missing and on_both) or (find_missing and not on_both):
                common_tracks.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    print('saving result...')

    if len(common_tracks) > 0:
        result_playlist = sp.user_playlist_create(username, f'find_common_songs result {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', public=False)
        for i in range(0, len(common_tracks) // 100 + 1):
            sp.playlist_add_items(result_playlist['id'], common_tracks[i * 100 : (i + 1) * 100])
    
    print('found', len(common_tracks))
