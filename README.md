# circle-radio

The catalogue of real Accra FM stations that CHALE: Accra Nights plays on its car radio. It keeps a list of stations, checks their internet streams on a schedule, and publishes the ones a browser game can play. Decision and reasons: circle-bible `DECISIONS.md`, 15 November 2026.

It does **not** relay, record or store audio. The game plays each station's own stream directly in the player's browser.

## Contents

```
stations/accra.json     the source list, edited by hand: name, frequency, stream address, permission
scripts/check.py        checks every stream and writes public/stations.json and the log
scripts/discover.py     suggests stream addresses from the Radio Browser directory (prints only)
public/stations.json    generated: the stations the game may play now
log/YYYY-MM.csv         generated: one line per station per check, for uptime
AGREEMENTS.md           the stations' answers
.github/workflows/      the scheduled check, every 30 minutes
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
```

Set the repository variable `GAME_ORIGIN` to the game's address so that the scheduled check tests CORS for the right origin. Serve `public/stations.json` from GitHub Pages or the raw file address, and allow the game's origin to fetch it.

## State on 15 November 2026

- 14 stations listed. Two have an address (Peace FM and Okay FM, from the station group's own site) and both are HTTP, so they are not playable from an HTTPS page as they stand. The other twelve have no address yet.
- Six frequencies are still to confirm (`null` in the list).
- The checker was tested against a local test server only; neither script has yet run against the real streams or Radio Browser.
- No station has been asked yet.

## Next

1. Run `discover.py`, pick addresses, run `check.py`: this tells how many Accra stations are playable today.
2. Write to the first two or three stations (AGREEMENTS.md says what to ask).
3. Build the player and the fallback in circle-game against `public/stations.json`.
