"""Sensors for the Tidemark integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import parse_datetime

from .const import DOMAIN, PERIOD_KEYS
from .coordinator import TidemarkCoordinator
from .entity import TidemarkEntity

LIMIT_KINDS = ("session", "weekly_all", "weekly_scoped")


def _find_limit(data: dict[str, Any], kind: str) -> dict[str, Any] | None:
    for limit in data.get("claude", {}).get("limits", []):
        if limit.get("kind") == kind:
            return limit
    return None


class TidemarkLimitPercentSensor(TidemarkEntity, SensorEntity):
    """Session / weekly-all / weekly-scoped utilisation percent."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: TidemarkCoordinator, entry: ConfigEntry, kind: str) -> None:
        super().__init__(coordinator, entry)
        self._kind = kind
        self._attr_unique_id = f"{entry.entry_id}_{kind}_percent"
        self._attr_translation_key = f"{kind}_percent"

    @property
    def available(self) -> bool:
        return (
            super().available
            and self._section_ok("claude")
            and _find_limit(self.coordinator.data, self._kind) is not None
        )

    @property
    def native_value(self) -> int | None:
        limit = _find_limit(self.coordinator.data, self._kind)
        return limit.get("percent") if limit else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        limit = _find_limit(self.coordinator.data, self._kind) or {}
        trend = limit.get("trend") or {}
        return {
            "severity": limit.get("severity"),
            "resets_at": limit.get("resets_at"),
            "is_active": limit.get("is_active"),
            "window_seconds": limit.get("window_seconds"),
            "scope_model": limit.get("scope_model"),
            "pace_projected": limit.get("pace_projected"),
            "projected_end": limit.get("projected_end"),
            "projected_basis": limit.get("projected_basis"),
            "trend_rate_per_hour": trend.get("rate_per_hour"),
            "trend_projected_at_reset": trend.get("projected_at_reset"),
            "trend_samples": trend.get("samples"),
        }


class TidemarkTimeToLimitSensor(TidemarkEntity, SensorEntity):
    """Seconds until this window exhausts, if the collector can project it."""

    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: TidemarkCoordinator, entry: ConfigEntry, kind: str) -> None:
        super().__init__(coordinator, entry)
        self._kind = kind
        self._attr_unique_id = f"{entry.entry_id}_{kind}_time_to_limit"
        self._attr_translation_key = f"{kind}_time_to_limit"

    @property
    def available(self) -> bool:
        return (
            super().available
            and self._section_ok("claude")
            and _find_limit(self.coordinator.data, self._kind) is not None
        )

    @property
    def native_value(self) -> int | None:
        limit = _find_limit(self.coordinator.data, self._kind) or {}
        return limit.get("exhausts_in_seconds")


class TidemarkTokensSensor(TidemarkEntity, SensorEntity):
    """Total tokens used in a rolling period (today/week/month)."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "tokens"

    def __init__(self, coordinator: TidemarkCoordinator, entry: ConfigEntry, period: str) -> None:
        super().__init__(coordinator, entry)
        self._period = period
        self._attr_unique_id = f"{entry.entry_id}_tokens_{period}"
        self._attr_translation_key = f"tokens_{period}"

    def _period_data(self) -> dict[str, Any] | None:
        for period in (self.coordinator.data or {}).get("agent", {}).get("periods", []):
            if period.get("key") == self._period:
                return period
        return None

    @property
    def available(self) -> bool:
        return super().available and self._section_ok("agent") and self._period_data() is not None

    @property
    def native_value(self) -> int | None:
        period = self._period_data()
        return period.get("total_tokens") if period else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        period = self._period_data() or {}
        return dict(period.get("tokens") or {})


class TidemarkCostSensor(TidemarkEntity, SensorEntity):
    """Cost in the collector's reporting currency for a rolling period."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator: TidemarkCoordinator, entry: ConfigEntry, period: str) -> None:
        super().__init__(coordinator, entry)
        self._period = period
        self._attr_unique_id = f"{entry.entry_id}_cost_{period}"
        self._attr_translation_key = f"cost_{period}"

    def _period_data(self) -> dict[str, Any] | None:
        for period in (self.coordinator.data or {}).get("agent", {}).get("periods", []):
            if period.get("key") == self._period:
                return period
        return None

    @property
    def available(self) -> bool:
        return super().available and self._section_ok("agent") and self._period_data() is not None

    @property
    def native_unit_of_measurement(self) -> str | None:
        return (self.coordinator.data or {}).get("agent", {}).get("currency")

    @property
    def native_value(self) -> float | None:
        period = self._period_data()
        return period.get("cost_local") if period else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        period = self._period_data() or {}
        return {
            "cost_usd": period.get("cost_usd"),
            "models": period.get("models"),
        }


class TidemarkOpenRouterCreditsSensor(TidemarkEntity, SensorEntity):
    """OpenRouter key credit balance remaining."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "USD"

    def __init__(self, coordinator: TidemarkCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_openrouter_credits"
        self._attr_translation_key = "openrouter_credits"

    @property
    def available(self) -> bool:
        return super().available and self._section_ok("openrouter")

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("openrouter", {}).get("key", {}).get("remaining")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("openrouter", {})
        account = data.get("account") or {}
        key = data.get("key") or {}
        return {
            "account_total_credits": account.get("total_credits"),
            "account_total_usage": account.get("total_usage"),
            "account_remaining": account.get("remaining"),
            "key_limit": key.get("limit"),
            "key_usage": key.get("usage"),
            "key_limit_reset": key.get("limit_reset"),
            "key_usage_daily": key.get("usage_daily"),
            "key_usage_weekly": key.get("usage_weekly"),
            "key_usage_monthly": key.get("usage_monthly"),
        }


class TidemarkLastUpdatedSensor(TidemarkEntity, SensorEntity):
    """The snapshot's own generated_at timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: TidemarkCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_generated_at"
        self._attr_translation_key = "generated_at"

    @property
    def native_value(self):
        generated_at = (self.coordinator.data or {}).get("generated_at")
        return parse_datetime(generated_at) if generated_at else None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: TidemarkCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [TidemarkLastUpdatedSensor(coordinator, entry)]
    for kind in LIMIT_KINDS:
        entities.append(TidemarkLimitPercentSensor(coordinator, entry, kind))
        entities.append(TidemarkTimeToLimitSensor(coordinator, entry, kind))
    for period in PERIOD_KEYS:
        entities.append(TidemarkTokensSensor(coordinator, entry, period))
        entities.append(TidemarkCostSensor(coordinator, entry, period))
    entities.append(TidemarkOpenRouterCreditsSensor(coordinator, entry))

    async_add_entities(entities)
