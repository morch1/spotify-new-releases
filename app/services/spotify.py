import time
import spotipy
import util
from collections import defaultdict
from sqlite3.dbapi2 import Connection
from typing import Iterable, Tuple
from dataclasses import dataclass
from spotipy.oauth2 import SpotifyOAuth

AUTH_SCOPE = 'playlist-read-private playlist-read-collaborative user-library-read playlist-modify-private playlist-modify-public user-follow-read'

ICON_SPOTIFY = 'https%3A%2F%2Fwww.iconsdb.com%2Ficons%2Fdownload%2Fwhite%2Fspotify-64.png'

JOIN_GROUP_PLAYLIST_UPDATES = 'Spotify - playlist updates'
JOIN_GROUP_NEW_RELEASES = 'Spotify - new releases'

ALBUM_TYPE_ALBUM = 'album'
ALBUM_TYPE_SINGLE = 'single'
ALBUM_TYPE_COMPILATION = 'compilation'
ALBUM_TYPE_APPEARS_ON = 'appears_on'


@dataclass(eq=False)
class SpotifyObject:
    spotify: 'Spotify'
    data: dict

    def __post_init__(self):
        self.id = self.data.get('id', None)
        self.name = self.data.get('name', None)

    @property
    def normalized_name(self) -> str:
        return util.normalize_name(self.name)

    @property
    def shortened_name(self) -> str:
        return util.shorten_name(self.name)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, str):
            return self.id == o
        elif isinstance(o, SpotifyObject):
            return self.id == o.id
        else:
            return super().__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name


@dataclass(eq=False)
class SpotifyUser(SpotifyObject):
    def __post_init__(self):
        super().__post_init__()
        self.name = self.data['display_name']


@dataclass(eq=False)
class SpotifyArtist(SpotifyObject):
    def get_albums(self, types: Iterable[str]) -> Iterable['SpotifyAlbum']:
        for album in self.spotify.iterate(self.spotify.sp.artist_albums(self.id, album_type=','.join(types), country=self.spotify.region)):
            yield SpotifyAlbum(self.spotify, album)


@dataclass(eq=False)
class SpotifyTrack(SpotifyObject):
    def __post_init__(self):
        super().__post_init__()
        self.artists = [SpotifyArtist(self.spotify, a) for a in self.data['artists']]
        if not hasattr(self, 'album'):
            album_data =  self.data.get('album', None)
            self.album = SpotifyAlbum(self.spotify, album_data) if album_data is not None else None
    
    @property
    def saved(self):
        return self in self.spotify.get_saved_tracks()

    @property
    def version_saved(self):
        return any(self.artists[0] == t.artists[0] and self.normalized_name == t.normalized_name for t in self.spotify.get_saved_tracks())


