"""Platform for sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DATA_DEVICE,
    DOMAIN,
    STATUS_SENSOR_NEEDSRESTART,
    STATUS_SENSOR_RESCAN,
)

SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=STATUS_SENSOR_RESCAN,
        entity_registry_visible_default=False,
        device_class = BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key=STATUS_SENSOR_NEEDSRESTART,
        device_class = BinarySensorDeviceClass.UPDATE,
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Platform setup using common elements."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    device = hass.data[DOMAIN][entry.entry_id][DATA_DEVICE]

    async_add_entities(
        ServerStatusBinarySensor(device, coordinator, description)
        for description in SENSORS
    )


class ServerStatusBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """LMS Status based sensor from LMS via cooridnatior."""

    _attr_has_entity_name = True

    def __init__(self, device, coordinator, description) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, context=description.key)
        self.coordinator = coordinator
        self.entity_description = description
        self._sensor = description.key
        self._attr_device_info = device
        self._attr_is_on = self.coordinator.data[self._sensor]
        self._attr_name = self._sensor
        self._attr_unique_id = device["serial_number"]
        self._attr_unique_id += description.key

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data[self._sensor]
        _LOGGER.debug("Update %s=%s", self._sensor, self._attr_is_on)
        self.async_write_ha_state()
