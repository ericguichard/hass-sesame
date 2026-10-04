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

# Coordinator poll interval (the whoami call). We do NOT track real-time state:
# whoami validates the token and marks availability, it does not follow the
# state of an access point (which the backend does not expose). 5 min is plenty.
DEFAULT_SCAN_INTERVAL = 300

# No access-point labels are hard-coded: the access points and their names come
# from the server (whoami -> points_acces); each button is labelled from the
# point id (see button.py). The integration therefore works with any access.
