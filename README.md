# Tidemark

A Home Assistant custom integration (domain `tidemark`) that reads the Claude usage collector
already running on Unraid — `kmbrimble/claude-usage-widget`'s `collector/` service at
`http://192.168.0.10:8766/usage` — and exposes its figures as Home Assistant sensors.

The point: showing Claude usage and spend on Kieren's iPhone Home Screen via the HA companion
app's Gauge/Details widgets, without an Apple Developer licence.

This repo implements [`kmbrimble/claude-usage-widget#9`](https://github.com/kmbrimble/claude-usage-widget/issues/9).
Read that issue for the full design rationale before making architectural changes here.

## Architecture

```
Unraid: collector  ->  http://192.168.0.10:8766/usage  ->  Home Assistant (tidemark)  ->  sensors
```

- **No Anthropic credentials or OAuth in Home Assistant.** The collector is the single credential
  holder; this integration only ever reads its already-computed JSON snapshot.
- **Config flow:** host, port, optional bearer token, scan interval.
- **Polling:** a `DataUpdateCoordinator` polls the collector on the LAN — cheap, since no
  Anthropic rate limit applies to a local read.
- **Failure handling:** sensors go `unavailable` when the collector is unreachable, rather than
  showing a wrong number. The snapshot's `stale` flag and `generated_at` timestamp are surfaced
  and honoured, not silently dropped.

## Sensors

Verified live on Kieren's HA instance (Core 2026.9.1), 16 Sep 2026:

| Entity | What it shows |
|---|---|
| `sensor.tidemark_session_usage` | Session (5h) utilisation %, attrs incl. `projected_end`/`projected_basis` |
| `sensor.tidemark_weekly_usage` | Weekly (all) utilisation % |
| `sensor.tidemark_weekly_scoped_usage` | Weekly, scoped to the current model bucket |
| `sensor.tidemark_session_time_to_limit` | Seconds to exhaustion (session window), `unknown` if the collector can't project it |
| `sensor.tidemark_weekly_time_to_limit` | Same, weekly window |
| `sensor.tidemark_weekly_scoped_time_to_limit` | Same, weekly-scoped window |
| `sensor.tidemark_tokens_today` / `_this_week` / `_this_month` | Total tokens, with input/output/cache breakdown as attributes |
| `sensor.tidemark_cost_today` / `_this_week` / `_this_month` | Cost in the collector's reporting currency (`agent.currency` — AUD on this account), per-model breakdown as a `models` attribute |
| `sensor.tidemark_openrouter_credits_remaining` | OpenRouter key credit balance remaining |
| `sensor.tidemark_snapshot_generated_at` | The snapshot's own `generated_at` timestamp |
| `binary_sensor.tidemark_snapshot_stale` | On if any section (`claude`/`openrouter`/`agent`) of the last snapshot was marked stale |

Percent sensors are `%`, 0–100, `measurement` state class — sized for a Gauge widget. Cost and
token sensors are `total` (they roll down at each window boundary, so never `total_increasing`).

## Install

Via HACS (recommended): **HACS → ⋮ → Custom repositories** → add this repo's URL, category
"Integration" → install → restart HA. HACS tracks releases here, so future updates show up as
a normal HACS update.

Manual: copy `custom_components/tidemark/` into HA's `custom_components/` directory, restart HA.

Then **Settings → Devices & services → Add integration → Tidemark**, and enter the collector's
host (`192.168.0.10` on Kieren's LAN), port (`8766`), an optional bearer token, and a scan
interval in seconds (default 60 — cheap, it's a local LAN poll).

## iOS Home Screen widget (the actual point of this repo)

This has to be done **on the iPhone itself** — nothing here can add a widget to a Home Screen
remotely.

1. Open the **Home Assistant** companion app on the iPhone, signed into the same instance.
2. Long-press the Home Screen → **+** → search **Home Assistant** → choose the **Gauge** widget
   (or **Details** for several values at once) → add it.
3. Edit the widget (long-press → Edit Widget) and pick an entity, e.g.
   `sensor.tidemark_session_usage` for a 0–100% gauge of session usage, or
   `sensor.tidemark_weekly_usage` for the weekly figure.
4. For a Details widget showing several rows at once, add `sensor.tidemark_cost_today`,
   `sensor.tidemark_tokens_today`, and `binary_sensor.tidemark_snapshot_stale` alongside the
   percent sensor, so a stale collector is visible at a glance.

## Status

v0.1.0 — full integration shipped, tested, and verified live 16 Sep 2026.

## Distribution

**This repo is public.** HACS custom-repository installation is the supported path (see
Install, above). HACS reads GitHub releases, so `gh release create` on every version bump keeps
it up to date.

## Related

- [`kmbrimble/claude-usage-widget`](https://github.com/kmbrimble/claude-usage-widget) — the
  collector this integration reads from, and the snapshot contract it depends on.
