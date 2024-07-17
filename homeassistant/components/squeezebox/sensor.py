"""Platform for sensor integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DATA_DEVICE,
    DATA_SERVER,
    DOMAIN,
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

SENSORS: dict[str, SensorEntityDescription] = {
    STATUS_SENSOR_INFO_TOTAL_ALBUMS: SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_ALBUMS,
        state_class = SensorStateClass.TOTAL,
        icon = "mdi:album"
    ),
    STATUS_SENSOR_INFO_TOTAL_ARTISTS: SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_ARTISTS,
        state_class = SensorStateClass.TOTAL,
        icon = "mdi:account-music"
    ),
    STATUS_SENSOR_INFO_TOTAL_DURATION: SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_DURATION,
        state_class = SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    STATUS_SENSOR_INFO_TOTAL_GENRES: SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_GENRES,
        state_class = SensorStateClass.TOTAL,
        icon = "mdi:music-box-multiple" ,
    ),
    STATUS_SENSOR_INFO_TOTAL_SONGS: SensorEntityDescription(
        key=STATUS_SENSOR_INFO_TOTAL_SONGS,
        state_class = SensorStateClass.TOTAL,
        icon = "mdi:file-music"
    ),
    STATUS_SENSOR_LASTSCAN: SensorEntityDescription(
        key=STATUS_SENSOR_LASTSCAN,
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    STATUS_SENSOR_NEWPLUGINS: SensorEntityDescription(
        key=STATUS_SENSOR_NEWPLUGINS,
    ),
    STATUS_SENSOR_NEWVERSION: SensorEntityDescription(
        key=STATUS_SENSOR_NEWVERSION,
        entity_registry_visible_default=False,
    ),
    STATUS_SENSOR_PLAYER_COUNT: SensorEntityDescription(
        key=STATUS_SENSOR_PLAYER_COUNT,
        state_class = SensorStateClass.TOTAL,
        icon = "mdi:folder-play"
    ),
    STATUS_SENSOR_OTHER_PLAYER_COUNT: SensorEntityDescription(
        key=STATUS_SENSOR_OTHER_PLAYER_COUNT,
        state_class = SensorStateClass.TOTAL,
        entity_registry_visible_default=False,
        icon = "mdi:folder-play-outline" ,
    ),
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Platform setup using common elements."""

    lms = hass.data[DOMAIN][entry.entry_id][DATA_SERVER]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    device = hass.data[DOMAIN][entry.entry_id][DATA_DEVICE]

    sensors = []
    for sensor,description in SENSORS.items():
        sensors.append(ServerStatusSensor(device, lms, sensor, coordinator, description))

    async_add_entities(sensors)


class ServerStatusSensor(CoordinatorEntity, SensorEntity):
    """LMS Status based sensor from LMS via cooridnatior."""

    def __init__(self, device, lms, sensor, coordinator, description) -> None:
        """Initialize the sensor using dscription and name based server name plus instance name."""
        super().__init__(coordinator, context=sensor)
        self._attr_unique_id = lms.uuid
        self._attr_unique_id += sensor
        self._device = device
        self._sensor = sensor
        # device.name? and loose lms? is this needed?
        self._prefix = lms.name and lms.name + " " or "LMS "
        self.coordinator = coordinator
        self.native_value = self.coordinator.data[self._sensor]
        self.entity_description = description

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.native_value = self.coordinator.data[self._sensor]
        _LOGGER.debug("Update Sensor %s=%s", self._sensor, self.native_value)
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Common Sensor Device ie server instance."""
        return self._device

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._prefix + self._sensor
