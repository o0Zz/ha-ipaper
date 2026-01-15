from ha_ipaper.core.config import PagesConfig
from ha_ipaper.services.homeassistant import HomeAssistantService
from fastapi import Depends


def get_pages_config() -> PagesConfig:
    raise RuntimeError("Dependency not overridden")


def get_homeassistant(
    config: PagesConfig = Depends(get_pages_config),
) -> HomeAssistantService:
    return HomeAssistantService(
        config.homeassistant_url,
        config.homeassistant_token,
    )
