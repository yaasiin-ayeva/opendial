# opendial

An open catalogue of real FM radio stations, city by city, with the internet stream of each one checked on a schedule. It keeps a hand-edited list per city, tests every stream, and publishes the ones a web page can play now. It starts with Accra, Ghana; other cities and countries are added as new lists.

opendial does **not** relay, record or store audio. An app that uses it plays each station's own stream directly in the listener's browser.

Its first user is the game CHALE: Accra Nights, whose car radio plays the real Accra stations (circle-bible `DECISIONS.md`, 15 November 2026). Nothing in opendial is specific to the game.

## Online

- Documentation: https://yaasiin-ayeva.github.io/opendial/
- Listening test, inside the documentation: https://yaasiin-ayeva.github.io/opendial/?view=listen
- Catalogue of a city, once the scheduled check has run: https://yaasiin-ayeva.github.io/opendial/public/gh/accra.json
- Index of cities: https://yaasiin-ayeva.github.io/opendial/public/index.json

The site is GitHub Pages serving the `main` branch as it is (`.nojekyll`). `index.html` renders `openapi.yaml` with [Scalar](https://github.com/scalar/scalar), loaded from a CDN, and shows `tools/listen.html` behind its "Listening test" button. When the published JSON changes shape, change `openapi.yaml` in the same commit.

## Contents

```
stations/<country>/<city>.json   the source list of one city, edited by hand: name, frequency, stream
                                 address, permission, sources (where each value was read) and
                                 verified (unverified, heard, checked). Today: stations/gh/accra.json
scripts/check.py                 checks every stream and writes public/ and log/
scripts/discover.py              suggests stream addresses from the Radio Browser directory (prints only)
openapi.yaml                     the description of the published files, rendered as the documentation
index.html                       the documentation site (Scalar) with the listening test
tools/listen.html                a page to open in a browser: plays each stream, notes what happened,
                                 exports the results
tests/test_check.py              tests of the checker against a local server (no internet needed)
public/<country>/<city>.json     generated: the stations of one city that can be played now
public/index.json                generated: the cities published, with their paths
log/<country>/<city>/YYYY-MM.csv generated: one line per station per check, for uptime
AGREEMENTS.md                    the stations' answers
.github/workflows/               check.yml: the scheduled check, every 30 minutes; tests.yml: the tests
```

`<country>` is the lower-case ISO 3166 two-letter code (`gh`, `ng`, `ke`), `<city>` a lower-case name with hyphens.

## Adding a city

1. Create `stations/<country>/<city>.json` on the model of `stations/gh/accra.json`, with `country`, `country_name`, `city` and the list of stations.
2. Run `python3 scripts/discover.py <country>/<city>` for candidate addresses, listen to them with `tools/listen.html`, and fill the list.
3. Run `python3 scripts/check.py <country>/<city>`. The scheduled check picks the new list up by itself.

## What the checker tests

| Test | Why |
| --- | --- |
| Live: HTTP 200, audio content type (or an HLS playlist), data received | The stream plays now |
| HTTPS, including after redirects | A web app is served over HTTPS; browsers block an HTTP stream on an HTTPS page |
| CORS header for the app's origin | Needed only for sound treatment through Web Audio (filters, effects); plain playback works without it |

A station is published when one of its streams is live and HTTPS. States in the log: `ok`, `http-only` (live but unusable from an HTTPS page), `down`, `no-stream` (no address yet).

## What an app reads

`public/index.json` lists the cities. `public/<country>/<city>.json` holds one city, sorted by frequency:

```json
{
  "country": "GH", "city": "Accra",
  "checked_at": "2026-11-15T10:30:00+00:00",
  "stations": [
    {
      "id": "joy-fm", "name": "Joy FM", "frequency_mhz": 99.7, "language": "en",
      "format": "news, talk, music", "permission": "granted",
      "streams": [{"url": "https://…", "hls": false, "cors": true, "content_type": "audio/mpeg", "bitrate_kbps": 128}]
    }
  ]
}
```

The app keeps the player, the station switch and the fallback. It should treat the catalogue as a hint, not a promise: a stream can fail between two checks. Route audio through Web Audio only for streams with `cors: true`. Decide in the app whether to show stations whose `permission` is not `granted`. For CHALE this lives in circle-game: next healthy station, then the shipped playlist.

## Use

```bash
python3 scripts/discover.py gh/accra       # candidates per station, from Radio Browser
# listen, then copy the chosen address into stations/gh/accra.json
python3 scripts/check.py                   # every city; or: python3 scripts/check.py gh/accra
python3 scripts/check.py --origin https://<the app's address>
python3 -m unittest discover -s tests -v   # the checker's tests, local only
```

To test by ear, open `tools/listen.html` in a browser (from GitHub Pages, or from disk with the file picker), load `stations/gh/accra.json`, and press Play on a stream or "Test all" (8 seconds per stream). It shows, per stream: HTTPS or HTTP, whether sound started and how fast, and whether the server allows CORS; "Export results" downloads the table.

Set the repository variable `APP_ORIGIN` to the app's address so that the scheduled check tests CORS for the right origin. Serve `public/` from GitHub Pages or the raw file addresses.

## State on 15 November 2026 (Accra, the only city so far)

- 18 stations listed: the first 14, plus 3FM, Class FM, Onua FM and Angel FM.
- All 18 have a stream address written as HTTPS, and all 18 frequencies are filled in (none is `null`). Peace FM and Okay FM also keep their earlier HTTP address as a backup.
- **Every address is unverified.** They were copied on 15 November 2026 from web pages, mostly listening directories (the `sources` field of each station), from a machine that could not reach the streams. None has been played or checked. Each stays `"verified": "unverified"` until someone hears it in `tools/listen.html` or `check.py` finds it live, on a machine with internet. `public/` is still empty.
- No station publishes a direct address on its own site: the sites of Joy FM, Adom FM and Peace FM only embed a player. Nine of the 18 addresses rest on a single directory page.
- Known doubts, written in each station's `note`:
  - Hitz FM and Asempa FM: the directory shows the address only with a query string carrying a player key and a listener id. The list keeps the address without the query string; it may not answer that way.
  - Okay FM and Oman FM: the host name may not match its certificate.
  - GBC Uniiq FM: a bare IP address, unlikely to work over HTTPS.
  - Citi FM and YFM: the directories disagree on the address; two are listed for each.
  - Accra FM: homepage not found. The language and format of the four added stations were not researched.
- Frequencies come from Wikipedia's list of stations in Greater Accra and agree with the directories; they were not compared with the National Communications Authority's list.
- The checker is tested against a local server only (`tests/`, 25 tests). Neither script has run against the real streams or Radio Browser. `tools/listen.html` has not been opened in a browser yet: its script was only checked for syntax.
- No station has been asked yet.

## Next

1. On a machine with internet: open `tools/listen.html` (served over HTTPS), load `stations/gh/accra.json`, run "Test all", export the results. Run `python3 scripts/check.py` as well. This tells how many Accra stations are playable today.
2. Correct the list from those results: remove or replace the addresses that fail, set `verified` to `heard` or `checked` on the ones that play, and use `discover.py` for the stations left without a working address.
3. Write to the first two or three stations (AGREEMENTS.md says what to ask), and ask the Multimedia Group for clean addresses for Hitz FM and Asempa FM.
4. Compare the frequencies with the National Communications Authority's FM list.
5. Build the player and the fallback in circle-game against `public/gh/accra.json`.
