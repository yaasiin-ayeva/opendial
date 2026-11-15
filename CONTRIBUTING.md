# Contributing

## Add a city

1. Create `stations/<country>/<city>.json` on the model of [`stations/gh/accra.json`](stations/gh/accra.json): `country` (upper-case ISO code), `country_name`, `city`, `about` and the stations, sorted by frequency.
2. Add the list to [`stations/index.json`](stations/index.json).
3. For each station give the frequency, the homepage and the direct stream address (the audio itself, not a web player), with the pages where you read them in `sources`.
4. Open the [listening test](https://yaasiin-ayeva.github.io/opendial/?view=listen), load your file from disk, run "Test all", and record what happened in `verified` and `last_test`.
5. Run `python3 -m unittest discover -s tests`, then open a pull request. The scheduled check picks the new list up by itself.

## Rules for addresses

- **Copy, never build.** An address comes from a page you opened. Do not derive one from another station's pattern, and do not trim it to make it look cleaner.
- **HTTPS only in practice.** Browsers block an HTTP stream on an HTTPS page. Record an HTTP-only address in `note`, not in `stream`.
- **No personal tokens.** Leave out addresses that carry a session or listener id.
- **Local stations only.** No international relays.
- **Say what is doubtful** in `note`: a single source, a certificate that may not match, a format you guessed.

## Fields of a station

| Field | Meaning |
| --- | --- |
| `id` | Lower-case, hyphens, unique in the city |
| `name`, `frequency_mhz`, `language`, `format`, `homepage` | As the station presents itself; `frequency_mhz` is `null` when unknown |
| `stream`, `backup_streams` | Direct stream addresses; `stream` may be empty |
| `sources` | Pages where the values were read |
| `verified` | `unverified` (never played), `played` (a browser played it), `heard` (a person confirmed the station), `checked` (passes the scheduled check) |
| `last_test` | Date, place and result of the latest listening test |
| `permission` | `not-asked`, `asked`, `granted`, `refused`: see [docs/agreements.md](docs/agreements.md) |
| `note` | What is doubtful |

## Code

Python standard library only, no build step for the pages. When the published JSON changes shape, change `openapi.yaml` in the same commit. Commit messages: an imperative subject under 72 characters, then why.

## Licence of contributions

By opening a pull request you agree that your code is released under the MIT licence ([LICENSE](LICENSE)) and your station data under CC0 1.0 ([LICENSE-DATA](LICENSE-DATA)). Only add data you read on a public page.
