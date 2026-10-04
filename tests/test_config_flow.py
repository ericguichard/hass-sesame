"""Config flow: user (success / invalid_auth / cannot_connect / duplicate) + reauth."""

import aiohttp
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.sesame_gate.const import CONF_TOKEN, CONF_URL, DOMAIN

from .const import (
    ACCOUNT_ID,
    ENTRY_DATA,
    NEW_TOKEN,
    TOKEN,
    WHOAMI_OK,
    WHOAMI_OTHER,
    WHOAMI_URL,
)


async def test_user_flow_success(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """whoami 200 -> entry created, title = account name, unique_id = account_id."""
    aioclient_mock.get(WHOAMI_URL, json=WHOAMI_OK)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: ENTRY_DATA[CONF_URL], CONF_TOKEN: TOKEN}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Alice B."
    assert result["data"] == {CONF_URL: ENTRY_DATA[CONF_URL], CONF_TOKEN: TOKEN}
    assert result["result"].unique_id == ACCOUNT_ID


async def test_user_flow_invalid_auth(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """whoami 401 -> invalid_auth error, form shown again."""
    aioclient_mock.get(WHOAMI_URL, status=401)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: ENTRY_DATA[CONF_URL], CONF_TOKEN: "ses_bad"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Network error -> cannot_connect."""
    aioclient_mock.get(WHOAMI_URL, exc=aiohttp.ClientError)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: ENTRY_DATA[CONF_URL], CONF_TOKEN: TOKEN}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_duplicate(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Same account (account_id) already configured -> abort already_configured."""
    MockConfigEntry(domain=DOMAIN, unique_id=ACCOUNT_ID, data=ENTRY_DATA).add_to_hass(
        hass
    )
    aioclient_mock.get(WHOAMI_URL, json=WHOAMI_OK)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: ENTRY_DATA[CONF_URL], CONF_TOKEN: TOKEN}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_success(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reauth: new token for the SAME account -> entry updated, abort."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=ACCOUNT_ID, data=ENTRY_DATA)
    entry.add_to_hass(hass)
    aioclient_mock.get(WHOAMI_URL, json=WHOAMI_OK)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TOKEN: NEW_TOKEN}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_TOKEN] == NEW_TOKEN

    # A successful reauth SCHEDULES an entry reload (async_update_reload_and_abort).
    # Let it run (first block) - the entry becomes LOADED with a coordinator -
    # then unload to cancel its timer (otherwise the harness fails at teardown
    # on a "lingering timer").
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_reauth_wrong_account(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Reauth with a DIFFERENT account's token -> abort wrong_account, unchanged."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=ACCOUNT_ID, data=ENTRY_DATA)
    entry.add_to_hass(hass)
    aioclient_mock.get(WHOAMI_URL, json=WHOAMI_OTHER)

    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TOKEN: NEW_TOKEN}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_account"
    assert entry.data[CONF_TOKEN] == TOKEN  # original token preserved
