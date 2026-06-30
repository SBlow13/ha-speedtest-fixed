from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_SERVER_ID, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SERVER_ID, default=""): str,
        vol.Optional(
            CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
        ): vol.All(vol.Coerce(int), vol.Range(min=1)),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    from . import _run_speedtest_binary

    try:
        server_id = data.get(CONF_SERVER_ID)
        await hass.async_add_executor_job(_run_speedtest_binary, server_id)
    except Exception as err:
        raise CannotConnect from err

    return {"title": "Speedtest"}


class SpeedtestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                if not user_input.get(CONF_SERVER_ID):
                    user_input[CONF_SERVER_ID] = None
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> dict[str, Any]:
        return await self.async_step_user(user_input)


class CannotConnect(HomeAssistantError):
    pass
