#!/usr/bin/env python3
"""Check every stream of every city list (stations/<country>/<city>.json) and publish the ones a
browser can play.

Usage: python3 scripts/check.py [gh/accra ...] [--origin https://app.example] [--allow-http] [--no-log]
With no place named, every list is checked.

For each stream it opens the address as a browser would, reads a few kilobytes and records:
  live    the server answered 200 with audio (or an HLS playlist) and sent data
  https   the address is HTTPS (a page served over HTTPS cannot play an HTTP stream)
  cors    the server sent Access-Control-Allow-Origin for the app's origin or '*'
          (needed only for sound treatment through Web Audio; plain playback works without it)
A station is published when one of its streams is live and HTTPS. Outputs:
  public/<country>/<city>.json     what an app reads for one city
  public/index.json                the cities published, with their paths
  log/<country>/<city>/YYYY-MM.csv one line per station per run, for uptime
Standard library only.
"""
import argparse
import csv
import datetime
import glob
import json
import os
import ssl
import urllib.error
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
AUDIO = ('audio/', 'application/ogg', 'application/vnd.apple.mpegurl', 'application/x-mpegurl')
# Playlist types: some servers label an HLS playlist audio/mpegurl or audio/x-mpegurl.
HLS = ('application/vnd.apple.mpegurl', 'application/x-mpegurl', 'audio/mpegurl', 'audio/x-mpegurl')
UA = 'opendial-check/1 (+https://github.com/yaasiin-ayeva/opendial)'


def probe(url, origin, timeout=12):
    """Open one stream and describe it. Never raises."""
    out = {'url': url, 'live': False, 'https': url.startswith('https://'), 'cors': False,
           'content_type': '', 'hls': False, 'bitrate_kbps': None, 'error': ''}
    if not url.startswith(('http://', 'https://')):
        out['error'] = 'not an http(s) address'
        return out
    try:
        # Inside the try: a malformed address must not stop the whole run.
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Origin': origin, 'Icy-MetaData': '0'})
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
            ctype = (r.headers.get('Content-Type') or '').split(';')[0].strip().lower()
            out['content_type'] = ctype
            out['hls'] = ctype in HLS or r.geturl().split('?')[0].endswith('.m3u8')
            # A redirect to HTTP breaks an HTTPS page just as an HTTP address does.
            out['https'] = out['https'] and r.geturl().startswith('https://')
            acao = r.headers.get('Access-Control-Allow-Origin') or ''
            out['cors'] = acao == '*' or acao == origin
            br = r.headers.get('icy-br') or ''
            out['bitrate_kbps'] = int(br.split(',')[0]) if br.split(',')[0].strip().isdigit() else None
            data = r.read(4096 if not out['hls'] else 512)
            is_audio = ctype.startswith(AUDIO[0]) or ctype in AUDIO[1:] or out['hls']
            if r.status != 200:
                out['error'] = 'HTTP %d' % r.status
            elif not is_audio:
                out['error'] = 'not audio: %s' % (ctype or 'no content type')
            elif not data:
                out['error'] = 'no data'
            else:
                out['live'] = True
    except urllib.error.HTTPError as e:
        out['error'] = 'HTTP %d' % e.code
    except Exception as e:  # timeouts, DNS, TLS, resets: all mean "not playable now"
        out['error'] = type(e).__name__ + ': ' + str(e)[:80]
    return out


def check_city(place, origin, allow_http, write_log, now):
    """Check one list (place is 'gh/accra'). Returns its line for public/index.json."""
    data = json.load(open(os.path.join(ROOT, 'stations', place + '.json'), encoding='utf-8'))
    source = data['stations']
    published, rows = [], []
    for st in source:
        urls = [u for u in [st.get('stream')] + list(st.get('backup_streams') or []) if u]
        probes = [probe(u, origin) for u in urls]
        good = [p for p in probes if p['live'] and (p['https'] or allow_http)]
        state = 'ok' if good else ('no-stream' if not urls else
                                   'http-only' if any(p['live'] for p in probes) else 'down')
        rows.append([now.isoformat(), st['id'], state, good[0]['url'] if good else '',
                     '; '.join(p['error'] for p in probes if p['error'])])
        print('%-10s %-14s %-10s %s' % (place, st['id'], state, rows[-1][4]))
        if good:
            published.append({
                'id': st['id'], 'name': st['name'], 'frequency_mhz': st.get('frequency_mhz'),
                'language': st.get('language'), 'format': st.get('format'),
                'permission': st.get('permission', 'not-asked'),
                'streams': [{'url': p['url'], 'hls': p['hls'], 'cors': p['cors'],
                             'content_type': p['content_type'], 'bitrate_kbps': p['bitrate_kbps']}
                            for p in good]})
    published.sort(key=lambda s: (s['frequency_mhz'] is None, s['frequency_mhz'] or 0, s['name']))
    out = os.path.join(ROOT, 'public', place + '.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump({'country': data.get('country'), 'city': data.get('city'),
                   'checked_at': now.isoformat(), 'stations': published}, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    if write_log:
        path = os.path.join(ROOT, 'log', place, now.strftime('%Y-%m') + '.csv')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        new = not os.path.exists(path)
        with open(path, 'a', encoding='utf-8', newline='') as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(['checked_at', 'station', 'state', 'stream', 'errors'])
            w.writerows(rows)
    print('%s: %d of %d stations published' % (place, len(published), len(source)))
    return {'country': data.get('country'), 'country_name': data.get('country_name'),
            'city': data.get('city'), 'path': place + '.json', 'checked_at': now.isoformat(),
            'listed': len(source), 'published': len(published)}


def places():
    """Every list in stations/, as 'country/city'."""
    found = glob.glob(os.path.join(ROOT, 'stations', '*', '*.json'))
    return sorted(os.path.relpath(f, os.path.join(ROOT, 'stations'))[:-5].replace(os.sep, '/') for f in found)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('place', nargs='*', help="lists to check, such as gh/accra (default: all)")
    ap.add_argument('--origin', default='https://app.example', help="the app's origin, for the CORS check")
    ap.add_argument('--allow-http', action='store_true', help='publish HTTP streams too (local tests only)')
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()

    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    index_path = os.path.join(ROOT, 'public', 'index.json')
    index = {}
    if os.path.exists(index_path):
        index = {c['path']: c for c in json.load(open(index_path, encoding='utf-8')).get('cities', [])}
    for place in args.place or places():
        line = check_city(place, args.origin, args.allow_http, not args.no_log, now)
        index[line['path']] = line
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, 'w', encoding='utf-8') as fh:
        json.dump({'cities': [index[k] for k in sorted(index)]}, fh, indent=2, ensure_ascii=False)
        fh.write('\n')


if __name__ == '__main__':
    main()
