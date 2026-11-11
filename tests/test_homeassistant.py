import asyncio
import json

import pytest
from homeassistant_api.errors import UnauthorizedError

from ha_ipaper.services.homeassistant import (
    HomeAssistantConnectionError,
    HomeAssistantService,
)

from .conftest import TOKEN, make_state


@pytest.mark.parametrize(
    ("url", "ws_url", "http_url"),
    [
        ("http://supervisor/core", "ws://supervisor/core/websocket", "http://supervisor/core/api"),
        ("http://supervisor/core/", "ws://supervisor/core/websocket", "http://supervisor/core/api"),
        ("http://192.168.1.10:8123", "ws://192.168.1.10:8123/api/websocket", "http://192.168.1.10:8123/api"),
        ("https://ha.example.com/", "wss://ha.example.com/api/websocket", "https://ha.example.com/api"),
    ],
)
def test_urls(url, ws_url, http_url):
    service = HomeAssistantService(url, TOKEN)
    assert service._ws_url == ws_url
    assert service._http_url == http_url


def test_get_data(fake_ha):
    ha, url = fake_ha
    entities = HomeAssistantService(url, TOKEN).get_data()

    sensor = entities["sensor"].entities["living_room_temperature"]
    assert sensor.state.state == "21.5"
    assert "coffee_machine" in entities["switch"].entities
    assert entities["weather_forecast"] == ha.forecast


def _add_big_states(ha, count: int = 6000) -> int:
    """Add sensors until the get_states reply is bigger than the websockets default limit (1 MiB)."""
    ha.states += [
        make_state(f"sensor.big_{i}", str(i), friendly_name=f"Sensor {i}", padding="x" * 400)
        for i in range(count)
    ]
    size = len(json.dumps(ha.states))
    assert size > 1024 * 1024
    return size


def test_get_data_many_entities(fake_ha):
    """Issue #4: get_states reply bigger than 1 MiB."""
    ha, url = fake_ha
    _add_big_states(ha)

    entities = HomeAssistantService(url, TOKEN).get_data()

    assert len(entities["sensor"].entities) == 6001


def test_supervisor_502_gives_clear_error(fake_ha):
    """Issue #3: the Supervisor answers 502 when it cannot reach Home Assistant Core."""
    ha, url = fake_ha
    ha.reject_status = 502
    service = HomeAssistantService("http://supervisor/core", TOKEN)
    service._ws_url = f"{url.replace('http', 'ws')}/core/websocket"

    with pytest.raises(HomeAssistantConnectionError, match="Supervisor cannot reach Home Assistant Core") as exc:
        service.get_data()
    assert "homeassistant_url and homeassistant_token" in str(exc.value)


@pytest.mark.parametrize("status", [403, 502])
def test_direct_connection_rejected_gives_clear_error(fake_ha, status):
    ha, url = fake_ha
    ha.reject_status = status

    with pytest.raises(HomeAssistantConnectionError, match=f"HTTP {status}") as exc:
        HomeAssistantService(url, TOKEN).get_data()
    assert "Supervisor" not in str(exc.value)


def test_wrong_token(fake_ha):
    _, url = fake_ha
    with pytest.raises(UnauthorizedError):
        HomeAssistantService(url, "wrong-token").get_data()


def test_call_service(fake_ha):
    ha, url = fake_ha

    asyncio.run(
        HomeAssistantService(url, TOKEN).call_service(
            "switch.turn_on", {"entity_id": "switch.coffee_machine"}
        )
    )

    [call] = ha.service_calls
    assert call["domain"] == "switch"
    assert call["service"] == "turn_on"
    assert call["service_data"] == {"entity_id": "switch.coffee_machine"}
