import argparse
import spotipy
import spotipy.util as util
from scripts import new_releases, on_repeat, on_this_day, find_common_songs, likes_playlist, remove_duplicates

SCOPE = 'playlist-read-private playlist-read-collaborative user-library-read playlist-modify-private playlist-modify-public user-follow-read'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('--dotenv', action='store_true')
    parser.add_argument('--dry', action='store_true')

    subparsers = parser.add_subparsers(dest='command')

    new_releases_parser = subparsers.add_parser('new_releases')
    new_releases_parser.add_argument('country')
    new_releases_parser.add_argument('playlist_id')
    new_releases_parser.add_argument('--num_tracks', type=int, default=30)

    on_repeat_parser = subparsers.add_parser('on_repeat')
    on_repeat_parser.add_argument('on_repeat_id')
    on_repeat_parser.add_argument('playlist_id')

    on_this_day_parser = subparsers.add_parser('on_this_day')
    on_this_day_parser.add_argument('lastfm_username')
    on_this_day_parser.add_argument('playlist_ids', nargs='+')

    find_common_songs_parser = subparsers.add_parser('find_common_songs')
    find_common_songs_parser.add_argument('playlist1')
    find_common_songs_parser.add_argument('playlist2')
    find_common_songs_parser.add_argument('--by_name', action='store_true')
    find_common_songs_parser.add_argument('--by_name_part', action='store_true')
    find_common_songs_parser.add_argument('--find_missing', action='store_true')

    likes_playlist_parser = subparsers.add_parser('likes_playlist')
    likes_playlist_parser.add_argument('playlist_id')
    likes_playlist_parser.add_argument('config_path')
    likes_playlist_parser.add_argument('--check_albums', action='store_true')
    likes_playlist_parser.add_argument('--by_name', action='store_true')
    likes_playlist_parser.add_argument('--by_name_part', action='store_true')

    remove_duplicates_parser = subparsers.add_parser('remove_duplicates')
    remove_duplicates_parser.add_argument('playlist_id')

    args = parser.parse_args()
    
    if args.dotenv:
        from dotenv import load_dotenv
        load_dotenv()

    token = util.prompt_for_user_token(args.username, SCOPE)

    if args.command == 'new_releases':
        new_releases.update(token, args.dry, args.country, args.playlist_id, args.num_tracks)
    elif args.command == 'on_repeat':
        on_repeat.update(token, args.dry, args.on_repeat_id, args.playlist_id)
    elif args.command == 'on_this_day':
        on_this_day.update(token, args.dry, args.lastfm_username, args.playlist_ids)
    elif args.command == 'find_common_songs':
        find_common_songs.run(token, args.dry, args.username, args.playlist1, args.playlist2, args.by_name, args.by_name_part, args.find_missing)
    elif args.command == 'likes_playlist':
        likes_playlist.update(token, args.dry, args.playlist_id, args.config_path, args.check_albums, args.by_name, args.by_name_part)
    elif args.command == 'remove_duplicates':
        remove_duplicates.run(token, args.dry, args.playlist_id)


if __name__ == '__main__':
    main()
