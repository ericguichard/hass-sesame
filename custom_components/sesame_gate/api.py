"""Minimal HTTP client for the Sesame API (an access-control backend).

Only two calls:

- ``GET  /api/integration/whoami`` - read-only, validates the token WITHOUT
  actuating anything, returns the account identity + the list of access points.
- ``POST /api/ouvrir``            - momentary open, returns ``{autorise}``.

Seasonal closure (backend contract since 2026-10): ``whoami`` may list access
points that are deliberately out of service for the season under
``points_hors_saison``; opening one returns HTTP 503 ``{erreur: "hors_saison"}``
straight away. The integration shows such a button as unavailable instead of
letting a press fail.

Unreachable access points (backend contract since 2026-10, 0.5.0): ``whoami`` may
also list under ``points_injoignables`` the points whose on-site equipment has
stopped answering the server's health probe. Same treatment: the button is
shown unavailable until the server reports the point reachable again.

Access points are NOT hard-coded: the server declares them through ``whoami``
(`points_acces`), so the integration adapts to any access (gate, door, barrier,
etc.) the backend exposes.

Both authenticate with ``Authorization: Bearer <token>``. A 401 on either means
"token revoked/expired/invalid" -> we raise ``SesameAuthError`` so HA triggers
re-authentication.

Note: the route names and JSON keys (`/api/ouvrir`, `point_acces`, `autorise`,
`coloti_id`, `coloti`) are the backend's HTTP contract and are used verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import aiohttp


class SesameAuthError(Exception):
    """Token missing/invalid/revoked/expired (HTTP 401) -> HA re-auth."""


class SesameConnectionError(Exception):
    """Backend unreachable or unexpected response."""


class SesameOutOfSeasonError(Exception):
    """The access point is closed for the season (HTTP 503 ``hors_saison``).

    Nothing is broken: the backend refuses on purpose. Kept distinct from
    ``SesameConnectionError`` so the message does not suggest a fault.
    """


@dataclass(slots=True)
class SesameData:
    """Normalised whoami response, consumed by the coordinator."""

    # STABLE account identity (from the backend). Identity key of the
    # integration: unique_id + device. NEVER the token (which rotates).
    account_id: str
    # Display name for the device label.
    account_name: str
    # Exposable access points (one button per entry), as declared by the server
    # - no name is hard-coded in the integration.
    points_acces: list[str]
    # Access points closed for the season (server-declared, may be empty): the
    # matching buttons are shown unavailable. Defaults to [] for older backends.
    points_hors_saison: list[str] = field(default_factory=list)
    # Access points whose on-site equipment is currently unreachable
    # (server-side health probe): shown unavailable too. [] for older backends.
    points_injoignables: list[str] = field(default_factory=list)


class SesameApiClient:
    """Small aiohttp client reusing HA's shared session."""

    def __init__(
        self, session: aiohttp.ClientSession, base_url: str, token: str
    ) -> None:
        self._session = session
        self._base = base_url.rstrip("/")
        self._token = token

    def set_token(self, token: str) -> None:
        """Update the token (after a re-authentication)."""
        self._token = token

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def whoami(self) -> SesameData:
        """Validate the token and return the identity + access points."""
        try:
            async with self._session.get(
                f"{self._base}/api/integration/whoami", headers=self._headers
            ) as resp:
                if resp.status == 401:
                    raise SesameAuthError
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise SesameConnectionError(str(err)) from err

        # The backend exposes the identity under the keys `coloti_id` / `coloti`
        # (HTTP contract); we map them to neutral fields inside the integration.
        ident = data.get("coloti") or {}
        name = f"{ident.get('prenom', '')} {ident.get('nom', '')}".strip()
        return SesameData(
            account_id=data["coloti_id"],
            account_name=name or "Sesame",
            points_acces=list(data.get("points_acces") or []),
            points_hors_saison=list(data.get("points_hors_saison") or []),
            points_injoignables=list(data.get("points_injoignables") or []),
        )

    async def open_access(self, access_point: str) -> bool:
        """Request an open. Returns ``autorise`` (True = open allowed)."""
        try:
            async with self._session.post(
                f"{self._base}/api/ouvrir",
                headers=self._headers,
                json={"point_acces": access_point},
            ) as resp:
                if resp.status == 401:
                    raise SesameAuthError
                if resp.status == 503:
                    # Seasonal closure is a deliberate refusal, not an outage:
                    # read the body before raise_for_status() turns it generic.
                    body = await resp.json(content_type=None)
                    if isinstance(body, dict) and body.get("erreur") == "hors_saison":
                        raise SesameOutOfSeasonError(access_point)
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise SesameConnectionError(str(err)) from err
        except ValueError as err:  # 503 with a non-JSON body
            raise SesameConnectionError(str(err)) from err

        return bool(data.get("autorise"))
