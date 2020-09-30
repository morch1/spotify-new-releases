import sys
import collections
import pylast
from datetime import datetime, timedelta


class LastFM:
    def __init__(self, db, api_key=None, api_secret=None, username=None, password_hash=None, update_scrobbles=True):
        self.scrobbles = db['scrobbles']

        if (api_key is None and api_secret is None) or not update_scrobbles:
            return
            
        self.network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret, username=username, password_hash=password_hash)
        self.user = self.network.get_user(username)

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
        return sorted([s for s in self.scrobbles if ts_from <= int(s[0]) < ts_to], key=lambda s: s[0])


    def get_top_songs(self, n, ts_from=0, ts_to=sys.maxsize):
        scrobbles = self.get_scrobbles(ts_from, ts_to)
        song_counter = collections.Counter([(s[1], s[3]) for s in scrobbles])
        song_max = song_counter.most_common(1)[0][1]
        artist_counter = collections.Counter([s[1] for s in scrobbles])
        artist_max = artist_counter.most_common(1)[0][1]
        days_counter = collections.Counter(dict(((artist, song), len(set(datetime.fromtimestamp(int(s[0])).strftime('%Y%m%d') for s in scrobbles if (s[1], s[3]) == (artist, song)))) for (artist, song) in song_counter))
        days_max = days_counter.most_common(1)[0][1]
        scores = {}
        for (artist, song), count in song_counter.items():
            scores[(artist, song)] = int(((count / song_max) * 0.8 + (days_counter[(artist, song)] / days_max) * 0.15 + (artist_counter[artist] / artist_max) * 0.05) * 100000)
        return collections.Counter(scores).most_common(n)
