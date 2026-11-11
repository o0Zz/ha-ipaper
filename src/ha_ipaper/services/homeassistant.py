import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

import websockets.sync.client
from homeassistant_api import Client, Entity, WebsocketClient
from websockets.exceptions import InvalidStatus

_LOGGER = logging.getLogger(__name__)

SUPERVISOR_URL = "http://supervisor/core"

# The get_states reply holds every entity and exceeds the websockets default limit (1 MiB)
# on large installations. Same limit as the Supervisor uses for messages from Core.
MAX_MESSAGE_SIZE = 64 * 1024 * 1024


class HomeAssistantConnectionError(Exception):
    """Home Assistant refused the connection; the message tells the user what to check."""


class _WebsocketClient(WebsocketClient):
    """WebsocketClient that accepts messages up to MAX_MESSAGE_SIZE.

    homeassistant_api opens the connection with the websockets default size limit
    and has no option to change it, so __enter__ is redone with max_size set.
    """

    def __enter__(self):
        self._conn = websockets.sync.client.connect(self.api_url, max_size=MAX_MESSAGE_SIZE)
        self._conn.__enter__()
        okay = self.authentication_phase()
        _LOGGER.debug("Authenticated with Home Assistant (%s)", okay.ha_version)
        self.supported_features_phase()
        return self


class HomeAssistantService:
    def __init__(self, url: str, token: str):
        url = url.rstrip("/")
        self._is_supervisor = url == SUPERVISOR_URL
        # The Supervisor proxy (add-on mode) serves the websocket at /core/websocket, not /core/api/websocket
        ws_path = "/websocket" if self._is_supervisor else "/api/websocket"
        self._ws_url = f"{url.replace('http://', 'ws://').replace('https://', 'wss://')}{ws_path}"
        self._http_url = f"{url}/api"
        self._token = token

    @contextmanager
    def _websocket(self) -> Iterator[WebsocketClient]:
        try:
            with _WebsocketClient(self._ws_url, self._token) as client:
                yield client
        except InvalidStatus as exc:
            status = exc.response.status_code
            if self._is_supervisor and status == 502:
                message = (
                    "The Home Assistant Supervisor cannot reach Home Assistant Core (HTTP 502). "
                    "Check that Home Assistant Core is started and running. "
                    "To bypass the Supervisor, set homeassistant_url and homeassistant_token "
                    "in the add-on configuration."
                )
            else:
                message = (
                    f"Home Assistant rejected the WebSocket connection to {self._ws_url} "
                    f"(HTTP {status}). Check homeassistant_url and homeassistant_token."
                )
            raise HomeAssistantConnectionError(message) from exc

    def get_data(self) -> dict:
        _LOGGER.debug("Fetching Home Assistant entities")
        with self._websocket() as client:
            entities = client.get_entities()
            entities["weather_forecast"] = client.trigger_service_with_response(
                "weather",
                "get_forecasts",
                entity_id="weather.home",
                type="daily",
            )["weather.home"]["forecast"]
            _LOGGER.debug("Fetched %d entities from Home Assistant", len(entities))
            return entities

    async def call_service(self, service: str, data: dict) -> None:
        domain, function = service.split(".")
        _LOGGER.debug("Calling Home Assistant service %s with data %s", service, data)
        with self._websocket() as client:
            with client.listen_events("state_changed") as events:
                client.trigger_service(domain, function, **data)
                next(events, None)

        _LOGGER.debug("Service %s called successfully", service)

    def get_entity(self, entity_id: str) -> Entity | None:
        with Client(self._http_url, self._token) as client:
            entities = client.get_entities()
            for entity_type in (
                "sensor",
                "binary_sensor",
                "switch",
                "light",
                "climate",
            ):
                for entity_key, entity in entities[entity_type].entities.items():
                    if entity_key == entity_id:
                        return entity

        _LOGGER.debug(f"Entity {entity_id} not found")
        return None

    def get_history(
        self, entity_id: str, start_time: datetime, end_time: datetime
    ) -> list[dict]:
        _LOGGER.debug(
            f"Fetching history for entity {entity_id} from {start_time} to {end_time}"
        )

        entity = self.get_entity(entity_id=entity_id)
        history = entity.get_history(start_time, end_time)
        _LOGGER.debug(
            f"Fetched {len(history.states)} history entries for entity {entity_id}"
        )

        values = []
        for state in history.states:
            try:
                values.append((state.last_changed, float(state.state)))
            except (ValueError, TypeError):
                pass  # Ignore non-numeric

        return values
