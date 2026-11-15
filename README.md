# circle-radio

The catalogue of real Accra FM stations that CHALE: Accra Nights plays on its car radio. It keeps a list of stations, checks their internet streams on a schedule, and publishes the ones a browser game can play. Decision and reasons: circle-bible `DECISIONS.md`, 15 November 2026.

It does **not** relay, record or store audio. The game plays each station's own stream directly in the player's browser.

## Contents

```
stations/accra.json     the source list, edited by hand: name, frequency, stream address, permission,
                        sources (where each value was read) and verified (unverified, heard, checked)
scripts/check.py        checks every stream and writes public/stations.json and the log
scripts/discover.py     suggests stream addresses from the Radio Browser directory (prints only)
tools/listen.html       a page to open in a browser: plays each stream, notes what happened, exports the results
tests/test_check.py     tests of the checker against a local server (no internet needed)
public/stations.json    generated: the stations the game may play now
log/YYYY-MM.csv         generated: one line per station per check, for uptime
AGREEMENTS.md           the stations' answers
.github/workflows/      check.yml: the scheduled check, every 30 minutes; tests.yml: the tests, on pull requests
```

## What the checker tests

| Test | Why |
| --- | --- |
| Live: HTTP 200, audio content type (or an HLS playlist), data received | The stream plays now |
| HTTPS, including after redirects | The game is served over HTTPS; browsers block an HTTP stream on an HTTPS page |
| CORS header for the game's origin | Needed only for sound treatment through Web Audio (car-radio filter, muffling); plain playback works without it |

A station is published when one of its streams is live and HTTPS. States in the log: `ok`, `http-only` (live but unusable from an HTTPS page), `down`, `no-stream` (no address yet).

## What the game reads

`public/stations.json`, sorted by frequency:

```json
{
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

The game side (circle-game) keeps the player, the station switch and the fallback: next healthy station, then the shipped playlist. It should treat the catalogue as a hint, not a promise: a stream can fail between two checks. Apply the sound filter only to streams with `cors: true`. Decide in the game whether to show stations whose `permission` is not `granted`.

## Use

```bash
python3 scripts/discover.py            # candidates per station, from Radio Browser
# listen, then copy the chosen address into stations/accra.json
python3 scripts/check.py --origin https://<the game's address>
python3 -m unittest discover -s tests -v   # the checker's tests, local only
```

To test by ear, open `tools/listen.html` in a browser (from GitHub Pages, or from disk with the file picker), load `stations/accra.json`, and press Play on a stream or "Test all" (8 seconds per stream). It shows, per stream: HTTPS or HTTP, whether sound started and after how long, the error if not, and whether a CORS fetch is allowed. "Export results" downloads the table as JSON. Serve the page over HTTPS to see what the game will see: an HTTP stream can play on a page opened from disk and still be blocked in the game.

Set the repository variable `GAME_ORIGIN` to the game's address so that the scheduled check tests CORS for the right origin. Serve `public/stations.json` from GitHub Pages or the raw file address, and allow the game's origin to fetch it.

## State on 15 November 2026

- 18 stations listed: the first 14, plus 3FM, Class FM, Onua FM and Angel FM.
- All 18 have a stream address written as HTTPS, and all 18 frequencies are filled in (none is `null`). Peace FM and Okay FM also keep their earlier HTTP address as a backup.
- **Every address is unverified.** They were copied on 15 November 2026 from web pages, mostly listening directories (the `sources` field of each station), from a machine that could not reach the streams. None has been played or checked. Each stays `"verified": "unverified"` until someone hears it in `tools/listen.html` or `check.py` finds it live, on a machine with internet. `public/stations.json` is still empty.
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

1. On a machine with internet: open `tools/listen.html` (served over HTTPS), load `stations/accra.json`, run "Test all", export the results. Run `python3 scripts/check.py` as well. This tells how many Accra stations are playable today.
2. Correct the list from those results: remove or replace the addresses that fail, set `verified` to `heard` or `checked` on the ones that play, and use `discover.py` for the stations left without a working address.
3. Write to the first two or three stations (AGREEMENTS.md says what to ask), and ask the Multimedia Group for clean addresses for Hitz FM and Asempa FM.
4. Compare the frequencies with the National Communications Authority's FM list.
5. Build the player and the fallback in circle-game against `public/stations.json`.
