"""The hand-edited lists are well formed and stations/index.json names each of them."""
import glob
import json
import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
STATIONS = os.path.join(ROOT, 'stations')
PERMISSION = {'not-asked', 'asked', 'granted', 'refused'}
VERIFIED = {'unverified', 'played', 'heard', 'checked'}


def load(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def lists():
    found = glob.glob(os.path.join(STATIONS, '*', '*.json'))
    return sorted(os.path.relpath(f, STATIONS).replace(os.sep, '/') for f in found)


class Lists(unittest.TestCase):
    def test_index_names_every_list(self):
        index = load(os.path.join(STATIONS, 'index.json'))['lists']
        self.assertEqual(sorted(e['path'] for e in index), lists())
        for e in index:
            data = load(os.path.join(STATIONS, e['path']))
            for key in ('country', 'country_name', 'city'):
                self.assertEqual(e[key], data[key], '%s: %s' % (e['path'], key))

    def test_each_list_is_well_formed(self):
        for path in lists():
            data = load(os.path.join(STATIONS, path))
            country, city = path[:-5].split('/')
            self.assertRegex(country, r'^[a-z]{2}$', path)
            self.assertRegex(city, r'^[a-z0-9-]+$', path)
            self.assertEqual(data['country'], country.upper(), path)
            ids = [s['id'] for s in data['stations']]
            self.assertEqual(len(ids), len(set(ids)), path + ': duplicate ids')
            for s in data['stations']:
                where = '%s: %s' % (path, s.get('id'))
                self.assertRegex(s['id'], r'^[a-z0-9-]+$', where)
                self.assertTrue(s['name'].strip(), where)
                self.assertIn(type(s.get('frequency_mhz')), (int, float, type(None)), where)
                self.assertIn(s.get('permission', 'not-asked'), PERMISSION, where)
                self.assertIn(s.get('verified', 'unverified'), VERIFIED, where)
                for url in [s.get('stream', '')] + list(s.get('backup_streams') or []):
                    if url:
                        self.assertTrue(re.match(r'^https?://', url), where + ': ' + url)


if __name__ == '__main__':
    unittest.main()
