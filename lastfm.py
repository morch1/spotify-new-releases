import sys
import collections
import spotify
import pylast
from datetime import datetime, timedelta


class LastFM:
    def __init__(self, db, api_key, api_secret, username, password_hash):
        if api_key is None:
            return
            
        self.network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret, username=username, password_hash=password_hash)
        self.user = self.network.get_user(username)
        self.scrobbles = db['scrobbles']

        print('updating scrobbles...')
        print(f'{len(self.scrobbles)} total')
        
        n_new = 0
        time_from = 0 if len(self.scrobbles) == 0 else self.scrobbles[-1][0]
        time_to = int(datetime.now().timestamp())
        scrobbles_set = set(tuple(s) for s in self.scrobbles)
        while True:
            new_scrobbles = self.user.get_recent_tracks(limit=999, time_from=time_from, time_to=time_to)
            new_scrobbles = sorted(new_scrobbles, key=lambda s: -int(s.timestamp))
            if len(new_scrobbles) == 0:
                break
            for s in new_scrobbles:
                scrobble = (s.timestamp, s.track.artist.name, s.album, s.track.title)
                if scrobble not in scrobbles_set:
                    n_new += 1
                    scrobbles_set.add(scrobble)
                    self.scrobbles.append(list(scrobble))
            time_to = int(s.timestamp)
            print(f'+ {n_new} new scrobbles ({len(self.scrobbles)} total)')


    def get_scrobbles(self, ts_from=0, ts_to=sys.maxsize):
        return [s for s in self.scrobbles if ts_from <= int(s[0]) < ts_to]


    def get_top_songs(self, n, ts_from=0, ts_to=sys.maxsize):
        return collections.Counter([(s[1], s[3]) for s in self.get_scrobbles(ts_from, ts_to)]).most_common(n)
