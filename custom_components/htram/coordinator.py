
"""DataUpdateCoordinator for HTRAM."""
import asyncio
import logging
from datetime import timedelta
import async_timeout

from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection
from bleak_retry_connector import BleakClientWithServiceCache

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    WRITE_UUID,
    NOTIFY_UUID,
    CMD_GET_REALTIME,
    CMD_GET_SETTINGS,
    CMD_GET_SOUND_STATUS,
    CMD_SET_SOUND_OFF,
    CMD_SET_SOUND_ON,
    CMD_SET_TEMP_UNIT_C,
    CMD_SET_TEMP_UNIT_F,
    POLL_INTERVAL,
    CMD_CHANGE_BLE_MODE
)
from . import utils

_LOGGER = logging.getLogger(__name__)

class HTRAMDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HTRAM data."""

    def __init__(self, hass: HomeAssistant, ble_device: BLEDevice) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLL_INTERVAL),
        )
        self.ble_device = ble_device
        self.address = ble_device.address
        self.data = {}
        self._client = None
        self._connected = False  # Custom connection state
        self._realtime_future = None
        self._settings_future = None
        self._sound_future = None
        _LOGGER.info(f"Coordinator for {ble_device.address} initialized")

    def _disconnected_callback(self, client):
        _LOGGER.info(f"BLE client for {self.address} disconnected.")
        client.stop_notify(NOTIFY_UUID)
        self._connected = False

    async def _async_update_data(self):
        """Fetch data from the device, limiting concurrent BLE connections."""
        try:
            try:
                _LOGGER.debug(f"Coordinator updating: Check connection to {self.address}")

                if not self._client or not self._connected:
                    _LOGGER.debug("Previous connection lost, cleaning up")
                    _LOGGER.debug(f"Coordinator updating: Establishing NEW connection to {self.address}")

                    client = await establish_connection(
                        BleakClientWithServiceCache,
                        self.ble_device,
                        name=self.address,
                        disconnected_callback=self._disconnected_callback,
                        max_attempts=2,
                        use_services_cache=True,
                        timeout=10
                    )
                    self._client = client
                    self._connected = True
            except Exception as e:
                _LOGGER.error(f"Failed to establish connection: {e}")
            _LOGGER.debug(f"Coordinator connected: {self._connected}")
                

            try:
                await self._client.write_gatt_char(WRITE_UUID, CMD_CHANGE_BLE_MODE, response=False)
                _LOGGER.info(f"Sent BLE mode activation command to {self.address}")
            except Exception as e:
                _LOGGER.warning(f"Failed to send BLE mode activation: {e}")

            self._realtime_future = asyncio.Future()
            self._settings_future = asyncio.Future()
            self._sound_future = asyncio.Future()
                    
            def notification_handler(sender, data: bytearray):
                hex_data = data.hex()
                _LOGGER.debug(f"Received notification: {hex_data}")
                if len(data) < 6:
                    return
                cmd_id = data[4:6].hex()
                if cmd_id == "4144": # Realtime
                    if self._realtime_future and not self._realtime_future.done():
                        self._realtime_future.set_result(data)
                elif cmd_id == "4143": # Settings
                    if self._settings_future and not self._settings_future.done():
                        self._settings_future.set_result(data)
                elif cmd_id == "2723": # Sound status
                    if self._sound_future and not self._sound_future.done():
                        self._sound_future.set_result(data)
        
            await self._client.stop_notify(NOTIFY_UUID)
            await asyncio.sleep(0.2)
            await self._client.start_notify(NOTIFY_UUID, notification_handler)
            await asyncio.sleep(0.2)


            # 1. Get Realtime Data
            await self._client.write_gatt_char(WRITE_UUID, CMD_GET_REALTIME)
            await asyncio.sleep(0.5)
            try:
                data = await asyncio.wait_for(self._realtime_future, timeout=5.0)
                self._parse_realtime(data)
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for realtime data")

            # 2. Get Sound Status
            await self._client.write_gatt_char(WRITE_UUID, CMD_GET_SOUND_STATUS)
            await asyncio.sleep(0.5)
            try:
                data = await asyncio.wait_for(self._sound_future, timeout=5.0)
                self._parse_sound(data)
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for sound status")

            # 3. Get Settings
            await self._client.write_gatt_char(WRITE_UUID, CMD_GET_SETTINGS)
            await asyncio.sleep(0.5)
            try:
                data = await asyncio.wait_for(self._settings_future, timeout=5.0)
                self._parse_settings(data)
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for settings")
        except Exception as e:
            raise UpdateFailed(f"Error fetching data: {e}") from e

        try:
            await self._client.stop_notify(NOTIFY_UUID)
            _LOGGER.debug("Cleaned up stale BlueZ notification handles")
        except Exception:
            pass

        return self.data
    
    def _crc16(self, data: bytes) -> int:
        """Calculate CRC16 for the given data using standard CCITT polynomial."""
        return utils.CRC16.crc16_short(data)

    def _parse_realtime(self, data: bytearray):
        # Validation
        if len(data) < 13:
            _LOGGER.warning(f"Realtime data too short: {len(data)}")
            return

        co2 = int.from_bytes(data[7:9], byteorder='big')
        temp = data[9]
        if temp > 128:
            temp = temp - 256
        
        hum = data[10]
        batt_level = data[11]
        batt = batt_level * 25
        if batt > 100:
            batt = 100

        charging = data[12]

        self.data["co2"] = co2
        self.data["temperature"] = temp
        self.data["humidity"] = hum
        self.data["battery"] = batt
        self.data["charging"] = charging == 1

    def _parse_sound(self, data: bytearray):
        if len(data) < 10:
             _LOGGER.warning(f"Sound data too short: {len(data)}")
             return
        is_off = data[9] == 0 
        self.data["mute"] = is_off 

    def _parse_settings(self, data: bytearray):
        if len(data) < 13:
             _LOGGER.warning(f"Settings data too short: {len(data)}")
             return

        low = int.from_bytes(data[7:9], byteorder='big')
        high = int.from_bytes(data[9:11], byteorder='big')
        screen_off = int.from_bytes(data[11:13], byteorder='big')

        self.data["alarm_low"] = low
        self.data["alarm_high"] = high
        self.data["screen_off"] = screen_off 

    async def async_set_mute(self, mute: bool):
        """Set mute state."""
        # Use verified hardcoded packets from Java source
        cmd = CMD_SET_SOUND_OFF if mute else CMD_SET_SOUND_ON
        await self._send_command(cmd)
        self.data["mute"] = mute
        self.async_update_listeners()

    async def async_set_temp_unit(self, celsius: bool):
        """Set temperature unit."""
        cmd = CMD_SET_TEMP_UNIT_C if celsius else CMD_SET_TEMP_UNIT_F
        await self._send_command(cmd)
        # Update local state optimistically
        self.data["temp_unit"] = "C" if celsius else "F"
        self.async_update_listeners()

    async def _send_command(self, command: bytearray):
        """Send a command to the device."""
        
        _LOGGER.info(f"Sending command: {len(command)} bytes")
        _LOGGER.debug(f"Command hex: {command.hex()}")
             
        try:
            await self._client.write_gatt_char(WRITE_UUID, command, response=False)
            _LOGGER.info("Command sent successfully (reused connection)")
            return
        except Exception as e:
            _LOGGER.warning(f"Failed to send on existing connection: {e}")
            return

    async def async_set_alarm_thresholds(self, low: int | None = None, high: int | None = None, screen_off: int | None = None):
        """Set alarm thresholds and screen off timer."""
        # Get current values to fill in gaps
        current_low = self.data.get("alarm_low", 800)
        current_high = self.data.get("alarm_high", 1000)
        current_screen_off = self.data.get("screen_off", 0)

        new_low = low if low is not None else current_low
        new_high = high if high is not None else current_high
        new_screen_off = screen_off if screen_off is not None else current_screen_off

        # Validate logic: Low < High
        if new_low >= new_high:
            _LOGGER.warning(f"Low threshold ({new_low}) must be less than High ({new_high})")
            return

        # Build packet using "submitAlertValue" structure (Full Update)
        # Header: 7B 41 00 0F 42 43 04 00 40 06 [Lov V] [Hi V] [Screen V] [CRC] 7D
        # Len: 0x0F (15)
        # Cmd: 42 43
        # Magic: 04 00 40 06 (Matches Java submitAlertValue)
        
        packet = bytearray([0x7B, 0x41, 0x00, 0x0F, 0x42, 0x43, 0x04, 0x00, 0x40, 0x06])
        
        # Low (2 bytes Big Endian)
        packet.append((new_low >> 8) & 0xFF)
        packet.append(new_low & 0xFF)
        
        # High (2 bytes Big Endian)
        packet.append((new_high >> 8) & 0xFF)
        packet.append(new_high & 0xFF)
        
        # Screen Off (2 bytes Big Endian) - Pass current value to preserve it (assuming 3rd arg is Screen Off)
        packet.append((new_screen_off >> 8) & 0xFF)
        packet.append(new_screen_off & 0xFF)

        # CRC (Calculated on the first 16 bytes: Header(4) + Data(12))
        crc = self._crc16(packet)
        packet.append((crc >> 8) & 0xFF)
        packet.append(crc & 0xFF)
        packet.append(0x7D)

        await self._send_command(packet)
        
        # Optimistic update
        self.data["alarm_low"] = new_low
        self.data["alarm_high"] = new_high
        self.data["screen_off"] = new_screen_off
        self.async_update_listeners()

    async def async_set_screen_off(self, minutes: int):
         """Set screen off timer using dedicated command."""
         # Use 'submitScreenOffTime' packet structure
         # Header: 7B 41 00 0B 42 43 04 00 20 00 [VAL_HI] [VAL_LO] [CRC] 7D
         # Magic: 20 00
         
         val_hi = (minutes >> 8) & 0xFF
         val_lo = minutes & 0xFF
         
         packet = bytearray([0x7B, 0x41, 0x00, 0x0B, 0x42, 0x43, 0x04, 0x00, 0x20, 0x00, val_hi, val_lo])
         
         # CRC
         crc = self._crc16(packet)
         packet.append((crc >> 8) & 0xFF)
         packet.append(crc & 0xFF)
         packet.append(0x7D)
         
         await self._send_command(packet)
         self.data["screen_off"] = minutes
         self.async_update_listeners()

    async def async_sync_time(self):
        """Sync device time (UTC)."""
        import datetime
        now = datetime.datetime.utcnow()
        
        # Format: YY MM DD HH mm ss (decimal values as bytes)
        # Packet: 7B 41 00 0C 22 42 01 00 [YY] [MM] [DD] [HH] [mm] [ss] [CRC] 7D
        
        # Header + Cmd (22 42) + Flag (01)
        packet = bytearray([0x7B, 0x41, 0x00, 0x0C, 0x22, 0x42, 0x01])
        
        # Date parts (modulo 100 for year to get 2 digits)
        packet.append(now.year % 100)
        packet.append(now.month)
        packet.append(now.day)
        packet.append(now.hour)
        packet.append(now.minute)
        packet.append(now.second)
        
        # CRC
        crc = self._crc16(packet)
        packet.append((crc >> 8) & 0xFF)
        packet.append(crc & 0xFF)
        packet.append(0x7D)
        
        await self._send_command(packet)
        _LOGGER.info("Synced time to device (UTC)")

        return crc 

    async def async_provision_wifi(self, ssid: str, password: str):
        """Provision WiFi credentials."""
        from .const import CMD_CHANGE_BLE_MODE
        
        # Send BLE mode initialization first (required for V1W)
        _LOGGER.info(f"Sending BLE mode initialization for WiFi provisioning")
        await self._send_command(CMD_CHANGE_BLE_MODE)
        
        # Now send WiFi configuration
        packet = utils.construct_submit_ssid(ssid, password)
        _LOGGER.info(f"Provisioning WiFi: SSID={ssid}, Packet length={len(packet)}")
        _LOGGER.debug(f"WiFi packet hex: {packet.hex()}")
        await self._send_command(packet)
        _LOGGER.info(f"WiFi provisioning packet sent successfully")

    async def async_provision_mqtt(self, mqtt_server: str, aes_key: str, aes_iv: str):
        """Provision custom MQTT server."""
        packet = utils.construct_submit_aes_key(aes_key, aes_iv, mqtt_server)
        _LOGGER.info(f"Provisioning MQTT: Server={mqtt_server}, Packet length={len(packet)}")
        _LOGGER.debug(f"MQTT packet hex: {packet.hex()}")
        await self._send_command(packet)
        _LOGGER.info(f"MQTT provisioning packet sent successfully")
