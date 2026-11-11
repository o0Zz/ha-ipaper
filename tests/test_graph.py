from datetime import datetime, timedelta, timezone

from ha_ipaper.routers.graph import graph_svg
from ha_ipaper.services.homeassistant import HomeAssistantService

from .conftest import TOKEN
from .test_pages import make_config

START = datetime(2025, 12, 31, tzinfo=timezone.utc)
END = START + timedelta(days=2)


def test_get_entity(fake_ha):
    _, url = fake_ha
    service = HomeAssistantService(url, TOKEN)

    entity = service.get_entity("living_room_temperature")

    assert entity is not None
    assert entity.state.state == "21.5"
    # Domains without any entity (light, climate, ...) must not fail the lookup
    assert service.get_entity("missing") is None


def test_get_history_keeps_numeric_values(fake_ha):
    _, url = fake_ha

    history = HomeAssistantService(url, TOKEN).get_history("living_room_temperature", START, END)

    assert [value for _, value in history] == [20.0, 21.5]
    assert all(isinstance(when, datetime) for when, _ in history)


def test_get_history_without_history(fake_ha):
    ha, url = fake_ha
    ha.history.clear()

    assert HomeAssistantService(url, TOKEN).get_history("living_room_temperature", START, END) == []


def test_get_history_unknown_entity(fake_ha):
    _, url = fake_ha
    assert HomeAssistantService(url, TOKEN).get_history("missing", START, END) == []


def test_graph_svg(fake_ha):
    _, url = fake_ha
    config = make_config(url)

    response = graph_svg("living_room_temperature", HomeAssistantService(url, TOKEN), config)

    assert response.status_code == 200
    assert response.media_type == "image/svg+xml"
    assert response.body.startswith(b"<?xml")


def test_graph_svg_unknown_sensor(fake_ha):
    _, url = fake_ha

    response = graph_svg("missing", HomeAssistantService(url, TOKEN), make_config(url))

    assert response.status_code == 404
