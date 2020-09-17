import sys
import collections


def get_scrobbles(db, ts_from=0, ts_to=sys.maxsize):
    return [s for s in db if ts_from <= int(s[0]) < ts_to]

def get_top_songs(db, n, ts_from=0, ts_to=sys.maxsize):
    return collections.Counter([(s[1], s[3]) for s in get_scrobbles(db, ts_from, ts_to)]).most_common(n)
