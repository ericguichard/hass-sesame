"""Pytest fixtures for the custom component."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/sesame_gate in all test sessions.

    Without this, HA refuses to set up a custom integration in tests.
    """
    yield


@pytest.fixture(autouse=True)
def _no_pycares_thread():
    """Prevent the c-ares (pycares) watchdog thread from starting.

    aiohttp (via aiodns) creates a ``pycares.Channel`` when HA's session
    connector is built, which starts a daemon thread ``_run_safe_shutdown_loop``.
    All HTTP is mocked here (aioclient_mock), so NO real DNS resolution is
    needed; that thread, whose survival depends on GC, makes HA's strict
    lingering-thread check fail non-deterministically. We neutralise the Channel:
    no thread, no flakiness.
    """
    with patch("pycares.Channel"):
        yield
