"""Config flow for Tidemark."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_BEARER_TOKEN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN

CONNECT_TIMEOUT = 10

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_BEARER_TOKEN): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


async def _test_connection(hass, host: str, port: int, bearer_token: str | None) -> None:
    """Raise CannotConnect if the collector isn't reachable."""
    session = async_get_clientsession(hass)
    headers = {"Authorization": f"Bearer {bearer_token}"} if bearer_token else {}
    try:
        async with asyncio.timeout(CONNECT_TIMEOUT):
            async with session.get(f"http://{host}:{port}/usage", headers=headers) as resp:
                if resp.status != 200:
                    raise CannotConnect(f"HTTP {resp.status}")
    except (ClientError, TimeoutError) as err:
        raise CannotConnect(str(err)) from err


class CannotConnect(Exception):
    """Cannot connect to the collector."""


class TidemarkConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tidemark."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()
            try:
                await _test_connection(
                    self.hass, host, port, user_input.get(CONF_BEARER_TOKEN)
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Tidemark ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_BEARER_TOKEN: user_input.get(CONF_BEARER_TOKEN),
                    },
                    options={CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL]},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return TidemarkOptionsFlow(config_entry)


class TidemarkOptionsFlow(OptionsFlow):
    """Handle options (scan interval only)."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self._config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        schema = vol.Schema(
            {vol.Required(CONF_SCAN_INTERVAL, default=current): int}
        )
        return self.async_show_form(step_id="init", data_schema=schema)
