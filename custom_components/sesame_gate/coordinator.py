"""Coordinator: polls whoami for availability + access-point discovery."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SesameApiClient, SesameAuthError, SesameConnectionError, SesameData
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SesameCoordinator(DataUpdateCoordinator[SesameData]):
    """Calls whoami periodically.

    - success     -> device available + ``data`` = identity/access points.
    - 401         -> ``ConfigEntryAuthFailed`` -> HA starts re-auth.
    - network/5xx -> ``UpdateFailed`` -> entities go "unavailable" (no illusion
      that an open is possible). NB: whoami 200 proves the token + backend
      respond, NOT that the access will physically open - a real open failure
      surfaces on press (see button.py).
    """

    def __init__(self, hass: HomeAssistant, api: SesameApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> SesameData:
        try:
            return await self.api.whoami()
        except SesameAuthError as err:
            raise ConfigEntryAuthFailed("Sesame token revoked or invalid") from err
        except SesameConnectionError as err:
            raise UpdateFailed(f"Sesame unreachable: {err}") from err
