import re
from unidecode import unidecode

def normalize_name(name):
    return ' '.join(re.sub(r'[^a-zA-Z0-9 ]+', '', unidecode(name.lower().replace('&', 'and'))).split())

def shorten_name(name):
    return normalize_name(name.split(' - ')[0].split(' (')[0].split(' [')[0])
