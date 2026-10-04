"""Coordinator: whoami OK -> available + access; 401 -> AuthFailed; net -> UpdateFailed."""

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.sesame_gate.api import SesameApiClient
from custom_components.sesame_gate.coordinator import SesameCoordinator

from .const import ENTRY_DATA, TOKEN, WHOAMI_OK, WHOAMI_URL


def _coordinator(hass: HomeAssistant) -> SesameCoordinator:
    session = async_get_clientsession(hass)
    api = SesameApiClient(session, ENTRY_DATA["url"], TOKEN)
    return SesameCoordinator(hass, api)


async def test_coordinator_ok(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """whoami 200 -> success, normalised data (identity + access points)."""
    aioclient_mock.get(WHOAMI_URL, json=WHOAMI_OK)
    coordinator = _coordinator(hass)

    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.data.account_id == WHOAMI_OK["coloti_id"]
    assert coordinator.data.account_name == "Alice B."
    assert coordinator.data.points_acces == ["gate", "garage"]


async def test_coordinator_401_auth_failed(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """whoami 401 -> ConfigEntryAuthFailed (triggers re-auth)."""
    aioclient_mock.get(WHOAMI_URL, status=401)
    coordinator = _coordinator(hass)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_coordinator_network_update_failed(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Network error -> UpdateFailed -> entities unavailable."""
    aioclient_mock.get(WHOAMI_URL, exc=aiohttp.ClientError)
    coordinator = _coordinator(hass)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    # via async_refresh: no exception, but last_update_success=False.
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
