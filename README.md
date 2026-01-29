# Honeywell Transmission Risk Air Monitor (HTRAM) Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Custom component for Home Assistant to integrate the **Honeywell Transmission Risk Air Monitor (HTRAM)** via **Bluetooth Low Energy (BLE)**.

This integration was reverse-engineered from the official Android application to provide full local control without cloud dependency.

## ✨ Recent Improvements

- ✅ **Fixed CRC Calculation** - Now uses correct polynomial (0x8005) for reliable device communication
- ✅ **Automatic Reconnection** - Handles connection drops with exponential backoff retry
- ✅ **PIN Entry in UI** - Enter pairing PIN directly in Home Assistant (no terminal needed!)
- ✅ **Screen Timeout Fixed** - Properly sets screen auto-off timer
- ✅ **WiFi Configuration** - Provision WiFi credentials via service call

## Features

*   **Real-time Monitoring**:
    *   CO2 Levels (ppm)
    *   Temperature (°C/°F)
    *   Humidity (%)
    *   Battery Level (%) & Charging Status
*   **Device Control**:
    *   **Mute Alarm**: Toggle the buzzer sound on/off.
    *   **Screen Settings**: Set auto-off timer ("Always On" vs "Auto Off (2 min)").
    *   **Alarm Thresholds**: Customize Low (Green/Yellow) and High (Yellow/Red) CO2 thresholds.
    *   **Temperature Unit**: Switch between Celsius and Fahrenheit.
    *   **Time Sync**: Synchronize device time with Home Assistant (UTC).
    *   **WiFi Provisioning**: Configure device WiFi credentials.

## Installation

### Via HACS (Recommended)

1. **Add Custom Repository**:
   - Open HACS in Home Assistant
   - Click on **Integrations**
   - Click the **⋮** (three dots) menu in the top right
   - Select **Custom repositories**
   - Add your fork URL: `https://github.com/YOUR_USERNAME/ha-htram-fork`
   - Category: **Integration**
   - Click **Add**

2. **Install the Integration**:
   - Search for "HTRAM" in HACS Integrations
   - Click **Download**
   - Restart Home Assistant

3. **Add the Device**:
   - Go to **Settings** > **Devices & Services**
   - Click **+ Add Integration**
   - Search for "HTRAM"
   - Follow the setup wizard
   - If prompted, enter the 6-digit PIN shown on the device screen

### Manual Installation

1.  Download the `custom_components/htram` folder from this repository.
2.  Copy it to your Home Assistant's `config/custom_components/` directory.
3.  Restart Home Assistant.
4.  Add via Settings > Devices & Services > Add Integration > HTRAM.

## Configuration

### Device Setup

1. **Prepare the Device**:
   - Double-press the top button on your HTRAM device until the Bluetooth icon starts flashing
   - The device is now in pairing mode

2. **Add to Home Assistant**:
   - Go to **Settings** > **Devices & Services**
   - Click **+ Add Integration**
   - Search for "HTRAM"
   - Select your device from the list
   - If the device requires pairing, you'll see a PIN entry form
   - Check the device screen for the 6-digit PIN and enter it in Home Assistant
   - Click **Submit**

3. **Done!** Your device will appear with all sensors and controls available

### WiFi Provisioning (Optional)

If your device supports WiFi, you can configure it using a service call:

Due to limitations in the current auto-discovery logic, you must pair the device with your OS first.

**Using SSH / Terminal:**
1.  Open your terminal.
2.  Run `bluetoothctl`.
3.  Put your HTRAM device in **Pairing Mode** (double-press button, Bluetooth icon flashes).
4.  Run `scan on`.
5.  Wait for your device to appear (look for `HTRAM-...`).
6.  Run `pair XX:XX:XX:XX:XX:XX` (replace with MAC address).
    *   *Note*: If `pair` fails, try running `connect XX:XX:XX:XX:XX:XX` instead.
7.  If a PIN appears on the device, enter it. If not, it may pair automatically ("Just Works" mode).
8.  Once paired/connected, type `exit`.

### Step 2: Add Integration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for **HTRAM**.
4.  Select your paired device from the list.

## Usage

Once added, a new Device will be created with the following entities:

*   **Sensors**: `sensor.htram_co2`, `sensor.htram_temperature`, etc.
*   **Switch**: `switch.htram_mute` (Turn **ON** to mute the device).
*   **Selects**:
    *   `select.htram_screen_off_timer`: Choose "Always On" or "Auto Off (2 min)".
    *   `select.htram_temperature_unit`: Celsius / Fahrenheit.
*   **Numbers**:
    *   `number.htram_co2_alarm_low`: Threshold for yellow warning.
    *   `number.htram_co2_alarm_high`: Threshold for red alarm.
    *   `number.htram_co2_alarm_low`: Threshold for yellow warning.
    *   `number.htram_co2_alarm_high`: Threshold for red alarm.
*   **Select**: `select.htram_temperature_unit`.
*   **Button**: `button.htram_sync_time`.

## Troubleshooting

*   **Bluetooth Range**: Ensure the device is close to your Home Assistant host or a Bluetooth Proxy.
*   **Polling**: Data is updated every 60 seconds to save battery.
*   **Battery Level**: The device reports battery in "bars" (0-4). The integration estimates this as 0%, 25%, 50%, 75%, 100%.

## Disclaimer

This is an unofficial integration and is not affiliated with Honeywell. Use at your own risk.
