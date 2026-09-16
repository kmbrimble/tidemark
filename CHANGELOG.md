# Changelog

## [Unreleased]

### Plan — 2026-09-16: full Tidemark integration (implements claude-usage-widget#9)

Build the `custom_components/tidemark/` integration: config flow (host, port, optional bearer
token, scan interval) with an options flow for the interval; a `DataUpdateCoordinator` polling
`http://<host>:<port>/usage`; sensors for every figure in the live snapshot (session/weekly-all/
weekly-scoped percent + their `resets_at`, `projected_end`/`projected_basis`/
`exhausts_in_seconds`, per-period token totals and AUD-or-whatever-`agent.currency` cost for
today/week/month with per-model breakdown as attributes, OpenRouter account + key credit
figures, three `generated_at`/`stale` pairs) plus one aggregate stale binary sensor; entities
`unavailable` when the collector is unreachable. `hacs.json` + `manifest.json` (version 0.1.0)
for HACS custom-repository distribution (repo is now public). Tests with
`pytest-homeassistant-custom-component` against a fixture captured from the live collector.
Deploy: copy into HA's `custom_components/`, restart, create the config entry via the API,
verify against a fresh curl. No brand icon — that needs a PR to the external
`home-assistant/brands` repo, out of scope for this session.

## 0.1.0 - Initial commit

Repo bootstrap: README, CLAUDE.md and this changelog, plus a `.gitignore` for the eventual
Python/Home Assistant integration code. No integration code yet — implements the design in
`kmbrimble/claude-usage-widget#9`, not built out.
