import logging
import voluptuous as vol

from homeassistant.components.media_player.const import MediaType
from homeassistant.helpers import config_validation as cv
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import *
from .media_player import WiiMData

# List the platforms that your integration supports.
PLATFORMS = ["media_player"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the WiiM integration from a config entry."""
    # Create integration-level data storage if it doesn't exist.
    hass.data.setdefault(DOMAIN, {})

    # (Optional) Store a shared instance of your global data object.
    hass.data[DOMAIN]["data"] = WiiMData()

    # Forward the config entry to the supported platforms.
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_setups(entry, [platform])
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await hass.config_entries.async_forward_entry_unload(entry, platform)
        for platform in PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

CMND_SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_CMD): cv.string,
    vol.Optional(ATTR_NOTIF, default=True): cv.boolean
})

PLAY_URL_SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
    vol.Required(ATTR_URL): cv.string
})

PRESET_BUTTON_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_PRESET): cv.positive_int
})


_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Handle service configuration."""

    async def async_service_handle(service):
        """Handle services."""
        _LOGGER.debug("DOMAIN: %s, entities: %s", DOMAIN, str(hass.data[DOMAIN].entities))
        _LOGGER.debug("Service_handle from id: %s", service.data.get(ATTR_ENTITY_ID))
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        entities = hass.data[DOMAIN].entities

        if entity_ids:
            if entity_ids == 'all':
                entity_ids = [e.entity_id for e in entities]
            entities = [e for e in entities if e.entity_id in entity_ids]

        if service.service == SERVICE_CMD:
            command = service.data.get(ATTR_CMD)
            notify = service.data.get(ATTR_NOTIF)
            for device in entities:
                if device.entity_id in entity_ids:
                    _LOGGER.debug("**COMMAND** entity: %s; command: %s", device.entity_id, command)
                    await device.async_execute_command(command, notify)
        elif service.service == SERVICE_PLAY_URL:
            url = service.data.get(ATTR_URL)
            for device in entities:
                if device.entity_id in entity_ids:
                    _LOGGER.debug("**PLAY URL** entity: %s; url: %s", device.entity_id, url)
                    await device.async_play_media(MediaType.URL, url)

        elif service.service == SERVICE_PRESET:
            preset = service.data.get(ATTR_PRESET)
            for device in entities:
                if device.entity_id in entity_ids:
                    _LOGGER.debug("**PRESET** entity: %s; preset: %s", device.entity_id, preset)
                    await device.async_preset_button(preset)

    hass.services.async_register(
        DOMAIN, SERVICE_CMD, async_service_handle, schema=CMND_SERVICE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_URL, async_service_handle, schema=PLAY_URL_SERVICE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_PRESET, async_service_handle, schema=PRESET_BUTTON_SCHEMA)

    return True
