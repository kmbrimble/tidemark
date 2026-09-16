"""Shared fixtures for Tidemark tests."""

import json
from pathlib import Path

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make custom_components/ importable for every test."""
    yield


@pytest.fixture
def snapshot() -> dict:
    """A real snapshot captured from the live collector, with series trimmed."""
    path = Path(__file__).parent / "fixtures_snapshot.json"
    return json.loads(path.read_text())
