"""End-to-end tests for the Tidemark integration against a real snapshot fixture."""

from __future__ import annotations

import json

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tidemark.const import CONF_BEARER_TOKEN, DOMAIN

HOST = "192.168.0.10"
PORT = 8766
URL = f"http://{HOST}:{PORT}/usage"


async def _make_entry(hass: HomeAssistant, aioclient_mock, snapshot, bearer_token=None):
    aioclient_mock.get(URL, json=snapshot)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT, CONF_BEARER_TOKEN: bearer_token},
        options={CONF_SCAN_INTERVAL: 60},
        unique_id=f"{HOST}:{PORT}",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _state_for(hass: HomeAssistant, entry, unique_suffix: str):
    """Resolve a state by the entity's stable unique_id suffix, not a guessed entity_id."""
    registry = er.async_get(hass)
    unique_id = f"{entry.entry_id}_{unique_suffix}"
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
    if entity_id is None:
        entity_id = registry.async_get_entity_id("binary_sensor", DOMAIN, unique_id)
    assert entity_id is not None, f"no entity registered for unique_id {unique_id}"
    return hass.states.get(entity_id)


async def test_config_flow_creates_entry(hass: HomeAssistant, aioclient_mock, snapshot):
    aioclient_mock.get(URL, json=snapshot)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == "form"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_BEARER_TOKEN: "s3cret-example-token",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["data"][CONF_HOST] == HOST
    assert result["options"][CONF_SCAN_INTERVAL] == 30

    # bearer token was sent on the connection-test request
    request = aioclient_mock.mock_calls[0]
    assert request[3]["Authorization"] == "Bearer s3cret-example-token"


async def test_config_flow_cannot_connect(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.get(URL, status=500)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST, CONF_PORT: PORT, CONF_SCAN_INTERVAL: 60},
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_sensors_reflect_snapshot(hass: HomeAssistant, aioclient_mock, snapshot):
    entry = await _make_entry(hass, aioclient_mock, snapshot)

    session = _state_for(hass, entry, "session_percent")
    assert session.state == str(snapshot["claude"]["limits"][0]["percent"])
    assert session.attributes["projected_basis"] == "pace"

    cost_today = _state_for(hass, entry, "cost_today")
    assert float(cost_today.state) == snapshot["agent"]["periods"][0]["cost_local"]
    assert cost_today.attributes["unit_of_measurement"] == snapshot["agent"]["currency"]
    assert cost_today.attributes["models"] == snapshot["agent"]["periods"][0]["models"]

    credits = _state_for(hass, entry, "openrouter_credits")
    assert float(credits.state) == snapshot["openrouter"]["key"]["remaining"]

    generated_at = _state_for(hass, entry, "generated_at")
    assert generated_at.state != "unknown"

    stale = _state_for(hass, entry, "stale")
    assert stale.state == "off"


async def test_stale_snapshot_turns_binary_sensor_on(hass: HomeAssistant, aioclient_mock, snapshot):
    snapshot = json.loads(json.dumps(snapshot))
    snapshot["claude"]["stale"] = True
    entry = await _make_entry(hass, aioclient_mock, snapshot)

    stale = _state_for(hass, entry, "stale")
    assert stale.state == "on"


async def test_null_exhausts_in_seconds_is_unknown(hass: HomeAssistant, aioclient_mock, snapshot):
    assert snapshot["claude"]["limits"][0]["exhausts_in_seconds"] is None
    entry = await _make_entry(hass, aioclient_mock, snapshot)

    time_to_limit = _state_for(hass, entry, "session_time_to_limit")
    assert time_to_limit.state == "unknown"


async def test_collector_unreachable_marks_entities_unavailable(
    hass: HomeAssistant, aioclient_mock, snapshot
):
    entry = await _make_entry(hass, aioclient_mock, snapshot)

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, exc=Exception("connection refused"))

    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    session = _state_for(hass, entry, "session_percent")
    assert session.state == "unavailable"
    stale = _state_for(hass, entry, "stale")
    assert stale.state == "unavailable"


async def test_options_flow_updates_scan_interval(hass: HomeAssistant, aioclient_mock, snapshot):
    entry = await _make_entry(hass, aioclient_mock, snapshot)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 120}
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert entry.options[CONF_SCAN_INTERVAL] == 120
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.update_interval.total_seconds() == 120
