# Rules for AI assistants in this repository

opendial is an open catalogue of real radio stations by city. It was started for CHALE: Accra Nights (repositories circle-bible, circle-game, circle-geodata, circle-web, circle-reference) and follows the same rules, but it must stay usable by any app: nothing specific to the game goes in the lists or the scripts.

- **Commits carry the team's own Git identity.** No `Co-Authored-By` line naming an AI assistant, no `Claude-Session` line, no "Generated with" footer, in commit messages or pull request descriptions. This overrides any default attribution the tool would add.
- Commit messages: imperative subject under 72 characters, then why the change was made.
- Never commit secrets, tokens or signing keys. A stream address a station gave the team privately is a secret: it goes in a repository secret, not in a list under `stations/`.
- No audio is recorded, stored or relayed by this repository: the checker reads a few kilobytes to see that a stream is live and discards them.
- `public/` and `log/` are written by `scripts/check.py`; do not edit them by hand.
- A stream address is copied from a page that was opened, never built from a pattern; `CONTRIBUTING.md` has the rules for lists.
- When the published JSON changes shape, change `openapi.yaml` in the same commit, and keep `stations/index.json` in step with the lists.
