# Changelog

## [Unreleased]

## 0.1.0 - 2026-09-16

Full `custom_components/tidemark/` integration, implementing `kmbrimble/claude-usage-widget#9`:

- Config flow (host, port, optional bearer token, scan interval) that tests the connection
  before creating the entry, plus an options flow for changing the scan interval later.
- `DataUpdateCoordinator` polling `http://<host>:<port>/usage`.
- Sensors for every figure in the live snapshot: session/weekly-all/weekly-scoped utilisation %
  (with `projected_end`/`projected_basis`/trend as attributes), a time-to-limit sensor per
  window, per-period (today/week/month) token totals and cost in the collector's reporting
  currency with per-model breakdown as an attribute, OpenRouter key credit balance, the
  snapshot's `generated_at` timestamp, and a `stale` binary sensor (on if any of the collector's
  three sections was marked stale).
- Entities go `unavailable` when the collector is unreachable, or when the specific section they
  read from reports `ok: false`.
- `hacs.json` + `manifest.json` (version 0.1.0) for HACS custom-repository distribution — this
  repo is now public, so no private-repo workaround was needed.
- Tests: `pytest` + `pytest-homeassistant-custom-component`, against a fixture captured from a
  live curl of the collector (8 tests: config flow success/failure, snapshot-to-state mapping,
  stale flag, null-projection handling, collector-unreachable unavailability, per-section
  `ok: false` unavailability, options flow).
- No brand icon — that needs a PR to the external `home-assistant/brands` repo, out of scope for
  an unattended session.
- Deployed and verified live against Kieren's HA instance (Core 2026.9.1): config-check passed,
  restart clean (no `tidemark` warnings/errors in the system log), config entry created via the
  API, and all 15 entity states matched a fresh collector curl exactly (`generated_at` and every
  value, byte for byte).
- Known gap, documented in CLAUDE.md: this container's Python (3.11) caps the test harness at
  `homeassistant` 2024.3.3, 2.5 years behind the live Core 2026.9.1 — the deploy verification
  above is what actually proves compatibility, not the test suite.

## 0.1.0 - Initial commit

Repo bootstrap: README, CLAUDE.md and this changelog, plus a `.gitignore` for the eventual
Python/Home Assistant integration code. No integration code yet — implements the design in
`kmbrimble/claude-usage-widget#9`, not built out.
