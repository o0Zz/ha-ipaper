"""Pages router for serving HTML templates."""

import logging
import traceback
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.params import Depends
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from ha_ipaper.core.config import PagesConfig
from ha_ipaper.core.dependencies import get_homeassistant, get_pages_config
from ha_ipaper.services.homeassistant import HomeAssistantService
from ha_ipaper.utils.filesystem import resolve_safe_path

_LOGGER = logging.getLogger(__name__)
router = APIRouter(tags=["pages"])


def _localized_now(tz_name: str | None) -> datetime:
    now_utc = datetime.now(timezone.utc)
    if tz_name:
        try:
            return now_utc.astimezone(ZoneInfo(tz_name))
        except ZoneInfoNotFoundError:
            _LOGGER.warning("Timezone '%s' not found, using local time", tz_name)

    return now_utc.astimezone()


@router.get("/", response_class=RedirectResponse)
async def serve_index():
    return RedirectResponse(url="/index.html")


@router.get("/{filename:path}.html", response_class=HTMLResponse)
async def serve_html(
    request: Request,
    filename: str,
    page: str | None = Query(default=None),
    config: PagesConfig = Depends(get_pages_config),
    ha: HomeAssistantService = Depends(get_homeassistant),
):
    try:
        resolve_safe_path(config.html_folders, filename, ".html")
        return config.templates.TemplateResponse(
            f"{filename}.html",
            {
                "request": request,
                "title": "Home Assistant Interactive ePaper Dashboard",
                "menu": config.menu,
                "entities": ha.get_data(),
                "date": _localized_now(config.timezone).strftime("%a %d %b %H:%M"),
                "page": page,
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        _LOGGER.exception("Error while rendering %s.html", filename)
        return config.templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": f"Error while rendering {filename}.html",
                "parameters": dict(request.query_params),
                "error_message": str(exc),
                "stacktrace": traceback.format_exc(),
            },
            status_code=200,
        )


@router.post("/{filename:path}.html", response_class=HTMLResponse)
async def serve_html_post(
    request: Request,
    filename: str,
    service: str | None = Form(default=None),
    page: str | None = Query(default=None),
    config: PagesConfig = Depends(get_pages_config),
    ha: HomeAssistantService = Depends(get_homeassistant),
):
    if service:
        form = await request.form()
        await ha.call_service(
            service, {k: v for k, v in form.items() if k != "service"}
        )
    return await serve_html(request, filename, page, config, ha)


@router.get("/{filename:path}")
async def serve_static(
    filename: str,
    config: PagesConfig = Depends(get_pages_config),
):
    return FileResponse(resolve_safe_path(config.html_folders, filename))
