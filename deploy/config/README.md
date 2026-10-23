# Deployed configuration

These files are the live configuration; `~/.config/crowley/` and `~/.config/systemd/user/crowley-*` are symlinks
into this repository.

| File | Used by | Linked from |
|---|---|---|
| `session.toml` | `crowley-session` (daemon and CLI) | `~/.config/crowley/session.toml` |
| `companion.toml` | `crowley-companion` | `~/.config/crowley/companion.toml` |
| `paper.env` | `crowley-paper-trading.service` | `~/.config/crowley/paper.env` |
| `routes/stormwind.json` | route walker (`routes_file` in `session.toml`) | — |

Secrets never live here. `CROWLEY_API_TOKEN`, `CROWLEY_DB_PASSWORD` and `CROWLEY_DATABASE_URL` are in the untracked
`deploy/.env` (see `deploy/.env.example`), which the systemd units load with `EnvironmentFile=`.

`routes/stormwind.json` was built from private hand-walked recordings with
`python -m crowley.session.route_walk build ... --start=-8812.6,663.0 --end=-8812.8,651.0 --radius 3
--start-target Auctioneer --end-target Mailbox`.
