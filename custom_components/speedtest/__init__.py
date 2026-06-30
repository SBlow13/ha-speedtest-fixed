from __future__ import annotations

from datetime import timedelta
import json
import logging
import os
import platform
import subprocess
import tarfile
import tempfile
import urllib.request

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SERVER_ID, CONF_UPDATE_INTERVAL, DOMAIN, SENSOR_TYPES

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

SPEEDTEST_BIN = os.path.join(os.path.dirname(__file__), "speedtest-bin", "speedtest")

OOKLA_BASE = "https://install.speedtest.net/app/cli/"
OOKLA_VERSION = "1.2.0"

ARCH_MAP = {
    "x86_64": f"ookla-speedtest-{OOKLA_VERSION}-linux-x86_64.tgz",
    "i386": f"ookla-speedtest-{OOKLA_VERSION}-linux-i386.tgz",
    "i686": f"ookla-speedtest-{OOKLA_VERSION}-linux-i386.tgz",
    "aarch64": f"ookla-speedtest-{OOKLA_VERSION}-linux-aarch64.tgz",
    "armv7l": f"ookla-speedtest-{OOKLA_VERSION}-linux-armhf.tgz",
    "armv6l": f"ookla-speedtest-{OOKLA_VERSION}-linux-armel.tgz",
}


def _install_binary_sync():
    if os.path.isfile(SPEEDTEST_BIN):
        return

    arch = platform.machine()
    filename = ARCH_MAP.get(arch)
    if not filename:
        raise RuntimeError(f"Unsupported architecture: {arch}")

    url = OOKLA_BASE + filename
    bindir = os.path.dirname(SPEEDTEST_BIN)
    os.makedirs(bindir, exist_ok=True)

    _LOGGER.info("Downloading Speedtest CLI from %s", url)
    data = urllib.request.urlopen(url, timeout=120).read()

    with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as f:
        f.write(data)
        tmppath = f.name

    try:
        with tarfile.open(tmppath, "r:gz") as tar:
            tar.extract("speedtest", path=bindir)
        os.chmod(SPEEDTEST_BIN, 0o755)
    finally:
        os.unlink(tmppath)


def _run_speedtest_binary(server_id):
    if not os.path.isfile(SPEEDTEST_BIN):
        _install_binary_sync()

    cmd = [SPEEDTEST_BIN, "--format=json", "--accept-license", "--accept-gdpr"]
    if server_id:
        cmd.extend(["--server-id", str(server_id)])

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Speedtest CLI failed (code {result.returncode}): {result.stderr}"
        )
    return json.loads(result.stdout)


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
            data = await self.hass.async_add_executor_job(
                _run_speedtest_binary, self.server_id
            )
            return {
                "ping": round(data.get("ping", {}).get("latency"), 1),
                "download": round(
                    data.get("download", {}).get("bandwidth", 0) * 8 / 1_000_000, 1
                ),
                "upload": round(
                    data.get("upload", {}).get("bandwidth", 0) * 8 / 1_000_000, 1
                ),
                "jitter": round(data.get("ping", {}).get("jitter"), 1),
                "packet_loss": data.get("packetLoss"),
                "server": data.get("server", {}).get("name"),
                "server_id": data.get("server", {}).get("id"),
                "timestamp": data.get("timestamp"),
            }
        except Exception as err:
            raise UpdateFailed(f"Speedtest failed: {err}") from err
