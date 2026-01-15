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

from .core.config import PagesConfig
from .core.dependencies import get_pages_config
from .routers import pages, svg

_LOGGER = logging.getLogger(__name__)

# Required configuration validators
CONFIG_VALIDATORS = [
    Validator("general.homeassistant_url", must_exist=True),
    Validator("general.homeassistant_token", must_exist=True),
    Validator("general.html_template", must_exist=True),
    Validator("server.bind_addr", must_exist=True),
    Validator("server.bind_port", must_exist=True),
    Validator("loggercfg", must_exist=True),
    Validator("menu", must_exist=True),
]


def http_to_websocket_url(url: str) -> str:
    """Convert HTTP URL to WebSocket URL for Home Assistant API."""
    ws_url = url.replace("http://", "ws://").replace("https://", "wss://")
    return f"{ws_url}/api/websocket"


def create_app(html_folder: str, ha_url: str, ha_token: str, menu: dict) -> FastAPI:
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
        html_folder=os.path.abspath(html_folder),
        homeassistant_url=ha_url,
        homeassistant_token=ha_token,
        menu=menu,
        templates=Jinja2Templates(directory=os.path.abspath(html_folder)),
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


def resolve_html_template_path(config_path: str, html_template: str) -> str:
    """Resolve HTML template path, making it absolute if relative."""
    if Path(html_template).is_absolute():
        return html_template
    return str(Path(config_path).parent / html_template)


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

    # Resolve HTML template path
    html_template = resolve_html_template_path(
        args.config, config.general.html_template
    )

    _LOGGER.info(f"Using HTML template folder: {html_template}")
    _LOGGER.info(f"Using Home Assistant URL: {config.general.homeassistant_url}")

    # Create FastAPI app
    app = create_app(
        html_folder=html_template,
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
        log_level="info",
    )


if __name__ == "__main__":
    main()
