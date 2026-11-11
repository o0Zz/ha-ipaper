import os
from pathlib import Path

import pytest

from ha_ipaper.__main__ import load_config

DEFAULT_CONFIG = str(Path(__file__).parent.parent / "config.yaml")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Run from an empty folder (load_config reads .env) without HA_IPAPER_* variables."""
    monkeypatch.chdir(tmp_path)
    for name in list(os.environ):
        if name.startswith("HA_IPAPER_"):
            monkeypatch.delenv(name)


def test_default_config_is_valid():
    config = load_config(DEFAULT_CONFIG)

    assert config.server.bind_port == 8081
    assert config.menu[0].name == "Home"


def test_environment_overrides_file(monkeypatch):
    """The Docker image and the add-on set the Home Assistant URL and token this way."""
    monkeypatch.setenv("HA_IPAPER_GENERAL__homeassistant_url", "http://supervisor/core")
    monkeypatch.setenv("HA_IPAPER_GENERAL__homeassistant_token", "env-token")

    config = load_config(DEFAULT_CONFIG)

    assert config.general.homeassistant_url == "http://supervisor/core"
    assert config.general.homeassistant_token == "env-token"


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "missing.yaml"))
