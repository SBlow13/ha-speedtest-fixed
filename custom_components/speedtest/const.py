from homeassistant.const import TIME_MILLISECONDS

DOMAIN = "speedtest"
CONF_SERVER_ID = "server_id"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 60

SENSOR_TYPES = {
    "ping": {
        "name": "Ping",
        "native_unit_of_measurement": TIME_MILLISECONDS,
        "icon": "mdi:timeline-clock",
        "state_class": "measurement",
    },
    "download": {
        "name": "Download",
        "native_unit_of_measurement": "Mbit/s",
        "icon": "mdi:download-network",
        "state_class": "measurement",
    },
    "upload": {
        "name": "Upload",
        "native_unit_of_measurement": "Mbit/s",
        "icon": "mdi:upload-network",
        "state_class": "measurement",
    },
}

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{DOMAIN}
Version: %s
This is a custom integration for running internet speed tests.
-------------------------------------------------------------------
"""
