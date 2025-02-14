"""Control bluetooth speaker bulb."""
import logging

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_scanner_count,
)
from homeassistant.components.bluetooth.models import BluetoothScanningMode
from homeassistant.components.bluetooth.scanner import create_bleak_scanner
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from bluetooth_speaker_bulb import find_device_by_address

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bluetooth Speaker Bulb from a config entry."""
    _LOGGER.debug(f"integration async setup entry: {entry.as_dict()}")
    hass.data.setdefault(DOMAIN, {})

    # Find ble device here so that we can raise device not found on startup
    address = entry.data.get(CONF_MAC)

    # try to get ble_device using HA scanner first
    ble_device = async_ble_device_from_address(hass, address.upper(), connectable=True)
    _LOGGER.debug(f"BLE device through HA bt: {ble_device}")
    count = async_scanner_count(hass, connectable=True)
    _LOGGER.debug(f"Count of BLE devices through HA bt: {count}")
    if ble_device is None:
        # if bluetooth not enabled, we get ble_device from a bleak scanner returned by HA
        scanner = create_bleak_scanner(BluetoothScanningMode.ACTIVE, None)
        ble_device = await scanner.find_device_by_address(address.upper(), timeout=15)
        _LOGGER.debug(f"BLE device using bleak scanner through HA: {ble_device}")
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find Bluetooth Speaker Bulb with address {address}")

    hass.data[DOMAIN][entry.entry_id] = ble_device
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "light")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async unload entry")
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "light")

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.config_entries.async_entries(DOMAIN):
            hass.data.pop(DOMAIN)
    return unload_ok
