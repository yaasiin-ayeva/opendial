#!/usr/bin/env python3
"""Tests for probe() of scripts/check.py, against a small server on 127.0.0.1.

Usage: python3 -m unittest discover -s tests -v
Standard library only. No test reaches the internet: real streams are tested with
scripts/check.py itself or by ear with tools/listen.html.
"""
import http.server
import os
import sys
import threading
import unittest

# The environment may set HTTP(S)_PROXY; the local server must be reached directly.
os.environ['NO_PROXY'] = os.environ['no_proxy'] = '127.0.0.1,localhost'

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
import check  # noqa: E402

ORIGIN = 'https://game.example'
SOUND = b'\xff\xfb\x90\x00' * 2048  # 8 kB that look like MP3 frames; never decoded
PLAYLIST = b'#EXTM3U\n#EXT-X-VERSION:3\n#EXTINF:6.0,\nsegment1.aac\n'

# path -> (status, headers, body)
ROUTES = {
    '/live': (200, {'Content-Type': 'audio/mpeg'}, SOUND),
    '/charset': (200, {'Content-Type': 'Audio/AACP; charset=utf-8'}, SOUND),
    '/ogg': (200, {'Content-Type': 'application/ogg'}, SOUND),
    '/page': (200, {'Content-Type': 'text/html'}, b'<html>player page</html>'),
    '/untyped': (200, {}, SOUND),
    '/empty': (200, {'Content-Type': 'audio/mpeg'}, b''),
    '/hls': (200, {'Content-Type': 'application/vnd.apple.mpegurl'}, PLAYLIST),
    '/hls-x': (200, {'Content-Type': 'application/x-mpegURL'}, PLAYLIST),
    '/hls-audio': (200, {'Content-Type': 'audio/x-mpegurl'}, PLAYLIST),
    '/list.m3u8': (200, {'Content-Type': 'text/plain'}, PLAYLIST),
    '/cors-any': (200, {'Content-Type': 'audio/mpeg', 'Access-Control-Allow-Origin': '*'}, SOUND),
    '/cors-game': (200, {'Content-Type': 'audio/mpeg', 'Access-Control-Allow-Origin': ORIGIN}, SOUND),
    '/cors-other': (200, {'Content-Type': 'audio/mpeg',
                          'Access-Control-Allow-Origin': 'https://other.example'}, SOUND),
    '/icy': (200, {'Content-Type': 'audio/mpeg', 'icy-br': '128'}, SOUND),
    '/icy-two': (200, {'Content-Type': 'audio/aac', 'icy-br': '64, 64'}, SOUND),
    '/icy-bad': (200, {'Content-Type': 'audio/mpeg', 'icy-br': 'high'}, SOUND),
    '/moved': (302, {'Location': '/live'}, b''),
    '/moved-to-page': (301, {'Location': '/page'}, b''),
    '/moved-to-hls': (302, {'Location': '/list.m3u8?session=1'}, b''),
    '/broken': (500, {'Content-Type': 'text/plain'}, b'error'),
}


