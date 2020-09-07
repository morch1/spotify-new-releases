import argparse
import spotipy
import spotipy.util as util
from scripts import new_releases, on_repeat, on_this_day

SCOPE = 'playlist-read-private playlist-read-collaborative user-library-read playlist-modify-private playlist-modify-public user-follow-read'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('--dotenv', action='store_true')

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

    args = parser.parse_args()
    
    if args.dotenv:
        from dotenv import load_dotenv
        load_dotenv()

    token = util.prompt_for_user_token(args.username, SCOPE)

    if args.command == 'new_releases':
        new_releases.update(token, args.country, args.playlist_id, args.num_tracks)
    elif args.command == 'on_repeat':
        on_repeat.update(token, args.on_repeat_id, args.playlist_id)
    elif args.command == 'on_this_day':
        on_this_day.update(token, args.lastfm_username, args.playlist_ids)


if __name__ == '__main__':
    main()
