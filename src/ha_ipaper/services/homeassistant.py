import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from homeassistant_api import Client, Entity, WebsocketClient
from niquests.exceptions import HTTPError

_LOGGER = logging.getLogger(__name__)

SUPERVISOR_URL = "http://supervisor/core"

# Entity domains searched by get_entity (the graph page passes the entity name without its domain)
GRAPH_DOMAINS = ("sensor", "binary_sensor", "switch", "light", "climate")


class HomeAssistantConnectionError(Exception):
    """Home Assistant refused the connection; the message tells the user what to check."""


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
            with WebsocketClient(self._ws_url, self._token) as client:
                yield client
        except HTTPError as exc:
            if exc.response is None:
                raise
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

    @staticmethod
    def _find_entity(client: Client, entity_id: str) -> Entity | None:
        entities = client.get_entities()
        for domain in GRAPH_DOMAINS:
            group = entities.get(domain)
            if group is not None and entity_id in group.entities:
                return group.entities[entity_id]

        _LOGGER.debug("Entity %s not found", entity_id)
        return None

    def get_entity(self, entity_id: str) -> Entity | None:
        with Client(self._http_url, self._token) as client:
            return self._find_entity(client, entity_id)

    def get_history(
        self, entity_id: str, start_time: datetime, end_time: datetime
    ) -> list[tuple[datetime, float]]:
        _LOGGER.debug(
            "Fetching history for entity %s from %s to %s", entity_id, start_time, end_time
        )

        # The entity must be used while its client is open: Entity.get_history goes through it
        with Client(self._http_url, self._token) as client:
            entity = self._find_entity(client, entity_id)
            history = entity.get_history(start_time, end_time) if entity else None

        if history is None:
            _LOGGER.debug("No history for entity %s", entity_id)
            return []

        _LOGGER.debug(
            "Fetched %d history entries for entity %s", len(history.states), entity_id
        )
        values = []
        for state in history.states:
            try:
                values.append((state.last_changed, float(state.state)))
            except (ValueError, TypeError):
                pass  # Ignore non-numeric

        return values
