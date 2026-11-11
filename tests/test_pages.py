import asyncio
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from ha_ipaper import __main__ as main_module
from ha_ipaper.__main__ import create_templates
from ha_ipaper.core.config import PagesConfig
from ha_ipaper.routers.pages import serve_html, serve_html_post
from ha_ipaper.services.homeassistant import HomeAssistantService

from .conftest import TOKEN

TEMPLATES = str(Path(main_module.__file__).parent / "html-template")
MENU = [
    {"name": "Home", "icon": "", "components": ["components/forecast.html", "components/sensors.html"]},
    {"name": "Switches", "icon": "", "components": ["components/switches.html"]},
]


def make_config(url: str) -> PagesConfig:
    return PagesConfig(
        html_folders=[TEMPLATES],
        homeassistant_url=url,
        homeassistant_token=TOKEN,
        menu=MENU,
        timezone="Europe/Paris",
        templates=create_templates([TEMPLATES]),
        graph_days=7,
    )


def make_request(path: str, method: str = "GET", query: str = "", form: dict | None = None) -> Request:
    body = urlencode(form or {}).encode()

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    headers = [(b"content-type", b"application/x-www-form-urlencoded")] if form else []
    scope = {"type": "http", "method": method, "path": path, "query_string": query.encode(), "headers": headers}
    return Request(scope, receive)


def render(url: str, filename: str = "index", page: str | None = None, ha=None) -> str:
    config = make_config(url)
    ha = ha or HomeAssistantService(url, TOKEN)
    response = asyncio.run(serve_html(make_request(f"/{filename}.html"), filename, page, config, ha))
    assert response.status_code == 200
    return response.body.decode()


def test_index_renders_entities(fake_ha):
    _, url = fake_ha
    body = render(url)

    assert "Living room" in body
    assert "21.5" in body
    assert "Stack trace" not in body


def test_page_parameter_selects_menu_entry(fake_ha):
    _, url = fake_ha
    body = render(url, page="Switches")

    assert "Coffee machine" in body
    assert "Living room" not in body


@pytest.mark.parametrize("filename", ["missing", "../../../pyproject"])
def test_unknown_or_outside_page_is_404(fake_ha, filename):
    _, url = fake_ha
    with pytest.raises(HTTPException) as exc:
        render(url, filename=filename)
    assert exc.value.status_code == 404


def test_connection_error_page_has_no_stack_trace(fake_ha):
    """Issue #3: show what to check instead of a traceback."""
    ha, url = fake_ha
    ha.reject_status = 502

    body = render(url)

    assert "Cannot connect to Home Assistant" in body
    assert "HTTP 502" in body
    assert "Stack trace" not in body


def test_unexpected_error_page_has_stack_trace(fake_ha):
    _, url = fake_ha

    class BrokenService:
        def get_data(self):
            raise RuntimeError("boom")

    body = render(url, ha=BrokenService())

    assert "Error while rendering index.html" in body
    assert "boom" in body
    assert "Stack trace" in body


def test_post_calls_service_then_renders(fake_ha):
    ha, url = fake_ha
    form = {"service": "switch.turn_on", "entity_id": "switch.coffee_machine"}
    request = make_request("/index.html", method="POST", query="page=Switches", form=form)

    response = asyncio.run(
        serve_html_post(
            request, "index", "switch.turn_on", "Switches", make_config(url), HomeAssistantService(url, TOKEN)
        )
    )

    # The page render also calls weather.get_forecasts
    [call] = [call for call in ha.service_calls if call["domain"] == "switch"]
    assert call["service"] == "turn_on"
    assert call["service_data"] == {"entity_id": "switch.coffee_machine"}
    assert "Coffee machine" in response.body.decode()
