# Crowley

Auction house data platform and addon for **WoW Forever**. Scan the AH in game, store the
full history per house on a server, compute gold-making strategies, and push the results
back into the game (and into Auctionator shopping lists).

```
addon/Crowley        in-game scanner, Auctionator bridge, /crowley commands (Lua)
addon/Crowley_Data   data file the companion writes; loaded at login or /reload
src/crowley/core     shared: SavedVariables parser, scan format, stats, Lua writer
src/crowley/companion  watches the game folder, uploads scans, writes Crowley_Data
src/crowley/server   FastAPI + TimescaleDB ingest and query API
deploy/              docker compose (db + server), companion systemd unit
```

See [docs/HANDOFF.md](docs/HANDOFF.md) for requirements, history and roadmap, and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the technical design.

## Quickstart (server and game on one Linux machine)

```sh
# 1. Server + database
cp deploy/.env.example deploy/.env      # set CROWLEY_API_TOKEN and CROWLEY_DB_PASSWORD
docker compose -f deploy/docker-compose.yml up -d --build
curl localhost:8080/healthz

# 2. Companion config
uv sync
mkdir -p ~/.config/crowley && cat > ~/.config/crowley/companion.toml <<TOML
wow_dir    = "/home/you/.wine/drive_c/Program Files (x86)/World of Warcraft/_forever_"
server_url = "http://127.0.0.1:8080"
api_token  = "<CROWLEY_API_TOKEN from deploy/.env>"
TOML
uv run crowley-companion install-addon  # symlinks Crowley, copies Crowley_Data
uv run crowley-companion doctor         # checks paths, addons and the server
uv run crowley-companion run            # or install deploy/crowley-companion.service
```

The addon requires Auctionator. In game:

| Command | What it does |
|---|---|
| `/crowley probe` | Records the client's AH API surface. **Run this first on the beta.** |
| `/crowley status` | Current house, scan cooldown, stored scans, strategy data age |
| `/crowley scan` | Full AH scan (AH must be open; once per 15 min) |
| `/crowley set faction neutral` | Override house detection (`region`/`ruleset`/`faction`, or `auto`) |
| `/crowley lists` | Push Crowley shopping lists into Auctionator |

Scans reach the server after `/reload` or logout, because that is when WoW writes SavedVariables.

## Game and server on different machines (Tailscale)

1. On the server, set `CROWLEY_BIND` in `deploy/.env` to `tailscale ip -4` and restart compose.
2. On the game machine, set `server_url = "http://<server-tailnet-name>:8080"` and run the companion there.

## Tests

```sh
uv run pytest                    # core + addon Lua (runs the real addon under Lua 5.1)
docker compose -f deploy/docker-compose.yml exec db createdb -U crowley crowley_test
CROWLEY_TEST_DATABASE_URL=postgresql://crowley:<pw>@127.0.0.1:5432/crowley_test uv run pytest
```
