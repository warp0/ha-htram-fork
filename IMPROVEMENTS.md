# HTRAM Integration Improvements

This document details the improvements made to the Home Assistant HTRAM integration based on the reference implementation at https://github.com/noname122021/honeywell-htram-v1w-ble-monitor

## Summary of Changes

### 1. ✅ Improved BLE Reconnection Handling

**Problem:** When Bluetooth connection drops, the device cannot reconnect without restarting.

**Solution:** Implemented robust reconnection logic with automatic retry mechanism:

- **Connection Lock:** Added `asyncio.Lock()` to prevent concurrent connection attempts
- **Retry Logic:** Automatic retry up to 3 times with exponential backoff (1s, 2s, 4s)
- **Connection Health Check:** Tests existing connections before reuse with `get_services()`
- **Graceful Cleanup:** Proper disconnect and cleanup on failures
- **Error Tracking:** Detailed logging for debugging connection issues

**Changed Files:**
- `coordinator.py`:
  - Added `_connection_lock`, `_reconnect_attempts`, `_max_reconnect_attempts`
  - Refactored `_async_update_data()` to use retry wrapper
  - New methods: `_fetch_data_with_retry()`, `_do_fetch_data()`
  - Improved `_cleanup_client()` with better error handling

### 2. ✅ Fixed Screen Timeout CRC Error

**Problem:** Missing `_crc16` method causing AttributeError when setting screen timeout, AND incorrect CRC polynomial causing communication failures.

**Solution:** 
- Added `_crc16()` method to coordinator that uses `utils.CRC16.crc16_short()`
- **CRITICAL FIX:** Corrected CRC16 implementation to use polynomial **0x8005** (not 0x1021)
- Updated CRC16_TABLE to exactly match the reference implementation from [air_monitor.py](https://github.com/noname122021/honeywell-htram-v1w-ble-monitor/blob/main/air_monitor.py#L14-L48)
- Removed duplicate `async_set_screen_off()` method
- Verified CRC byte order matches device expectations (big-endian)
- Fixed duplicate `CMD_HEARTBEAT` import

**Changed Files:**
- `coordinator.py`:
  - Added `def _crc16(self, data: bytes) -> int`
  - Removed duplicate `async_set_screen_off()` definition
  - Cleaned up duplicate imports
- `utils.py`:
  - **Replaced entire CRC16 class** with correct implementation using polynomial 0x8005
  - Updated CRC16_TABLE with exact values from reference
  - Simplified algorithm to match reference exactly

### 3. ✅ Enhanced Pairing Process

**Problem:** No guidance for PIN-based pairing during setup.

**Solution:** While Home Assistant doesn't support inline PIN dialogs during BLE pairing (pairing happens at OS level), we improved the user experience:

- **Enhanced Instructions:** Added detailed pairing instructions in config flow
- **PIN Information:** Documents default PINs (000000 or 123456)
- **Step-by-Step Guide:** Clear instructions for activating pairing mode
- **Error Messages:** Improved error messages for pairing failures

**Changed Files:**
- `config_flow.py`: Enhanced description placeholders and error handling
- `translations/en.json`: Added comprehensive pairing instructions

**Note:** BLE pairing in Home Assistant happens at the operating system level. Users will see OS-native PIN prompts when needed. The integration provides clear instructions but cannot programmatically display PIN entry dialogs within HA.

### 4. ✅ Fixed WiFi Configuration

**Problem:** Missing `asyncio` import and duplicate coordinator references.

**Solution:**
- Added missing `asyncio` import for delay between commands
- Removed duplicate coordinator assignment
- Improved error handling with try-catch blocks
- Added detailed logging for configuration steps

**Changed Files:**
- `__init__.py`:
  - Added `import asyncio`
  - Removed duplicate `hass.data[DOMAIN][entry.entry_id] = coordinator` line
  - Enhanced `handle_configure_device()` with better error handling and logging

## Technical Details

### Reconnection Algorithm

The new reconnection logic follows this flow:

```python
1. Lock acquired (prevents concurrent attempts)
2. For each attempt (max 3):
   a. Try to fetch data
   b. On failure:
      - Clean up connection
      - Wait with exponential backoff
      - Retry
3. If all attempts fail, raise UpdateFailed
```

### CRC Calculation

The CRC16 implementation matches the device's expectations:
- **Polynomial:** 0x8005 (NOT 0x1021 - this was a critical bug!)
- **Algorithm:** Table lookup with `idx = ((crc >> 8) ^ byte) & 0xFF`
- **Initial Value:** 0
- **Byte Order:** Big-endian (network byte order)
- **Implementation:** Exact copy from [reference air_monitor.py](https://github.com/noname122021/honeywell-htram-v1w-ble-monitor/blob/main/air_monitor.py#L51-L56)

**Important:** The previous implementation was using the wrong polynomial (0x1021 for CCITT) which would cause all CRC checks to fail. This has been corrected to use 0x8005 as required by the device.

### WiFi Provisioning Protocol

The WiFi configuration follows the device's packet structure:
- **Command:** `0x7460` (submitSSID)
- **Format:** Header + Zeros(22) + PwdLen(1) + Password(64) + SSID(33) + Zeros(33) + CRC(2) + Tail(0x7D)
- **Sequence:** MQTT config first (if provided), then WiFi config with 1s delay

## Testing Recommendations

### 1. Test Reconnection
```bash
# While monitoring logs:
1. Start integration
2. Move device out of range
3. Wait for connection drop
4. Move device back in range
5. Verify automatic reconnection
```

### 2. Test Screen Timeout
```yaml
# In Home Assistant Developer Tools > Services
service: number.set_value
target:
  entity_id: number.htram_screen_timeout
data:
  value: 30
```

### 3. Test WiFi Configuration
```yaml
# In Home Assistant Developer Tools > Services
service: htram.configure_device
data:
  ssid: "YourWiFiSSID"
  password: "YourWiFiPassword"
```

## Known Limitations

1. **PIN Entry:** Cannot show PIN dialog within HA - users must respond to OS-level prompts
2. **Single Device Service:** WiFi config service applies to all configured HTRAM devices
3. **AES Key Format:** MQTT AES key should be Base64-encoded (matches Android app behavior)

## Reference Documentation

- Original Python Implementation: https://github.com/noname122021/honeywell-htram-v1w-ble-monitor/blob/main/air_monitor.py
- Protocol Documentation: https://github.com/noname122021/honeywell-htram-v1w-ble-monitor/blob/main/PROTOCOL.md
- Web Dashboard: https://github.com/noname122021/honeywell-htram-v1w-ble-monitor/tree/main/web

## Future Improvements

1. **Device-Targeted Services:** Add device_id parameter to WiFi config service
2. **History Download:** Implement historical data download (90 days capability)
3. **Firmware Update:** Add OTA firmware update support
4. **Advanced Settings:** Expose more device settings (NB-IoT, Zigbee, etc.)
5. **Connection Status Sensor:** Add sensor showing connection state and signal strength
