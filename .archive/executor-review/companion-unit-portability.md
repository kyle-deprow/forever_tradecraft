# Companion unit portability

Reviewed 2026-10-17. This bounded launch-readiness fix changes only
`deploy/crowley-companion.service` and the companion installation section of
`README.md`.

The user unit no longer selects `%h/repos/crowley` as a working directory and
now invokes the installed `%h/.local/bin/crowley-companion run` entry point
directly. README installation now uses `uv tool install --editable
/absolute/checkout`, keeps the authenticated configuration at
`~/.config/crowley/companion.toml`, and shows the user-unit installation and
reload commands. No service was enabled, started, or reloaded by this change.

Validation was limited to a scoped diff check and `systemd-analyze verify` when
available. Runtime activation, configuration authentication, game state, and
server connectivity were not exercised.
