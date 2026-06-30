from __future__ import annotations

from datetime import timedelta
import logging

import speedtest

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SERVER_ID, CONF_UPDATE_INTERVAL, DOMAIN, SENSOR_TYPES

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = SpeedtestDataUpdateCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, coordinator.first_refresh)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_run_speedtest(call):
        await coordinator.async_refresh()

    hass.services.async_register(DOMAIN, "run_speedtest", handle_run_speedtest)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class SpeedtestDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.server_id = entry.data.get(CONF_SERVER_ID)
        update_interval = entry.data.get(CONF_UPDATE_INTERVAL, 60)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            update_interval=timedelta(minutes=update_interval),
        )

    async def first_refresh(self, _=None):
        await self.async_refresh()

    async def _async_update_data(self):
        try:
            def _run_speedtest():
                st = speedtest.Speedtest()
                if self.server_id:
                    st.get_servers([self.server_id])
                st.get_best_server()
                st.download()
                st.upload()
                return st.results.dict()

            data = await self.hass.async_add_executor_job(_run_speedtest)

            return {
                "ping": data.get("ping"),
                "download": data.get("download") / 1_000_000 if data.get("download") else 0,
                "upload": data.get("upload") / 1_000_000 if data.get("upload") else 0,
                "server": data.get("server", {}).get("name"),
                "server_id": data.get("server", {}).get("id"),
                "timestamp": data.get("timestamp"),
            }

        except Exception as err:
            raise UpdateFailed(f"Speedtest failed: {err}") from err
