"""Config flow: UI setup + re-authentication.

Auth via a ``Bearer`` API token. ``unique_id`` = the STABLE account identity
(``account_id``), NEVER the token: otherwise token rotation (the very case
re-auth must handle) would change the ``unique_id`` and re-auth could no longer
find the entry.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    SesameApiClient,
    SesameAuthError,
    SesameConnectionError,
    SesameData,
)
from .const import CONF_TOKEN, CONF_URL, DOMAIN


class SesameConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configuration flow for the Sesame integration."""

    VERSION = 1

    async def _validate(self, url: str, token: str) -> SesameData:
        """Validate the (url, token) pair via whoami. Raises on failure."""
        session = async_get_clientsession(self.hass)
        api = SesameApiClient(session, url, token)
        return await api.whoami()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Initial step: URL + token."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = await self._validate(
                    user_input[CONF_URL], user_input[CONF_TOKEN]
                )
            except SesameAuthError:
                errors["base"] = "invalid_auth"
            except SesameConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(data.account_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=data.account_name, data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL): str,
                    vol.Required(CONF_TOKEN): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Triggered by ``ConfigEntryAuthFailed``: ask for a new token."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate the new token; check it belongs to the SAME account."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                data = await self._validate(entry.data[CONF_URL], user_input[CONF_TOKEN])
            except SesameAuthError:
                errors["base"] = "invalid_auth"
            except SesameConnectionError:
                errors["base"] = "cannot_connect"
            else:
                # The new token must belong to the already-configured account
                # (a token from a DIFFERENT account is rejected cleanly).
                await self.async_set_unique_id(data.account_id)
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, CONF_TOKEN: user_input[CONF_TOKEN]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )
