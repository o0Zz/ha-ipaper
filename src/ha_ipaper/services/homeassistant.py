from homeassistant_api import WebsocketClient


class HomeAssistantService:
    def __init__(self, url: str, token: str):
        self._url = url
        self._token = token

    def get_data(self) -> dict:
        with WebsocketClient(self._url, self._token) as client:
            entities = client.get_entities()
            entities["weather_forecast"] = client.trigger_service_with_response(
                "weather",
                "get_forecasts",
                entity_id="weather.home",
                type="daily",
            )["weather.home"]["forecast"]
            return entities

    async def call_service(self, service: str, data: dict) -> None:
        domain, function = service.split(".")
        with WebsocketClient(self._url, self._token) as client:
            with client.listen_events("state_changed") as events:
                client.trigger_service(domain, function, **data)
                next(events, None)
