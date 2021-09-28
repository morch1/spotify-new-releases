from config import Config
import re
import itertools

_REMIX_REGEX = re.compile(r".*(?: - | \(| \[)(.*)(?:remix| mix|cover|remastered|remaster|edit|live|instrumental)")


def run(config: Config, playlist_ids: list[str]):
    """
    removes duplicates from each playlist on playlist_ids list
    based on track names, not IDs to take different versions of same song into consideration
    (caution: pretty aggressive and not tested a whole lot so it's likely to remove more than necessary)
    """
    sp = config.spotify

    for playlist_id in playlist_ids:
        playlist = sp.get_playlist(playlist_id)

        print(f'getting tracks from playlist {playlist}...')
        tracks = []
        for song in playlist.get_tracks():
            remix_re = re.search(_REMIX_REGEX, song.normalized_name)
            rmxartist = remix_re.group(1) if remix_re else None
            tracks.append((song, rmxartist))

        print('finding duplicates...')
        duplicates = []
        for (i, (t1, t1_rmxartist)), (j, (t2, t2_rmxartist)) in itertools.product(enumerate(tracks), enumerate(tracks)):
            if i != j and t1.artists[0] == t2.artists[0] and t1.shortened_name == t2.shortened_name and t1_rmxartist == t2_rmxartist and t1.date_added <= t2.date_added and not any(dup == t1 and dup_pos == i for dup, dup_pos in duplicates):
                duplicates.append((t2, j))
                print(t1.date_added, t1.added_by, t1.artists[0], '-', t1)
                print(t2.date_added, t2.added_by, t2.artists[0], '-', t2, '[ DUPLICATE ]')

        playlist.remove_occurences_of_tracks(duplicates)
        print(playlist, len(duplicates), 'duplicates removed')
