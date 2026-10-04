"""Buttons: one per access point, async_press -> /api/ouvrir, refusal -> error."""

import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.sesame_gate.const import DOMAIN

from .const import ACCOUNT_ID, ENTRY_DATA, OPEN_URL, WHOAMI_OK, WHOAMI_URL


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=ACCOUNT_ID, data=ENTRY_DATA)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _teardown(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    # Unload the entry -> cancels the coordinator poll timer (otherwise HA's
    # test harness fails the test on a "lingering timer" at teardown).
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


def _entity_id(hass: HomeAssistant, point: str) -> str:
    eid = er.async_get(hass).async_get_entity_id(
        BUTTON_DOMAIN, DOMAIN, f"{ACCOUNT_ID}_{point}"
    )
    assert eid is not None
    return eid


async def test_setup_creates_one_button_per_access(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """whoami reports 2 access points -> 2 buttons, unique_id = account_id_<point>."""
    aioclient_mock.get(WHOAMI_URL, json=WHOAMI_OK)
    entry = await _setup(hass)

    assert _entity_id(hass, "gate")
    assert _entity_id(hass, "garage")

    await _teardown(hass, entry)


async def test_press_calls_open(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """async_press -> POST /api/ouvrir with the right point_acces."""
    aioclient_mock.get(WHOAMI_URL, json=WHOAMI_OK)
    aioclient_mock.post(OPEN_URL, json={"autorise": True})
    entry = await _setup(hass)

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: _entity_id(hass, "gate")},
        blocking=True,
    )

    post_calls = [c for c in aioclient_mock.mock_calls if c[0] == "POST"]
    assert len(post_calls) == 1
    assert str(post_calls[0][1]) == OPEN_URL
    assert post_calls[0][2] == {"point_acces": "gate"}

    await _teardown(hass, entry)


async def test_press_refusal_raises(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Backend refuses (autorise:false) -> HomeAssistantError surfaced on press."""
    aioclient_mock.get(WHOAMI_URL, json=WHOAMI_OK)
    aioclient_mock.post(OPEN_URL, json={"autorise": False})
    entry = await _setup(hass)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: _entity_id(hass, "gate")},
            blocking=True,
        )

    await _teardown(hass, entry)
