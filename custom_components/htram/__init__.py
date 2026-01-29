"""The HTRAM integration."""
import asyncio
import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import HTRAMDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.SELECT, Platform.BUTTON]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HTRAM from a config entry."""
    address = entry.unique_id
    assert address is not None

    ble_device = bluetooth.async_ble_device_from_address(hass, address.upper(), connectable=True)
    if not ble_device:
        raise ConfigEntryNotReady(f"Could not find HTRAM device with address {address}")

    coordinator = HTRAMDataUpdateCoordinator(hass, ble_device)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register Service
    async def handle_configure_device(call):
        """Handle the service call."""
        ssid = call.data.get("ssid")
        password = call.data.get("password")
        mqtt_server = call.data.get("mqtt_server")
        aes_key = call.data.get("aes_key")
        aes_iv = call.data.get("aes_iv")
        
        # Apply configuration to all configured HTRAM devices
        # In a production system, you might want to add device targeting
        for entry_id, coord in hass.data[DOMAIN].items():
            try:
                # Send MQTT configuration first if provided
                if mqtt_server and aes_key and aes_iv:
                    _LOGGER.info(f"Provisioning MQTT for device {coord.address}")
                    await coord.async_provision_mqtt(mqtt_server, aes_key, aes_iv)
                    # Small delay between commands
                    await asyncio.sleep(1)
                
                # Then send WiFi configuration if provided
                if ssid and password:
                    _LOGGER.info(f"Provisioning WiFi for device {coord.address}: SSID={ssid}")
                    await coord.async_provision_wifi(ssid, password)
                    _LOGGER.info(f"WiFi provisioning completed for {coord.address}")
                    
            except Exception as e:
                _LOGGER.error(f"Failed to configure device {coord.address}: {e}", exc_info=True)

    import voluptuous as vol
    from homeassistant.helpers import config_validation as cv

    SERVICE_SCHEMA = vol.Schema({
        vol.Optional("ssid"): cv.string,
        vol.Optional("password"): cv.string,
        vol.Optional("mqtt_server"): cv.string,
        vol.Optional("aes_key"): cv.string,
        vol.Optional("aes_iv"): cv.string,
    })

    hass.services.async_register(DOMAIN, "configure_device", handle_configure_device, schema=SERVICE_SCHEMA)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
