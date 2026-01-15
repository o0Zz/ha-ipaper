from dataclasses import dataclass

from fastapi.templating import Jinja2Templates


@dataclass(frozen=True)
class PagesConfig:
    html_folder: str
    homeassistant_url: str
    homeassistant_token: str
    menu: dict
    templates: Jinja2Templates
