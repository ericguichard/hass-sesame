"""Sesame integration - open access points (gates, doors, barriers) from HA."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SesameApiClient
from .const import CONF_TOKEN, CONF_URL, DOMAIN
from .coordinator import SesameCoordinator

PLATFORMS: list[Platform] = [Platform.BUTTON]

type SesameConfigEntry = ConfigEntry[SesameCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SesameConfigEntry) -> bool:
    """Set up an entry: client + coordinator, then the platforms."""
    session = async_get_clientsession(hass)
    api = SesameApiClient(session, entry.data[CONF_URL], entry.data[CONF_TOKEN])
    coordinator = SesameCoordinator(hass, api)

    # First refresh: validate the token (401 -> re-auth) and discover the access
    # points before creating the entities.
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SesameConfigEntry) -> bool:
    """Unload the entry and its platforms."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
