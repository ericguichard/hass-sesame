"""Shared test constants & data fixtures."""

# Arbitrary test URL (the integration has no default URL; each deployment
# enters its own).
BASE_URL = "https://gate.example.test"

# Actual URLs called by the client (see api.py).
WHOAMI_URL = f"{BASE_URL}/api/integration/whoami"
OPEN_URL = f"{BASE_URL}/api/ouvrir"

# Stable account identity (from the backend).
ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"
OTHER_ACCOUNT_ID = "22222222-2222-2222-2222-222222222222"

# Nominal whoami response. The `coloti_id`/`coloti` keys are the backend's HTTP
# contract; `points_acces` is intentionally generic to prove the integration
# hard-codes no access-point name.
WHOAMI_OK = {
    "coloti_id": ACCOUNT_ID,
    "coloti": {"prenom": "Alice", "nom": "B."},
    "points_acces": ["gate", "garage"],
}

# whoami with one access point closed for the season (backend `points_hors_saison`).
WHOAMI_SEASONAL = {**WHOAMI_OK, "points_hors_saison": ["garage"]}

# whoami for a DIFFERENT account (for the reauth consistency check).
WHOAMI_OTHER = {
    "coloti_id": OTHER_ACCOUNT_ID,
    "coloti": {"prenom": "Dave", "nom": "H."},
    "points_acces": ["gate", "garage"],
}

TOKEN = "ses_test_token_valid"
NEW_TOKEN = "ses_test_token_rotated"

ENTRY_DATA = {"url": BASE_URL, "token": TOKEN}
