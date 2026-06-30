# Speedtest for Home Assistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=SBlow13&repository=ha-speedtest-fixed&category=integration)

Run internet speed tests using the **official Ookla Speedtest CLI** directly in Home Assistant.

## Features

- **Ping** sensor (ms)
- **Download** sensor (Mbit/s)
- **Upload** sensor (Mbit/s)
- **Jitter** sensor (ms)
- **Packet Loss** sensor (%)
- Configurable update interval via UI
- Optional Speedtest server ID selection
- `speedtest.run_speedtest` service for manual triggers
- Automatically downloads the official Ookla Speedtest binary (no system package needed)

## Installation

1. Click the badge above or add manually via HACS as a custom repository
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration → Speedtest**
4. Configure update interval and optional server ID

The official Speedtest CLI binary is downloaded automatically during setup.
