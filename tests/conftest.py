"""Test fixtures: a fake Home Assistant (WebSocket and REST API) running in a background thread."""

import json
import threading
from collections.abc import Iterator
from urllib.parse import parse_qs, urlsplit

import pytest
from websockets.datastructures import Headers
from websockets.http11 import Request, Response
from websockets.sync.server import ServerConnection, serve

TOKEN = "test-token"
TIMESTAMP = "2026-01-01T00:00:00+00:00"
CONTEXT = {"id": "01JTEST", "parent_id": None, "user_id": None}


def make_state(entity_id: str, state: str, *, when: str = TIMESTAMP, **attributes) -> dict:
    """Return an entity state as Home Assistant sends it in a get_states reply."""
    return {
        "entity_id": entity_id,
        "state": state,
        "attributes": attributes,
        "last_changed": when,
        "last_updated": when,
        "last_reported": when,
        "context": CONTEXT,
    }


class FakeHomeAssistant:
    """Minimal Home Assistant API.

    WebSocket: auth, get_states, call_service, events.
    REST: GET /api/, /api/states, /api/history/period/<start>.
    """

    def __init__(self) -> None:
        self.states: list[dict] = [
            make_state(
                "sensor.living_room_temperature",
                "21.5",
                device_class="temperature",
                unit_of_measurement="°C",
                friendly_name="Living room",
            ),
            make_state("switch.coffee_machine", "off", friendly_name="Coffee machine"),
            make_state("weather.home", "sunny", friendly_name="Home"),
        ]
        self.forecast: list[dict] = [
            {"datetime": f"2026-01-0{day}T12:00:00+00:00", "condition": "sunny", "temperature": 20 + day}
            for day in range(1, 6)
        ]
        # REST history, by entity_id
        self.history: dict[str, list[dict]] = {
            "sensor.living_room_temperature": [
                make_state("sensor.living_room_temperature", "20.0", when="2026-01-01T00:00:00+00:00"),
                make_state("sensor.living_room_temperature", "unavailable", when="2026-01-01T01:00:00+00:00"),
                make_state("sensor.living_room_temperature", "21.5", when="2026-01-01T02:00:00+00:00"),
            ]
        }
        # HTTP status to answer every request with (WebSocket handshake and REST)
        self.reject_status: int | None = None
        # Every call_service message received
        self.service_calls: list[dict] = []

    def process_request(self, connection: ServerConnection, request: Request) -> Response | None:
        if self.reject_status is not None:
            return connection.respond(self.reject_status, "Rejected by test\n")
        if request.headers.get("Upgrade") is None:
            return self.rest(request)
        return None  # WebSocket handshake

    def rest(self, request: Request) -> Response:
        url = urlsplit(request.path)
        if url.path == "/api/":
            data = {"message": "API running."}
        elif url.path == "/api/states":
            data = self.states
        elif url.path.startswith("/api/history/period/"):
            entity_ids = parse_qs(url.query)["filter_entity_id"][0].split(",")
            data = [self.history[entity_id] for entity_id in entity_ids if entity_id in self.history]
        else:
            return Response(404, "Not Found", Headers([("Content-Length", "0"), ("Connection", "close")]), b"")
        body = json.dumps(data).encode()
        headers = Headers([
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
            ("Connection", "close"),
        ])
        return Response(200, "OK", headers, body)

    def handler(self, ws: ServerConnection) -> None:
        ws.send(json.dumps({"type": "auth_required", "ha_version": "2026.11.0"}))
        auth = json.loads(ws.recv())
        if auth.get("access_token") != TOKEN:
            ws.send(json.dumps({"type": "auth_invalid", "message": "Invalid access token"}))
            return
        ws.send(json.dumps({"type": "auth_ok", "ha_version": "2026.11.0"}))

        subscriptions: list[int] = []
        for raw in ws:
            msg = json.loads(raw)
            result = None
            if msg["type"] == "get_states":
                result = self.states
            elif msg["type"] == "subscribe_events":
                subscriptions.append(msg["id"])
            elif msg["type"] == "call_service":
                self.service_calls.append(msg)
                result = {"context": CONTEXT}
                if msg.get("return_response"):
                    entity_id = msg["service_data"]["entity_id"]
                    result["response"] = {entity_id: {"forecast": self.forecast}}
            ws.send(json.dumps({"id": msg["id"], "type": "result", "success": True, "result": result}))

            if msg["type"] == "call_service":
                for subscription in subscriptions:
                    ws.send(json.dumps({
                        "id": subscription,
                        "type": "event",
                        "event": {
                            "event_type": "state_changed",
                            "data": {"entity_id": msg["service_data"].get("entity_id")},
                            "origin": "LOCAL",
                            "time_fired": TIMESTAMP,
                            "context": CONTEXT,
                        },
                    }))


@pytest.fixture
def fake_ha() -> Iterator[tuple[FakeHomeAssistant, str]]:
    """Start a fake Home Assistant and return it with its base URL (http://127.0.0.1:<port>)."""
    ha = FakeHomeAssistant()
    # No size limit on the server side: the tests check the client limit
    server = serve(ha.handler, "127.0.0.1", 0, process_request=ha.process_request, max_size=None)

    def serve_forever() -> None:
        try:
            server.serve_forever()
        except OSError:
            pass  # Windows: select() on the socket closed by shutdown()

    thread = threading.Thread(target=serve_forever, daemon=True)
    thread.start()
    try:
        yield ha, f"http://127.0.0.1:{server.socket.getsockname()[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
