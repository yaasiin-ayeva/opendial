#!/usr/bin/env python3
"""Find a working address for the stations whose stream is down or unknown.

Usage: python3 scripts/refresh.py [gh/accra ...] [--report refresh-report.md] [--allow-http]

For each station of each list (stations/<country>/<city>.json):
  1. its own addresses are tested as scripts/check.py tests them;
  2. if none is live over HTTPS, the Radio Browser directory is asked for the stations of that
     country with the same name, and each of their addresses is tested;
  3. the first one that is live over HTTPS becomes the station's `stream`. The address it replaces
     is kept in `note`, the directory entry is added to `sources`, and `verified` becomes `checked`.

Addresses are copied from the directory as they stand, never built. An address with a query string
is skipped: it usually carries a player key or a listener id. Stations that work are left alone.

The lists are edited in place; nothing is committed. The weekly workflow (.github/workflows/
refresh.yml) runs this and opens a pull request, so a person reads every change before it is merged.
Radio Browser is a community directory: an entry can be wrong, which is why this never merges itself.
"""
import argparse
import datetime
import json
import os
import urllib.request

from check import ROOT, places, probe
from discover import key

API = os.environ.get('OPENDIAL_RADIO_BROWSER', 'https://all.api.radio-browser.info')
UA = 'opendial-refresh/1 (+https://github.com/yaasiin-ayeva/opendial)'


def directory(country):
    """Every Radio Browser entry of a country, or [] when the directory cannot be reached."""
    url = '%s/json/stations/search?countrycode=%s&hidebroken=true&limit=2000' % (API, country)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)
    except Exception as e:
        print('Radio Browser unreachable for %s: %s' % (country, e))
        return []


def usable(p, allow_http):
    return p['live'] and (p['https'] or allow_http)


def candidates(station, entries):
    """(address, directory page) pairs for a station, most voted first, without query strings."""
    k = key(station['name'])
    hits = [e for e in entries if k and key(e.get('name', '')) == k]
    hits.sort(key=lambda e: -int(e.get('votes') or 0))
    seen, out = set(), []
    for e in hits:
        for url in (e.get('url_resolved'), e.get('url')):
            if url and url not in seen and '?' not in url:
                seen.add(url)
                out.append((url, 'https://www.radio-browser.info/history/%s' % e.get('stationuuid', '')))
    return out


def refresh_list(data, entries, origin, allow_http, today):
    """Repair the stations of one list in place. Returns the changes and what stays broken."""
    changed, broken = [], []
    for st in data['stations']:
        own = [u for u in [st.get('stream')] + list(st.get('backup_streams') or []) if u]
        if any(usable(probe(u, origin), allow_http) for u in own):
            continue
        found = None
        for url, page in candidates(st, entries):
            if url in own:
                continue
            if usable(probe(url, origin), allow_http):
                found = (url, page)
                break
        if not found:
            broken.append(st['name'] + (' (no address)' if not own else ''))
            continue
        old = st.get('stream') or ''
        st['stream'] = found[0]
        st['backup_streams'] = [u for u in st.get('backup_streams') or [] if u != found[0]]
        st['sources'] = list(st.get('sources') or []) + [found[1]]
        st['verified'] = 'checked'
        was = ('It replaces %s, which no longer answered.' % old) if old else 'The station had no address before.'
        st['note'] = ((st.get('note') or '').rstrip() + ' ' if st.get('note') else '') + \
            'Address taken from Radio Browser by the weekly refresh on %s and checked live over HTTPS; nobody has listened to it. %s' % (today, was)
        changed.append((st['name'], old, found[0]))
    return changed, broken


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('place', nargs='*')
    ap.add_argument('--origin', default='https://app.example')
    ap.add_argument('--allow-http', action='store_true', help='local tests only')
    ap.add_argument('--report', default='')
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    lines, total, by_country = [], 0, {}
    for place in args.place or places():
        path = os.path.join(ROOT, 'stations', place + '.json')
        data = json.load(open(path, encoding='utf-8'))
        country = data['country']
        if country not in by_country:
            by_country[country] = directory(country)
        changed, broken = refresh_list(data, by_country[country], args.origin, args.allow_http, today)
        print('%s: %d repaired, %d still without a working address' % (place, len(changed), len(broken)))
        if changed:
            total += len(changed)
            with open(path, 'w', encoding='utf-8') as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
                fh.write('\n')
        lines.append('### %s, %s' % (data['city'], data.get('country_name', country)))
        lines += ['- **%s**: `%s` replaces `%s`' % (n, new, old or 'nothing') for n, old, new in changed] or ['- No change.']
        if broken:
            lines.append('- Still without a working address: ' + ', '.join(broken) + '.')
        lines.append('')
    report = ('Weekly refresh of %s. %d address%s changed.\n\n'
              'Each new address was copied from the Radio Browser directory and answered with audio over HTTPS. '
              'Nobody has listened to it: open the listening test before merging.\n\n' % (today, total, '' if total == 1 else 'es')
              ) + '\n'.join(lines)
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as fh:
            fh.write(report)
    print('%d address%s changed' % (total, '' if total == 1 else 'es'))


if __name__ == '__main__':
    main()
