from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES
from . import SpeedtestDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SpeedtestDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SpeedtestSensor(coordinator, entry, sensor_type)
        for sensor_type in SENSOR_TYPES
    )


class SpeedtestSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SpeedtestDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Speedtest",
            manufacturer="Ookla",
            model="Speedtest",
            sw_version="1.0.0",
        )

        sensor_config = SENSOR_TYPES[sensor_type]
        self._attr_name = sensor_config["name"]
        self._attr_native_unit_of_measurement = sensor_config[
            "native_unit_of_measurement"
        ]
        self._attr_icon = sensor_config["icon"]
        self._attr_state_class = sensor_config["state_class"]

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._sensor_type)
