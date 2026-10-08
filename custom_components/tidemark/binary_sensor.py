"""Stale binary sensor for the Tidemark integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TidemarkCoordinator
from .entity import TidemarkEntity


class TidemarkStaleBinarySensor(TidemarkEntity, BinarySensorEntity):
    """On if any section of the last snapshot was marked stale."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "stale"

    def __init__(self, coordinator: TidemarkCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_stale"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return any(
            data.get(section, {}).get("stale", False)
            for section in ("claude", "openrouter", "agent")
        )


class TidemarkLoginNeededBinarySensor(TidemarkEntity, BinarySensorEntity):
    """On when the collector's credential needs a human login soon, or already.

    Unlike the other entities this stays available when the claude section is
    failing — a credential that can no longer be renewed is precisely what a
    reader needs to be told when the figures have stopped.
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "login_needed"

    def __init__(self, coordinator: TidemarkCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_login_needed"

    def _login(self) -> dict:
        return (self.coordinator.data or {}).get("claude", {}).get("login") or {}

    @property
    def is_on(self) -> bool:
        return bool(self._login().get("warning", False))

    @property
    def extra_state_attributes(self) -> dict:
        login = self._login()
        return {
            "expired": login.get("expired", False),
            "days_remaining": login.get("days_remaining"),
            "expires_at": login.get("refresh_token_expires_at"),
            "note": login.get("note"),
        }


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TidemarkStaleBinarySensor(coordinator, entry),
            TidemarkLoginNeededBinarySensor(coordinator, entry),
        ]
    )
