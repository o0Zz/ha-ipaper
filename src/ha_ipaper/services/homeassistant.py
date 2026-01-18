import logging
from datetime import datetime

from homeassistant_api import Client, Entity, WebsocketClient

_LOGGER = logging.getLogger(__name__)


class HomeAssistantService:
    def __init__(self, url: str, token: str):
        self._ws_url = f"{url.replace('http://', 'ws://').replace('https://', 'wss://')}/api/websocket"
        self._http_url = f"{url}/api"
        self._token = token

    def get_data(self) -> dict:
        _LOGGER.debug("Fetching Home Assistant entities")
        with WebsocketClient(self._ws_url, self._token) as client:
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
        with WebsocketClient(self._ws_url, self._token) as client:
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
