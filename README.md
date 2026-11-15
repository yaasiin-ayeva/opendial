# opendial

An open catalogue of real FM radio stations, city by city. opendial keeps a hand-edited list per city, tests the internet stream of each station on a schedule, and publishes the stations a web page can play now.

It does **not** relay, record or store audio: an app plays each station's own stream directly in the listener's browser.

- **Documentation:** https://yaasiin-ayeva.github.io/opendial/
- **Listening test:** https://yaasiin-ayeva.github.io/opendial/?view=listen
- **Cities so far:** Accra (Ghana), Cotonou (Benin), Lomé (Togo)

## Use it in an app

The catalogue is static JSON on GitHub Pages: no key, no account.

```js
const base = 'https://yaasiin-ayeva.github.io/opendial/public/';
const { cities } = await (await fetch(base + 'index.json')).json();
const { stations } = await (await fetch(base + 'gh/accra.json')).json();
new Audio(stations[0].streams[0].url).play(); // after a click
```

Treat it as a hint, not a promise: a stream can fail between two checks, so fall back to the next stream, then the next station. Route audio through Web Audio only for streams with `cors: true`. The documentation describes every field.

## How it works

| Step | Where | What |
| --- | --- | --- |
| 1. List | `stations/<country>/<city>.json` | Edited by hand: name, frequency, stream address, where each value was read |
| 2. Listen | `tools/listen.html` | A person tests the list in a real browser |
| 3. Check | `scripts/check.py`, every 30 minutes | Each stream must answer with audio, over HTTPS |
| 4. Publish | `public/<country>/<city>.json` | The stations that passed, with `hls`, `cors` and `permission` |
| 5. Refresh | `scripts/refresh.py`, every Monday | For a station whose stream is down or unknown, looks for a working address in the Radio Browser directory and proposes it as a pull request |

## Repository

```
stations/        hand-edited lists, one per city, and index.json naming them
public/          generated: the catalogue apps read (do not edit)
log/             generated: one line per station per check, for uptime (do not edit)
scripts/         check.py (the checker), refresh.py (repairs dead addresses), discover.py (lists candidates)
tools/           listen.html, the listening test
tests/           tests of the checker and of the lists, no internet needed
docs/            agreements.md, the stations' answers
index.html       the documentation site: renders openapi.yaml with Scalar
openapi.yaml     the description of the published files
```

`<country>` is the lower-case ISO 3166 two-letter code (`gh`), `<city>` a lower-case name with hyphens (`accra`).

## Run it

```bash
python3 scripts/check.py                 # check every city; or one: scripts/check.py gh/accra
python3 scripts/refresh.py               # repair dead addresses from Radio Browser (edits the lists, commits nothing)
python3 scripts/discover.py gh/accra     # candidate addresses for the stations of a list
python3 -m unittest discover -s tests    # tests, local only
```

Standard library only.

### Automation

| Workflow | When | What it does |
| --- | --- | --- |
| `check.yml` | Every 30 minutes | Tests every stream, commits `public/` and `log/` |
| `refresh.yml` | Mondays, 05:17 UTC, or by hand | Runs `refresh.py` and opens a pull request with the repaired addresses; an issue with a link if the repository does not let workflows open pull requests |
| `tests.yml` | Pull requests and pushes to `main` | Runs the tests |

The refresh never merges itself: an address from a community directory can be wrong, so a person runs the listening test before merging. The scheduled check tests CORS against the origin in the repository variable `APP_ORIGIN`.

## State

**Accra (18 stations).** On 15 November 2026 the listening test played 14 of them in Chrome on the published site; 13 of those also allow Web Audio. Class FM, GBC Uniiq FM, Okay FM and Oman FM did not load and need a working address. Addresses came from listening directories, not from the stations, and nobody has yet listened to confirm that each stream is the station it claims to be. No station has been asked for its agreement yet.

**Lomé (13 stations) and Cotonou (14 stations).** Added on 15 November 2026 from station sites and listening directories. Five stations in Lomé and six in Cotonou have a stream address; the others have a frequency only, mostly because their only public address carries an expiring token. In the listening test the same day, all six played in Cotonou and three of five in Lomé (Zéphyr FM and Kanal FM did not load).

## Contributing

Adding a city or fixing an address: see [CONTRIBUTING.md](CONTRIBUTING.md). Rules for coding agents: [AGENTS.md](AGENTS.md).

## Rights

The stations belong to their broadcasters. opendial lists public stream addresses and gives no right to use a station's name or audio; [docs/agreements.md](docs/agreements.md) records what each station has answered. The repository has no licence file yet: until one is added, the code and the lists are not licensed for reuse.

opendial was started for the game CHALE: Accra Nights, whose car radio plays the real Accra stations. Nothing in it is specific to the game.
