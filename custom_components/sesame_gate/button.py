"""Button entities: one momentary open per access point.

``button`` and NOT ``cover``/``lock`` - the backend reports no access state; a
cover/lock would show an invented state. The button is the honest object:
"press = open", momentary.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SesameConfigEntry
from .api import SesameAuthError, SesameConnectionError
from .const import DOMAIN
from .coordinator import SesameCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SesameConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one button per access point reported by whoami."""
    coordinator = entry.runtime_data
    async_add_entities(
        SesameOpenButton(coordinator, point)
        for point in coordinator.data.points_acces
    )


class SesameOpenButton(CoordinatorEntity[SesameCoordinator], ButtonEntity):
    """An "open" button for an access point declared by the server."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:gate"

    def __init__(self, coordinator: SesameCoordinator, point: str) -> None:
        super().__init__(coordinator)
        self._point = point
        account_id = coordinator.data.account_id
        self._attr_unique_id = f"{account_id}_{point.lower()}"
        # Label derived from the point id (no hard-coded name): "main_gate" ->
        # "Main Gate". has_entity_name=True -> "Sesame - <account> <access>".
        self._attr_name = point.replace("_", " ").title()
        # Device keyed on account_id (stable across token rotation, like the
        # unique_id).
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_id)},
            name=f"Sesame - {coordinator.data.account_name}",
            manufacturer="Sesame",
        )

    async def async_press(self) -> None:
        """Request the open; surface a real failure to the user."""
        try:
            allowed = await self.coordinator.api.open_access(self._point)
        except SesameAuthError as err:
            raise HomeAssistantError(
                "Sesame token revoked - reconfigure the integration"
            ) from err
        except SesameConnectionError as err:
            raise HomeAssistantError(f"Sesame unreachable: {err}") from err
        if not allowed:
            raise HomeAssistantError("Sesame refused the open")
