#!/usr/bin/env python3
"""Suggest stream addresses for the stations of one city list from the Radio Browser directory.

Usage: python3 scripts/discover.py gh/accra
Prints candidates; it changes no file. Copy an address into the list by hand, after
listening to it, then run scripts/check.py. Radio Browser is a community directory: an entry can
be wrong or out of date, and it gives no right to use a station's stream.
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
API = 'https://all.api.radio-browser.info/json/stations/search?countrycode=%s&hidebroken=true&limit=1000'
UA = 'opendial-discover/1 (+https://github.com/yaasiin-ayeva/opendial)'


def key(name):
    return re.sub(r'[^a-z0-9]', '', re.sub(r'\b(fm|radio|ghana|accra|online)\b|\d+(\.\d+)?', '', name.lower()))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    place = sys.argv[1]
    data = json.load(open(os.path.join(ROOT, 'stations', place + '.json'), encoding='utf-8'))
    req = urllib.request.Request(API % data['country'], headers={'User-Agent': UA})
    found = json.load(urllib.request.urlopen(req, timeout=30))
    wanted = data['stations']
    for st in wanted:
        k = key(st['name'])
        hits = [f for f in found if k and k == key(f.get('name', ''))]
        hits.sort(key=lambda f: (not f.get('url_resolved', '').startswith('https://'), -int(f.get('votes') or 0)))
        print('\n%s (%s)' % (st['name'], st['id']))
        for f in hits[:5]:
            print('  %-5s %-4s %4s kbps  votes %-4s %s' % (
                'https' if f.get('url_resolved', '').startswith('https://') else 'http',
                f.get('codec', ''), f.get('bitrate', ''), f.get('votes', ''), f.get('url_resolved', '')))
        if not hits:
            print('  no entry with this name')


if __name__ == '__main__':
    main()
