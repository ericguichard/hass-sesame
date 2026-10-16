"""Constants for the Sesame integration."""

from __future__ import annotations

# Integration domain. NB: the plain `sesame` domain is already taken by a core
# integration (Candy House SESAME locks), so we namespace as `sesame_gate` to
# avoid shadowing it and to stay eligible for the HACS store.
DOMAIN = "sesame_gate"

# No default URL: each deployment enters the address of its own Sesame server
# in the config flow (the integration is not tied to any deployment).

# Config entry keys.
CONF_URL = "url"
CONF_TOKEN = "token"

# Coordinator poll interval (the whoami call). whoami validates the token and
# carries the server-side availability of each access point (closed for the
# season, unreachable equipment). 1 min (0.5.0, was 5 min) so a button greys out
# and comes back promptly when the equipment drops or returns; the call is tiny.
DEFAULT_SCAN_INTERVAL = 60

# No access-point labels are hard-coded: the access points and their names come
# from the server (whoami -> points_acces); each button is labelled from the
# point id (see button.py). The integration therefore works with any access.
