from dataclasses import dataclass

from fastapi.templating import Jinja2Templates


@dataclass(frozen=True)
class PagesConfig:
    html_folders: list[str]
    homeassistant_url: str
    homeassistant_token: str
    menu: dict
    timezone: str | None
    templates: Jinja2Templates
    graph_days: int | None = None
