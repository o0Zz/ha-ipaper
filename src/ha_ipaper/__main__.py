#!/usr/bin/env python3
"""HA-IPaper: Home Assistant Interactive ePaper Dashboard."""

import argparse
import logging
import logging.config
import os
import sys
from pathlib import Path

import uvicorn
from dynaconf import Dynaconf, Validator
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from .core.config import PagesConfig
from .core.dependencies import get_pages_config
from .routers import pages, svg

_LOGGER = logging.getLogger(__name__)

# Required configuration validators
CONFIG_VALIDATORS = [
    Validator("general.homeassistant_url", must_exist=True),
    Validator("general.homeassistant_token", must_exist=True),
    Validator("general.html_templates", must_exist=True),
    Validator("server.bind_addr", must_exist=True),
    Validator("server.bind_port", must_exist=True),
    Validator("loggercfg", must_exist=True),
    Validator("menu", must_exist=True),
]


def http_to_websocket_url(url: str) -> str:
    """Convert HTTP URL to WebSocket URL for Home Assistant API."""
    ws_url = url.replace("http://", "ws://").replace("https://", "wss://")
    return f"{ws_url}/api/websocket"


def create_templates(html_folders: list[str]) -> Jinja2Templates:
    """Create Jinja2Templates with multiple folders (first = highest priority)."""
    if len(html_folders) > 1:
        loader = ChoiceLoader([FileSystemLoader(folder) for folder in html_folders])
        templates = Jinja2Templates(directory=html_folders[-1])
        templates.env.loader = loader
    else:
        templates = Jinja2Templates(directory=html_folders[0])

    return templates


def create_app(
    html_folders: list[str],
    ha_url: str,
    ha_token: str,
    menu: dict,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="HA-IPaper",
        description="Home Assistant Interactive ePaper Dashboard",
    )

    # Convert to WebSocket URL if needed
    if ha_url.startswith(("http://", "https://")):
        ha_url = http_to_websocket_url(ha_url)

    # Configure pages
    config = PagesConfig(
        html_folders=html_folders,
        homeassistant_url=ha_url,
        homeassistant_token=ha_token,
        menu=menu,
        templates=create_templates(html_folders),
    )
    app.dependency_overrides[get_pages_config] = lambda: config

    # Include routers (SVG first to match .svg before generic path)
    app.include_router(svg.router)
    app.include_router(pages.router)

    return app


def load_config(config_path: str) -> Dynaconf:
    """Load and validate configuration from YAML file."""
    if not Path(config_path).is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = Dynaconf(
        settings_files=[config_path],
        envvar_prefix="HA_IPAPER",
        load_dotenv=True,
        validators=CONFIG_VALIDATORS,
    )
    config.validators.validate()
    return config


def resolve_path(base_path: Path, path: str) -> str:
    """Resolve a path relative to the config file, making it absolute."""
    if Path(path).is_absolute():
        return path
    return str(base_path / path)


def main() -> None:
    """Application entry point."""
    parser = argparse.ArgumentParser(
        prog="HA-IPaper",
        description="Home Assistant Interactive ePaper Dashboard",
    )
    parser.add_argument(
        "-config", type=str, required=True, help="Configuration file (YAML)"
    )
    args = parser.parse_args()

    # Load configuration
    _LOGGER.info(f"Loading configuration from {args.config}")
    try:
        config = load_config(args.config)
    except Exception:
        _LOGGER.exception(f"Failed to load configuration: {args.config}")
        sys.exit(1)

    # Setup logging
    logging.config.dictConfig(config.loggercfg.to_dict())

    # Build list of HTML template folders (first = highest priority)
    html_folders = [
        os.path.abspath(resolve_path(Path(args.config).parent, folder))
        for folder in config.general.html_templates
        if Path(resolve_path(Path(args.config).parent, folder)).is_dir()
    ]
    html_folders.append(
        os.path.abspath(resolve_path(Path(__file__).parent, "html-template"))
    )

    _LOGGER.info(f"Using HTML template folders: {html_folders}")
    _LOGGER.info(f"Using Home Assistant URL: {config.general.homeassistant_url}")

    # Create FastAPI app
    app = create_app(
        html_folders=html_folders,
        ha_url=config.general.homeassistant_url,
        ha_token=config.general.homeassistant_token,
        menu=config.menu,
    )

    # Run server
    _LOGGER.info(
        f"Starting server on {config.server.bind_addr}:{config.server.bind_port}"
    )
    uvicorn.run(
        app,
        host=config.server.bind_addr,
        port=config.server.bind_port,
        log_config=None,  # Use our logging configuration instead of uvicorn's default
    )


if __name__ == "__main__":
    main()
