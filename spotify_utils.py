import argparse
import spotipy
import spotipy.util as util
import scripts

SCOPE = 'playlist-read-private playlist-read-collaborative user-library-read playlist-modify-private playlist-modify-public user-follow-read'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('--dotenv', action='store_true')
    parser.add_argument('--dry', action='store_true')

    subparsers = parser.add_subparsers(dest='command')

    commands = scripts.init(subparsers)

    args = parser.parse_args()
    
    if args.dotenv:
        from dotenv import load_dotenv
        load_dotenv()

    token = util.prompt_for_user_token(args.username, SCOPE)

    commands[args.command](token, **vars(args))


if __name__ == '__main__':
    main()
