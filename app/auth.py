import hjson
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from services.spotify import AUTH_SCOPE

def main():
    with open('/home/app/config.hjson', 'r', encoding='utf-8') as cf:
        config = hjson.load(cf)

    client_id = config['spotify']['client_id']
    client_secret = config['spotify']['client_secret']
    username = config['spotify']['username']

    auth_manager = SpotifyOAuth(
            client_id, 
            client_secret, 
            'http://localhost', 
            scope=AUTH_SCOPE, 
            username=username, 
            cache_path='/home/app/auth/.spotipy-cache', 
            open_browser=False
        )

    sp = spotipy.Spotify(auth_manager=auth_manager)
    sp.me()

    print('Auth cache generated!')


if __name__ == '__main__':
    main()
