import spotipy
import re
import itertools


def init(parser):
    parser.add_argument('playlist_id')


def run(token, dry, playlist_id, **_):
    sp = spotipy.Spotify(auth=token)
    remix_regex = re.compile(r".*(?: - | \(| \[)(.*)(?:remix| mix|cover|remastered|remaster|edit|live|instrumental)")

    print('getting playlisted tracks...')
    
    tracks = []
    songs = sp.playlist(playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            name = song['track']['name'].lower()
            shortname = name.split(' - ')[0].split(' (')[0].split(' [')[0]
            remix_re = re.search(remix_regex, name)
            rmxartist = remix_re.group(1) if remix_re else None
            tracks.append((song['track']['id'], song['track']['artists'][0]['name'], name, shortname, rmxartist, song['added_at'], song['added_by']['id']))
        songs = sp.next(songs) if songs['next'] else None

    print('finding duplicates...')

    duplicates = []
    for (i, (t1_id, t1_artist, t1_name, t1_short, t1_rmxartist, t1_added_at, t1_added_by)), (j, (t2_id, t2_artist, t2_name, t2_short, t2_rmxartist, t2_added_at, t2_added_by)) in itertools.product(enumerate(tracks), enumerate(tracks)):
        if i != j and t1_artist == t2_artist and t1_short == t2_short and t1_rmxartist == t2_rmxartist and t1_added_at <= t2_added_at and not any(x['uri'] == t1_id and i in x['positions'] for x in duplicates):
            duplicates.append({'uri': t2_id, 'positions': [j]})
            print(t1_added_at, t1_added_by, t1_artist, '-', t1_name)
            print(t2_added_at, t2_added_by, t2_artist, '-', t2_name, '[ DUPLICATE ]')
            print()

    print('updating playlist...')

    if not dry and len(duplicates) > 0:
        for i in range(0, len(duplicates) // 100 + 1):
            sp.playlist_remove_specific_occurrences_of_items(playlist_id, duplicates[i * 100 : (i + 1) * 100])

    print('removed', len(duplicates))
