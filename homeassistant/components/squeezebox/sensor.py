"""Platform for sensor integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SqueezeboxConfigEntry
from .const import (
    STATUS_SENSOR_INFO_TOTAL_ALBUMS,
    STATUS_SENSOR_INFO_TOTAL_ARTISTS,
    STATUS_SENSOR_INFO_TOTAL_DURATION,
    STATUS_SENSOR_INFO_TOTAL_GENRES,
    STATUS_SENSOR_INFO_TOTAL_SONGS,
    STATUS_SENSOR_LASTSCAN,
    STATUS_SENSOR_NEWPLUGINS,
    STATUS_SENSOR_NEWVERSION,
    STATUS_SENSOR_OTHER_PLAYER_COUNT,
    STATUS_SENSOR_PLAYER_COUNT,
)
from .coordinator import LMSStatusDataUpdateCoordinator

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_ALBUMS,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:album",
    ),
    SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_ARTISTS,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:account-music",
    ),
    SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_DURATION,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_GENRES,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:drama-masks",
    ),
    SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_SONGS,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:file-music",
    ),
    SensorEntityDescription(
        key=STATUS_SENSOR_LASTSCAN,
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key=STATUS_SENSOR_NEWPLUGINS,
        entity_registry_visible_default=False,
    ),
    SensorEntityDescription(
        key=STATUS_SENSOR_NEWVERSION,
        entity_registry_visible_default=False,
    ),
    SensorEntityDescription(
        key=STATUS_SENSOR_PLAYER_COUNT,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:folder-play",
    ),
    SensorEntityDescription(
        key=STATUS_SENSOR_OTHER_PLAYER_COUNT,
        state_class=SensorStateClass.TOTAL,
        entity_registry_visible_default=False,
        icon="mdi:folder-play-outline",
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SqueezeboxConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Platform setup using common elements."""

    async_add_entities(
        ServerStatusSensor(
            entry.runtime_data.device, entry.runtime_data.coordinator, description
        )
        for description in SENSORS
    )


class ServerStatusSensor(CoordinatorEntity, SensorEntity):
    """LMS Status based sensor from LMS via cooridnatior."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device,
        coordinator: LMSStatusDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor using description, device and coordinator data."""
        super().__init__(coordinator, context=description.key)
        self.entity_description = description
        self.coordinator = coordinator
        self.native_value = coordinator.data[description.key]
        self._attr_device_info = device
        self._attr_name = description.key
        self._attr_unique_id = device["serial_number"]
        self._attr_unique_id += description.key

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.native_value = self.coordinator.data[self.entity_description.key]
        _LOGGER.debug(
            "Update Sensor %s=%s", self.entity_description.key, self.native_value
        )
        self.async_write_ha_state()
