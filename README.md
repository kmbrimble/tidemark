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

## Sensors (planned — see issue #9 for the full list)

Session %, weekly all %, weekly scoped %, time to limit, projected end and its basis, token
counts and AUD cost per day/week/month, per-model breakdown, OpenRouter credits, a
`generated_at` timestamp, and a stale binary sensor.

## Status

Bootstrap only. No integration code yet — this commit seeds the repo (README, CHANGELOG,
CLAUDE.md, `.gitignore`) ahead of implementation.

## Distribution

Intended to be HACS-installable as a custom repository. **Unverified:** whether HACS can add and
install from a *private* GitHub repo. This must be checked before relying on HACS distribution —
if it can't, the fallback is manual installation (copy `custom_components/tidemark/` into HA) or
making the repo public.

## Related

- [`kmbrimble/claude-usage-widget`](https://github.com/kmbrimble/claude-usage-widget) — the
  collector this integration reads from, and the snapshot contract it depends on.
