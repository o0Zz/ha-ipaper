"""SVG router for extracting and serving SVG symbols."""

import logging
from functools import lru_cache
from xml.etree import ElementTree as ET

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response

from ha_ipaper.core.config import PagesConfig
from ha_ipaper.core.dependencies import get_pages_config
from ha_ipaper.utils.filesystem import resolve_safe_path

_LOGGER = logging.getLogger(__name__)

router = APIRouter(tags=["svg"])


@lru_cache(maxsize=64)
def extract_symbol(svg_fullpath: str, symbol_id: str) -> bytes | None:
    """Extract a symbol from an SVG file and return it as a standalone SVG."""
    root = ET.parse(svg_fullpath).getroot()
    _LOGGER.debug(f"Extracting symbol {symbol_id} from {svg_fullpath}")

    namespace = {"svg": "http://www.w3.org/2000/svg"}
    ET.register_namespace("", namespace["svg"])

    symbol = root.find(f".//svg:symbol[@id='{symbol_id}']", namespaces=namespace)
    if symbol is None:
        return None

    standalone_svg = ET.Element(
        "svg", {"viewBox": symbol.get("viewBox", "0 0 100 100")}
    )
    for element in symbol:
        standalone_svg.append(element)

    return ET.tostring(standalone_svg, encoding="utf-8", xml_declaration=True)


@router.get("/{path:path}.svg")
async def serve_svg(
    path: str,
    id: str | None = Query(default=None),
    config: PagesConfig = Depends(get_pages_config),
):
    """Serve SVG files, optionally extracting a specific symbol."""
    file_path = resolve_safe_path(config.html_folders, path, ".svg")

    if id:
        svg = extract_symbol(file_path, id)
        if svg is None:
            raise HTTPException(status_code=404, detail="SVG symbol not found")
        return Response(content=svg.decode("utf-8"), media_type="image/svg+xml")

    return FileResponse(file_path, media_type="image/svg+xml")
