"""Shared base entity for Tidemark: device grouping and section availability."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TidemarkCoordinator


class TidemarkEntity(CoordinatorEntity[TidemarkCoordinator]):
    """Common device grouping for every Tidemark entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TidemarkCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="kmbrimble/claude-usage-widget",
            model="Tidemark collector",
        )

    def _section_ok(self, section: str) -> bool:
        data: dict[str, Any] = self.coordinator.data or {}
        return bool(data.get(section, {}).get("ok", False))
