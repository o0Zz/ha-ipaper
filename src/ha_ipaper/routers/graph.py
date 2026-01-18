"""SVG router for extracting and serving SVG symbols."""

import io
import logging
from datetime import datetime, timedelta

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from ha_ipaper.core.config import PagesConfig
from ha_ipaper.core.dependencies import get_homeassistant, get_pages_config
from ha_ipaper.services.homeassistant import HomeAssistantService

_LOGGER = logging.getLogger(__name__)

router = APIRouter(tags=["graph"])


@router.get("/graph.svg")
def graph_svg(
    sensor: str = Query(..., description="Sensor entity id"),
    ha: HomeAssistantService = Depends(get_homeassistant),
    config: PagesConfig = Depends(get_pages_config),
):
    entity = ha.get_entity(sensor)
    if entity is None:
        return Response(content="", media_type="image/svg+xml", status_code=404)

    history = ha.get_history(
        sensor, datetime.now() - timedelta(days=config.graph_days), datetime.now()
    )
    matplotlib.use("Agg")

    x = [entry[0] for entry in history]
    y = [entry[1] for entry in history]

    fig, ax = plt.subplots(figsize=(7, 3))

    ax.plot(x, y, color="#1f2937", linewidth=1.0)

    # Axes
    ax.set_ylabel(
        f"{entity.state.attributes['device_class']} ({entity.state.attributes['unit_of_measurement']})",
        fontsize=9,
    )

    # Date & temps
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    # Grille légère
    ax.grid(True, which="major", axis="y", linestyle="--", linewidth=0.5, alpha=0.4)

    # Nettoyage visuel
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.tick_params(axis="both", labelsize=8)
    ax.margins(x=0)

    fig.tight_layout()

    # Export to SVG
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight")
    plt.close(fig)

    return Response(content=buffer.getvalue(), media_type="image/svg+xml")
