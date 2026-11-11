"""Test fixtures: a fake Home Assistant WebSocket API running in a background thread."""

import json
import threading
from collections.abc import Iterator

import pytest
from websockets.sync.server import ServerConnection, serve

TOKEN = "test-token"
TIMESTAMP = "2026-01-01T00:00:00+00:00"
CONTEXT = {"id": "01JTEST", "parent_id": None, "user_id": None}


def make_state(entity_id: str, state: str, **attributes) -> dict:
    """Return an entity state as Home Assistant sends it in a get_states reply."""
    return {
        "entity_id": entity_id,
        "state": state,
        "attributes": attributes,
        "last_changed": TIMESTAMP,
        "last_updated": TIMESTAMP,
        "last_reported": TIMESTAMP,
        "context": CONTEXT,
    }


class FakeHomeAssistant:
    """Minimal Home Assistant WebSocket API: auth, get_states, call_service, events."""

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
        # HTTP status to answer the WebSocket handshake with, instead of accepting it
        self.reject_status: int | None = None
        # Every call_service message received
        self.service_calls: list[dict] = []

    def process_request(self, connection: ServerConnection, request):
        if self.reject_status is not None:
            return connection.respond(self.reject_status, "Rejected by test\n")
        return None

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
                    entity_id = msg["target"]["entity_id"]
                    result["response"] = {entity_id: {"forecast": self.forecast}}
            ws.send(json.dumps({"id": msg["id"], "type": "result", "success": True, "result": result}))

            if msg["type"] == "call_service":
                for subscription in subscriptions:
                    ws.send(json.dumps({
                        "id": subscription,
                        "type": "event",
                        "event": {
                            "event_type": "state_changed",
                            "data": {"entity_id": msg["target"]["entity_id"]} if "target" in msg else {},
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
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield ha, f"http://127.0.0.1:{server.socket.getsockname()[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
