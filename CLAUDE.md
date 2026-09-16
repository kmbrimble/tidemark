# tidemark — project context

Home Assistant custom integration (domain `tidemark`) that polls the Claude usage collector
already running on Unraid (`kmbrimble/claude-usage-widget`'s `collector/`, serving
`http://192.168.0.10:8766/usage`) and exposes its figures as HA sensors — so Kieren can put
Claude usage/spend on his iPhone Home Screen via the HA companion app's Gauge/Details widgets,
with no Apple Developer licence.

**This repo is the implementation of [`kmbrimble/claude-usage-widget#9`](https://github.com/kmbrimble/claude-usage-widget/issues/9).**
Read that issue before making architectural decisions here — it's the design spec, including
why prior art (`trickv/hass-claude-usage`) was rejected (it runs its own Anthropic OAuth flow
and polls Anthropic directly, which is exactly the second-poller/second-token risk this
architecture exists to avoid).

## Architecture — decided in the issue, not up for re-litigation here

- One credential holder: the collector. **No Anthropic credentials or OAuth ever live in Home
  Assistant.** This integration is a read-only consumer of the collector's JSON.
- Config flow: host, port, optional bearer token, scan interval.
- `DataUpdateCoordinator` polling the collector. Local LAN traffic — no Anthropic rate limit
  applies, so short intervals are cheap.
- Sensors go `unavailable` when the collector is unreachable — never show a stale number as if
  live. Honour the snapshot's `stale` flag and `generated_at` timestamp explicitly.

## Snapshot contract

Read from the collector side: `/projects/claude-usage-widget/CLAUDE.md` and
`/projects/claude-usage-widget/docs/usage-api.md` (the collector repo, not this one). Don't
assume the shape — check that doc before wiring a sensor to a field.

## Status

v0.1.0 shipped 16 Sep 2026: full integration (config flow + options flow, coordinator, sensors,
stale binary sensor), tested, deployed to the live HA instance, and released on GitHub.

## Distribution — resolved

**This repo is public**, so HACS distribution as a custom repository is the target — no private-repo
workaround needed. Kieren adds it in HACS as a custom repository pointing at this GitHub repo;
HACS reads releases, so every version bump needs a matching tagged `gh release`.

No brand icon: that needs a PR to the external `home-assistant/brands` repo, which isn't
something a session here can do unattended. Revisit if wanted later.

## Scope

- This repo: the HA custom integration only (`custom_components/tidemark/`), `hacs.json`,
  `manifest.json`.
- Not this repo: the collector itself, or any other consumer of its JSON (macOS widget,
  Windows tray) — those live in `kmbrimble/claude-usage-widget`.

## Secrets

Nothing credential-shaped is committed. The optional bearer token is entered live through the
config flow / options flow and stored only in HA's own config-entry storage, never in this repo.
Run a secret scan (`git grep` for bearer-looking strings, `HA_TOKEN`, `sk-or-`, JWT-shaped
tokens) before every push — the repo being public raises the cost of a slip.

## Test and verify

`cd custom_components/tidemark/.. && python3 -m venv .venv && .venv/bin/pip install
pytest-homeassistant-custom-component` (slow — it resolves a matching `homeassistant` core; it's
what pins the version below). Then `.venv/bin/python -m pytest tests/ -q`.

**Known version gap:** this container's Python (3.11) caps pip's resolve at `homeassistant
2024.3.3` (2024.4+ needs Python 3.12), while the live instance runs Core 2026.9.0. The test
suite proves the entity/coordinator/config-flow logic against a snapshot fixture — it does
**not** prove API compatibility with the 2.5-years-newer live core. The deploy step's log check
is the real compatibility test; a clean local test run is necessary, not sufficient.

Tests use a fixture (`tests/fixtures_snapshot.json`) captured from a live `curl` of the
collector with the `series` arrays trimmed — re-capture it if the collector's JSON shape changes,
don't hand-edit field names from memory.

## Deploy

No CI. Live install is manual, following `/projects/ha-config/CLAUDE.md`'s API-not-browser
discipline:

1. Copy `custom_components/tidemark/` (excluding `__pycache__`) into `/ha-config/custom_components/`
   on the HA config mount.
2. `POST /api/config/core/check_config` (validates YAML, not this component — informational here).
3. Restart via `homeassistant.restart`, poll `/api/config` until `state == "RUNNING"`.
4. Check `system_log/list` over the websocket, filtered for `tidemark`, at WARNING and above —
   not just ERROR. A `400` from the config-flow POST below means the import failed; read the log
   before touching code.
5. Create the config entry: `POST /api/config/config_entries/flow {"handler":"tidemark"}`, then
   `POST` the host/port/token/interval to the returned `flow_id`.
6. Verify entity states against a fresh `curl` of the collector, matched by `generated_at` (not
   just close-enough percent values — the collector polls independently on its own cadence).

Rollback if the install goes wrong: `rm -rf /ha-config/custom_components/tidemark` + restart.
There's no "backup and restore" step here (ha-config's constraint #1 backup rule is for editing
an existing file; this adds a new directory) — state that plainly rather than pretending one
applies.

Per-version release (every bump, not just v0.1.0): bump `manifest.json` version, tag
`vX.Y.Z`, `gh release create` with notes, then HACS picks it up on the next check.
