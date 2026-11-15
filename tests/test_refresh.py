"""The weekly refresh repairs a dead station from the directory and leaves a working one alone."""
import http.server
import os
import sys
import threading
import unittest

os.environ['NO_PROXY'] = os.environ['no_proxy'] = '127.0.0.1,localhost'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
import refresh  # noqa: E402


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/live'):
            self.send_response(200)
            self.send_header('Content-Type', 'audio/mpeg')
            self.end_headers()
            self.wfile.write(b'\xff\xfb' * 2048)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


class Refresh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.base = 'http://127.0.0.1:%d' % cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def run_refresh(self, stations, entries):
        data = {'country': 'XX', 'city': 'Test', 'stations': stations}
        return data, refresh.refresh_list(data, entries, 'https://app.example', True, '2026-11-15')

    def test_dead_station_takes_the_live_directory_address(self):
        st = {'id': 'a', 'name': 'Alpha FM', 'stream': self.base + '/dead', 'backup_streams': [], 'sources': [], 'note': 'Old.'}
        entries = [{'name': 'Alpha FM 99.9', 'url_resolved': self.base + '/live1', 'votes': 3, 'stationuuid': 'u1'}]
        data, (changed, broken) = self.run_refresh([st], entries)
        self.assertEqual(changed, [('Alpha FM', self.base + '/dead', self.base + '/live1')])
        self.assertEqual(broken, [])
        self.assertEqual(st['stream'], self.base + '/live1')
        self.assertEqual(st['verified'], 'checked')
        self.assertIn('/dead', st['note'])
        self.assertTrue(st['sources'][-1].endswith('/u1'))

    def test_working_station_is_left_alone(self):
        st = {'id': 'a', 'name': 'Alpha FM', 'stream': self.base + '/live0', 'verified': 'heard'}
        entries = [{'name': 'Alpha FM', 'url_resolved': self.base + '/live1', 'votes': 9, 'stationuuid': 'u1'}]
        before = dict(st)
        _, (changed, broken) = self.run_refresh([st], entries)
        self.assertEqual((changed, broken), ([], []))
        self.assertEqual(st, before)

    def test_backup_keeps_a_station_out_of_the_refresh(self):
        st = {'id': 'a', 'name': 'Alpha FM', 'stream': self.base + '/dead', 'backup_streams': [self.base + '/live0']}
        _, (changed, broken) = self.run_refresh([st], [])
        self.assertEqual((changed, broken), ([], []))

    def test_addresses_with_a_query_string_and_dead_ones_are_skipped(self):
        st = {'id': 'a', 'name': 'Alpha FM', 'stream': ''}
        entries = [{'name': 'Alpha FM', 'url_resolved': self.base + '/live1?listenerid=42', 'votes': 9, 'stationuuid': 'u1'},
                   {'name': 'Alpha FM', 'url_resolved': self.base + '/dead', 'votes': 5, 'stationuuid': 'u2'},
                   {'name': 'Beta FM', 'url_resolved': self.base + '/live2', 'votes': 5, 'stationuuid': 'u3'}]
        _, (changed, broken) = self.run_refresh([st], entries)
        self.assertEqual(changed, [])
        self.assertEqual(broken, ['Alpha FM (no address)'])
        self.assertEqual(st['stream'], '')


if __name__ == '__main__':
    unittest.main()
