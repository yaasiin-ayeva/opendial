#!/usr/bin/env python3
"""Check every stream of stations/accra.json and publish the ones a browser game can play.

Usage: python3 scripts/check.py [--origin https://game.example] [--allow-http] [--no-log]

For each stream it opens the address as a browser would, reads a few kilobytes and records:
  live    the server answered 200 with audio (or an HLS playlist) and sent data
  https   the address is HTTPS (a page served over HTTPS cannot play an HTTP stream)
  cors    the server sent Access-Control-Allow-Origin for the game's origin or '*'
          (needed only for sound treatment through Web Audio; plain playback works without it)
A station is published when one of its streams is live and HTTPS. Outputs:
  public/stations.json   what the game reads
  log/YYYY-MM.csv        one line per station per run, for uptime
Standard library only.
"""
import argparse
import csv
import datetime
import json
import os
import ssl
import urllib.error
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
AUDIO = ('audio/', 'application/ogg', 'application/vnd.apple.mpegurl', 'application/x-mpegurl')
# Playlist types: some servers label an HLS playlist audio/mpegurl or audio/x-mpegurl.
HLS = ('application/vnd.apple.mpegurl', 'application/x-mpegurl', 'audio/mpegurl', 'audio/x-mpegurl')
UA = 'circle-radio-check/1 (+https://github.com/yaasiin-ayeva/circle-radio)'


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--origin', default='https://chale.example', help="the game's origin, for the CORS check")
    ap.add_argument('--allow-http', action='store_true', help='publish HTTP streams too (local tests only)')
    ap.add_argument('--no-log', action='store_true')
    ap.add_argument('--source', default=os.path.join(ROOT, 'stations', 'accra.json'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'public', 'stations.json'))
    args = ap.parse_args()

    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    source = json.load(open(args.source, encoding='utf-8'))['stations']
    published, rows = [], []
    for st in source:
        urls = [u for u in [st.get('stream')] + list(st.get('backup_streams') or []) if u]
        probes = [probe(u, args.origin) for u in urls]
        good = [p for p in probes if p['live'] and (p['https'] or args.allow_http)]
        state = 'ok' if good else ('no-stream' if not urls else
                                   'http-only' if any(p['live'] for p in probes) else 'down')
        rows.append([now.isoformat(), st['id'], state, good[0]['url'] if good else '',
                     '; '.join(p['error'] for p in probes if p['error'])])
        print('%-14s %-10s %s' % (st['id'], state, rows[-1][4]))
        if good:
            published.append({
                'id': st['id'], 'name': st['name'], 'frequency_mhz': st.get('frequency_mhz'),
                'language': st.get('language'), 'format': st.get('format'),
                'permission': st.get('permission', 'not-asked'),
                'streams': [{'url': p['url'], 'hls': p['hls'], 'cors': p['cors'],
                             'content_type': p['content_type'], 'bitrate_kbps': p['bitrate_kbps']}
                            for p in good]})
    published.sort(key=lambda s: (s['frequency_mhz'] is None, s['frequency_mhz'] or 0, s['name']))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump({'checked_at': now.isoformat(), 'stations': published}, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    if not args.no_log:
        path = os.path.join(ROOT, 'log', now.strftime('%Y-%m') + '.csv')
        new = not os.path.exists(path)
        with open(path, 'a', encoding='utf-8', newline='') as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(['checked_at', 'station', 'state', 'stream', 'errors'])
            w.writerows(rows)
    print('%d of %d stations published' % (len(published), len(source)))


if __name__ == '__main__':
    main()