@dataclass(eq=False)
class SpotifyPlaylist(SpotifyObject):
    def __post_init__(self):
        super().__post_init__()
        self.description = self.data['description']
        self.is_collaborative = self.data['collaborative']
        self.owner = self.data['owner']['id']

    @property
    def url(self):
        return f'https%3A%2F%2Fopen.spotify.com%2Fplaylist%2F{self.id}'

    def edit(self, name: str = None, description: str = None):
        self.spotify.sp.playlist_change_details(self.id, name=name, description=description)
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description

    def get_tracks(self):
        for song in self.spotify.iterate(self.spotify.sp.playlist_tracks(self.id)):
            yield SpotifyPlaylistedTrack(self.spotify, song['track'], self, song['added_at'], song['added_by']['id'])

    def add_tracks(self, tracks: Iterable[SpotifyTrack], position=None):
        if len(tracks) > 0:
            for i in range(0, len(tracks) // 100 + 1):
                time.sleep(1)
                self.spotify.sp.playlist_add_items(self.id, [t.id for t in tracks[i * 100 : (i + 1) * 100] if t.id is not None], position)
    
    def replace_tracks(self, tracks: Iterable[SpotifyTrack]):
        self.spotify.sp.playlist_replace_items(self.id, (t.id for t in tracks))

    def remove_tracks(self, tracks: Iterable[SpotifyTrack]):
        if len(tracks) > 0:
            for i in range(0, len(tracks) // 100 + 1):
                time.sleep(0.2)
                self.spotify.sp.playlist_remove_all_occurrences_of_items(self.id,  [t.id for t in tracks[i * 100 : (i + 1) * 100] if t.id is not None])

    def remove_occurences_of_tracks(self, occurences: Iterable[Tuple[SpotifyTrack, int]]):
        """
        removes tracks from specified positions on playlist, as given by a list: [(track1, pos1), (track2, pos2), ...]
        """
        occ_dict = defaultdict(list)
        for t, pos in occurences:
            if t.id is not None:
                occ_dict[t.id].append(pos)
        occ_list = [{'uri': i, 'positions': p} for i, p in occ_dict.items()]
        if len(occ_list) > 0:
            for i in range(0, len(occ_list) // 100 + 1):
                time.sleep(0.2)
                self.spotify.sp.playlist_remove_specific_occurrences_of_items(self.id, occ_list[i * 100 : (i + 1) * 100])
    
    def swap_tracks(self, pos1, pos2):
        self.spotify.sp.playlist_reorder_items(self.id, pos1, pos2)


@dataclass(eq=False)
class SpotifyPlaylistedTrack(SpotifyTrack):
    playlist: SpotifyPlaylist
    date_added: str  # TODO
    added_by: str  # TODO


@dataclass(eq=False)
class SpotifyAlbum(SpotifyObject):
    def __post_init__(self):
        super().__post_init__()
        self.artists = [SpotifyArtist(self.spotify, a) for a in self.data['artists']]
        self.release_date = self.data['release_date']

    def get_tracks(self):
        for song in self.spotify.iterate(self.spotify.sp.album_tracks(self.id)):
            yield SpotifyAlbumTrack(self.spotify, song, self)


@dataclass(eq=False)
class SpotifyAlbumTrack(SpotifyTrack):
    album: SpotifyAlbum


@dataclass(frozen=True)
class SpotifySearchQuery:
    artist_name: str
    album_name: str
    track_name: str


class Spotify:
    def __init__(self, db: Connection, client_id: str, client_secret: str, region: str, username: str):
        auth_manager = SpotifyOAuth(client_id, 
                client_secret, 
                'http://localhost', 
                scope=AUTH_SCOPE, 
                username=username, 
                cache_path='/home/app/data/.spotipy-cache', 
                open_browser=False
            )
        sp = spotipy.Spotify(auth_manager=auth_manager)

        self.sp = sp
        self.username = username
        self.region = region
        self.db = db

    def iterate(self, collection, key=None):
        if key:
            collection = collection[key]
        while collection:
            for x in collection['items']:
                yield x
            collection = self.sp.next(collection) if collection['next'] else None
            if collection and key:
                collection = collection[key]

    def _try_search(self, q):
        attempt = 0
        while attempt < 5:
            try:
                return self.sp.search(q=q, type='track', limit=10, market=self.region)
            except spotipy.SpotifyException:
                attempt += 1
        return []

    def bulk_search(self, queries: Iterable[SpotifySearchQuery], limit: int = None) -> Iterable[SpotifyTrack]:
        returned = 0
        for query in queries:
            time.sleep(0.1)
            sr = self._try_search(f'artist:{query.artist_name} {query.album_name if query.album_name is not None else ""} track:{query.track_name}')
            if len(sr['tracks']['items']) == 0 and query.album_name is not None:
                sr = self._try_search(f'artist:{query.artist_name} track:{query.track_name}')
            sr2 = [s for s in sr['tracks']['items'] if s['name'] == query.track_name and query.artist_name in [a['name'] for a in s['artists']]]
            if len(sr2) == 0:
                sr2 = sr['tracks']['items']
            if len(sr2) > 0:
                returned += 1
                yield SpotifyTrack(self, sr2[0])
            if limit is not None and returned >= limit:
                return

    def get_playlist(self, playlist_id: str) -> SpotifyPlaylist:
        return SpotifyPlaylist(self, self.sp.playlist(playlist_id))

    def get_album(self, album_id: str) -> SpotifyAlbum:
        return SpotifyAlbum(self, self.sp.album(album_id))

    def get_user(self, user_id: str) -> SpotifyUser:
        return SpotifyUser(self, self.sp.user(user_id))

    @util.memoize
    def get_saved_tracks(self) -> Iterable[SpotifyTrack]:
        for song in self.iterate(self.sp.current_user_saved_tracks()):
            yield SpotifyTrack(self, song['track'])

    @util.memoize
    def get_saved_albums(self) -> Iterable[SpotifyAlbum]:
        for album in self.iterate(self.sp.current_user_saved_albums()):
            yield SpotifyAlbum(self, album['album'])

    @util.memoize
    def get_playlists(self) -> Iterable[SpotifyPlaylist]:
        for playlist in self.iterate(self.sp.user_playlists(self.username)):
            yield SpotifyPlaylist(self, playlist)

    @util.memoize
    def get_followed_artists(self) -> Iterable[SpotifyArtist]:
        for a in self.iterate(self.sp.current_user_followed_artists(), 'artists'):
            yield SpotifyArtist(self, a)

    def is_following_user(self, user_id: str) -> bool:
        return self.sp.current_user_following_users([user_id])[0]
