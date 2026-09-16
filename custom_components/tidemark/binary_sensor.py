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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TidemarkStaleBinarySensor(coordinator, entry)])