class Handler(http.server.BaseHTTPRequestHandler):
    seen = {}  # path -> request headers of the last request

    def do_GET(self):
        path = self.path.split('?')[0]
        Handler.seen[path] = dict(self.headers)
        status, headers, body = ROUTES.get(path, (404, {'Content-Type': 'text/plain'}, b'not found'))
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class ProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.base = 'http://127.0.0.1:%d' % cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def probe(self, path, origin=ORIGIN):
        return check.probe(self.base + path, origin, timeout=5)

    # live or not
    def test_live_audio_stream(self):
        p = self.probe('/live')
        self.assertTrue(p['live'])
        self.assertEqual(p['error'], '')
        self.assertEqual(p['content_type'], 'audio/mpeg')
        self.assertFalse(p['hls'])
        self.assertEqual(p['url'], self.base + '/live')

    def test_content_type_parameters_and_case_are_ignored(self):
        p = self.probe('/charset')
        self.assertTrue(p['live'])
        self.assertEqual(p['content_type'], 'audio/aacp')

    def test_ogg_is_audio(self):
        self.assertTrue(self.probe('/ogg')['live'])

    def test_web_page_is_not_a_stream(self):
        p = self.probe('/page')
        self.assertFalse(p['live'])
        self.assertEqual(p['error'], 'not audio: text/html')

    def test_missing_content_type_is_not_a_stream(self):
        p = self.probe('/untyped')
        self.assertFalse(p['live'])
        self.assertEqual(p['error'], 'not audio: no content type')

    def test_audio_type_without_data_is_not_live(self):
        p = self.probe('/empty')
        self.assertFalse(p['live'])
        self.assertEqual(p['error'], 'no data')

    def test_404(self):
        p = self.probe('/nothing-here')
        self.assertFalse(p['live'])
        self.assertEqual(p['error'], 'HTTP 404')

    def test_500(self):
        p = self.probe('/broken')
        self.assertFalse(p['live'])
        self.assertEqual(p['error'], 'HTTP 500')

    def test_refused_connection_does_not_raise(self):
        p = check.probe('http://127.0.0.1:1/stream', ORIGIN, timeout=2)
        self.assertFalse(p['live'])
        self.assertNotEqual(p['error'], '')

    def test_malformed_address_does_not_raise(self):
        for url in ('not an address', 'http://', 'http://[broken/stream', 'file:///etc/hostname'):
            with self.subTest(url=url):
                p = check.probe(url, ORIGIN, timeout=2)
                self.assertFalse(p['live'])
                self.assertNotEqual(p['error'], '')

    # HLS
    def test_hls_playlist_content_type(self):
        p = self.probe('/hls')
        self.assertTrue(p['live'])
        self.assertTrue(p['hls'])
        self.assertEqual(p['content_type'], 'application/vnd.apple.mpegurl')

    def test_hls_playlist_other_content_types(self):
        for path in ('/hls-x', '/hls-audio'):
            with self.subTest(path=path):
                p = self.probe(path)
                self.assertTrue(p['live'])
                self.assertTrue(p['hls'])

    def test_hls_by_file_name(self):
        p = self.probe('/list.m3u8?session=1')
        self.assertTrue(p['live'])
        self.assertTrue(p['hls'])

    # HTTPS
    def test_http_address_is_not_https(self):
        self.assertFalse(self.probe('/live')['https'])

    # CORS
    def test_cors_absent(self):
        self.assertFalse(self.probe('/live')['cors'])

    def test_cors_any_origin(self):
        self.assertTrue(self.probe('/cors-any')['cors'])

    def test_cors_for_the_game_origin(self):
        self.assertTrue(self.probe('/cors-game')['cors'])

    def test_cors_for_another_origin(self):
        p = self.probe('/cors-other')
        self.assertTrue(p['live'])   # plain playback does not need CORS
        self.assertFalse(p['cors'])

    def test_origin_header_is_sent(self):
        self.probe('/cors-game')
        self.assertEqual(Handler.seen['/cors-game'].get('Origin'), ORIGIN)

    # bitrate
    def test_icy_bitrate(self):
        self.assertEqual(self.probe('/icy')['bitrate_kbps'], 128)

    def test_icy_bitrate_repeated(self):
        self.assertEqual(self.probe('/icy-two')['bitrate_kbps'], 64)

    def test_icy_bitrate_absent_or_unreadable(self):
        self.assertIsNone(self.probe('/live')['bitrate_kbps'])
        self.assertIsNone(self.probe('/icy-bad')['bitrate_kbps'])

    # redirects
    def test_redirect_to_a_stream(self):
        p = self.probe('/moved')
        self.assertTrue(p['live'])
        self.assertEqual(p['content_type'], 'audio/mpeg')
        self.assertEqual(p['url'], self.base + '/moved')  # the catalogue keeps the listed address

    def test_redirect_to_a_page(self):
        p = self.probe('/moved-to-page')
        self.assertFalse(p['live'])
        self.assertEqual(p['error'], 'not audio: text/html')

    def test_redirect_to_a_playlist(self):
        p = self.probe('/moved-to-hls')
        self.assertTrue(p['live'])
        self.assertTrue(p['hls'])


if __name__ == '__main__':
    unittest.main()
