import logging

from homeassistant_api import WebsocketClient

_LOGGER = logging.getLogger(__name__)


class HomeAssistantService:
    def __init__(self, url: str, token: str):
        self._url = url
        self._token = token

    def get_data(self) -> dict:
        _LOGGER.debug("Fetching Home Assistant entities")
        with WebsocketClient(self._url, self._token) as client:
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
        with WebsocketClient(self._url, self._token) as client:
            with client.listen_events("state_changed") as events:
                client.trigger_service(domain, function, **data)
                next(events, None)

        _LOGGER.debug("Service %s called successfully", service)
