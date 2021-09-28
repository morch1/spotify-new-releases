import re
import functools
import itertools
from unidecode import unidecode

def normalize_name(name):
    return ' '.join(re.sub(r'[^a-zA-Z0-9 ]+', '', unidecode(name.lower().replace('&', 'and'))).split())

def shorten_name(name):
    return normalize_name(name.split(' - ')[0].split(' (')[0].split(' [')[0])

# https://stackoverflow.com/a/53437323/3814090
def memoize(f):
    cache = {}
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        k = args, frozenset(kwargs.items())
        it = cache[k] if k in cache else f(*args, **kwargs)
        cache[k], result = itertools.tee(it)
        return result
    return wrapper
