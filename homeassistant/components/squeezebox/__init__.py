"""The Squeezebox integration."""

from asyncio import timeout
import logging

from pysqueezebox import Server

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)

from .const import (
    CONF_HTTPS,
    DATA_COORDINATOR,
    DATA_DEVICE,
    DATA_SERVER,
    DISCOVERY_TASK,
    DOMAIN,
    MANUFACTURER,
    PLAYER_DISCOVERY_UNSUB,
    SERVER_MODEL,
    STATUS_API_TIMEOUT,
    STATUS_QUERY_LIBRARYNAME,
    STATUS_QUERY_MAC,
    STATUS_QUERY_UUID,
    STATUS_QUERY_VERSION,
)
from .coordinator import LMSStatusDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SENSOR, Platform.BINARY_SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an LMS Server from a config entry."""
    config = entry.data
    session = async_get_clientsession(hass)
    _LOGGER.debug("Reached async_setup_entry for host=%s(%s)", config[CONF_HOST],entry.entry_id)

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    https = config.get(CONF_HTTPS, False)
    host = config[CONF_HOST]
    port = config[CONF_PORT]

    hass.data.setdefault(DOMAIN, {})
    entry.runtime_data = {}

    lms = Server(session, host, port, username, password, https=https)
    _LOGGER.debug("LMS object for %s", lms)

    try:
       async with timeout(STATUS_API_TIMEOUT):
          status = await lms.async_query("serverstatus","-","-","prefs:libraryname")
    except Exception as err:
       raise ConfigEntryNotReady(f"Error communicating config not read for {host}") from err

    if not status:
       raise ConfigEntryNotReady(f"Error Config Not read for {host}")
    _LOGGER.debug("LMS Status for setup  = %s", status)

    lms.uuid = status[STATUS_QUERY_UUID]
    lms.name = (STATUS_QUERY_LIBRARYNAME in status and status[STATUS_QUERY_LIBRARYNAME]) and status[STATUS_QUERY_LIBRARYNAME] or host
    _LOGGER.debug("LMS %s = '%s' with uuid = %s ", lms.name, host, lms.uuid)

    device = DeviceInfo(
            identifiers={
                (DOMAIN, lms.uuid)
            },
            name=lms.name,
            manufacturer=MANUFACTURER,
            model=SERVER_MODEL,
            sw_version=STATUS_QUERY_VERSION in status and status[STATUS_QUERY_VERSION] or None,
            serial_number=lms.uuid,
            connections = STATUS_QUERY_MAC in status and {(CONNECTION_NETWORK_MAC, format_mac(status[STATUS_QUERY_MAC]))} or None,
        )
    _LOGGER.debug("LMS Device %s", device)

    coordinator = LMSStatusDataUpdateCoordinator(hass, lms)

    entry.runtime_data[DATA_COORDINATOR] = coordinator
    entry.runtime_data[DATA_DEVICE] = device
    entry.runtime_data[DATA_SERVER] = lms

    await coordinator.async_config_entry_first_refresh()
    # Make sure data is present before we add the server status sensors
    # As always_update is false the data doesnt chanage and the entities don't get a value
    # unless we set the value at sensor init.
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Stop player discovery task for this config entry.
    _LOGGER.debug("Reached async_unload_entry for LMS=%s(%s)", entry.runtime_data[DATA_SERVER].name or "Unkown" ,entry.entry_id)
    entry.runtime_data[PLAYER_DISCOVERY_UNSUB]()

    # Remove redunant server/devices revmoves devices with no entities.
    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)
    for device_entry in dr.async_entries_for_config_entry(device_reg, entry.entry_id):
            # Do any of the devices for this entry have any entities(even if disabled) if not delete
            items = entity_reg.entities.get_entries_for_device_id(device_entry.id,True)
            if not items:
                _LOGGER.warning("Removing stale device %s", device_entry.name)
                device_reg.async_remove_device(device_entry.id)

    # Stop server discovery task if this is the last config entry.
    current_entries = hass.config_entries.async_entries(DOMAIN)
    if len(current_entries) == 1 and current_entries[0] == entry:
        _LOGGER.debug("Stopping server discovery task")
        hass.data[DOMAIN][DISCOVERY_TASK].cancel()
        hass.data[DOMAIN].pop(DISCOVERY_TASK)

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
