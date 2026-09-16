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

Bootstrap only (seeded 16 Sep 2026). No integration code yet.

## Open question — check before relying on it

**Whether HACS can install a custom integration from a *private* GitHub repo is unverified.**
This repo is private. Verify HACS's private-repo support before promising HACS distribution to
Kieren — if it can't, fall back to manual install (`custom_components/tidemark/` copied in by
hand) or make the repo public.

## Scope

- This repo: the HA custom integration only (`custom_components/tidemark/` once code exists),
  `hacs.json`, `manifest.json`.
- Not this repo: the collector itself, or any other consumer of its JSON (macOS widget,
  Windows tray) — those live in `kmbrimble/claude-usage-widget`.

## Test and verify

No test harness yet — add one (pytest + `pytest-homeassistant-custom-component` is the standard
choice for HA custom integrations) when the first sensor lands.

## Deploy

No deploy step yet beyond `git push origin main`.
