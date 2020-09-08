import os
import spotipy
import spotipy.util as util
from dotenv import load_dotenv


def init(parser):
    parser.add_argument('playlist_id')
    parser.add_argument('config_path')
    parser.add_argument('--check_albums', action='store_true')
    parser.add_argument('--by_name', action='store_true')
    parser.add_argument('--by_name_part', action='store_true')


def run(token, dry, playlist_id, config_path, check_albums, by_name, by_name_part, **_):
    sp = spotipy.Spotify(auth=token)

    with open(config_path, 'r') as config_file:
        other_playlists = [sp.playlist(line.strip().split()[0]) for line in config_file.readlines() if len(line.strip()) > 0]

    playlisted_tracks = {}

    if check_albums:
        print('getting tracks from saved albums...')

        saved_albums = sp.current_user_saved_albums()
        while saved_albums:
            for album in saved_albums['items']:
                for track in album['album']['tracks']['items']:
                    playlisted_tracks[track['id']] = (track['artists'][0]['id'], track['name'].lower())
            saved_albums = sp.next(saved_albums) if saved_albums['next'] else None

    print('getting tracks from playlists...')

    for gp in other_playlists:
        songs = gp['tracks']
        while songs:
            for song in songs['items']:
                playlisted_tracks[song['track']['id']] = (song['track']['artists'][0]['id'], song['track']['name'].lower())
            songs = sp.next(songs) if songs['next'] else None

    print('getting saved tracks and comparing...')

    to_add = []
    songs = sp.current_user_saved_tracks()
    while songs:
        for song in songs['items']:
            on_both = song['track']['id'] in playlisted_tracks \
                or (by_name and any(s1[0] == song['track']['artists'][0]['id'] and s1[1] == song['track']['name'].lower() for _, s1 in playlisted_tracks.items())) \
                or (by_name_part and any(s1[0] == song['track']['artists'][0]['id'] and (s1[1] in song['track']['name'].lower() or song['track']['name'].lower() in s1[1]) for _, s1 in playlisted_tracks.items()))
            if not on_both:
                to_add.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    to_remove = []
    songs = sp.playlist(playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            if song['track']['id'] in to_add:
                to_add.remove(song['track']['id'])
            else:
                to_remove.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    print('updating playlist...')

    if not dry and len(to_add) > 0:
        for i in range(0, len(to_add) // 100 + 1):
            sp.playlist_add_items(playlist_id, to_add[i * 100 : (i + 1) * 100])

    if not dry and len(to_remove) > 0:
        for i in range(0, len(to_remove) // 100 + 1):
            sp.playlist_remove_all_occurrences_of_items(playlist_id, to_remove[i * 100 : (i + 1) * 100])

    print('added', len(to_add), 'removed', len(to_remove))
