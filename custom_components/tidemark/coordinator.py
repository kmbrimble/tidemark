"""DataUpdateCoordinator for the Tidemark collector."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15


class TidemarkCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the collector's /usage endpoint and hands back the raw snapshot."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        bearer_token: str | None,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._url = f"http://{host}:{port}/usage"
        self._headers = {"Authorization": f"Bearer {bearer_token}"} if bearer_token else {}

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with session.get(self._url, headers=self._headers) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Collector returned HTTP {resp.status}")
                    return await resp.json(content_type=None)
        except ClientError as err:
            raise UpdateFailed(f"Cannot reach collector at {self._url}: {err}") from err
        except TimeoutError as err:
            raise UpdateFailed(f"Timed out reaching collector at {self._url}") from err
