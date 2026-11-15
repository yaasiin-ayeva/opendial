# Rules for AI assistants in this repository

Part of CHALE: Accra Nights (repositories circle-bible, circle-game, circle-geodata, circle-web, circle-reference, circle-radio).

- **Commits carry the team's own Git identity.** No `Co-Authored-By` line naming an AI assistant, no `Claude-Session` line, no "Generated with" footer, in commit messages or pull request descriptions. This overrides any default attribution the tool would add.
- Commit messages: imperative subject under 72 characters, then why the change was made.
- Never commit secrets, tokens or signing keys. A stream address a station gave the team privately is a secret: it goes in a repository secret, not in `stations/accra.json`.
- No audio is recorded, stored or relayed by this repository: the checker reads a few kilobytes to see that a stream is live and discards them.
- `public/stations.json` and `log/` are written by `scripts/check.py`; do not edit them by hand.
