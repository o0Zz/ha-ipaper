#!/bin/python3
import argparse
import datetime
import logging
import logging.config
import os
import signal
import sys
import time
from functools import lru_cache
from xml.etree import ElementTree as ET

import yaml
from flask import (
    Flask,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from homeassistant_api import WebsocketClient

from . import httpserver

_LOGGER = logging.getLogger(__name__)


class SVGHandler:
    @staticmethod
    @lru_cache(maxsize=64)
    def extract_symbol(svg_fullpath, symbol_id):
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


class WebServer:
    def __init__(
        self,
        html_folder: str,
        homeassistant_url: str,
        homeassistant_token: str,
        menu: dict,
        debug: bool,
    ):
        self.app = Flask(__name__)
        self.setup_routes()

        self.html_folder = os.path.abspath(html_folder)
        self.homeassistant_url = homeassistant_url
        self.homeassistant_token = homeassistant_token
        self.menu = menu

        if self.homeassistant_url.startswith(
            "http://"
        ) or self.homeassistant_url.startswith("https://"):
            self.homeassistant_url = self.homeassistant_url.replace(
                "http://", "ws://"
            ).replace("https://", "wss://")
            self.homeassistant_url += "/api/websocket"

        self.app.template_folder = self.html_folder
        self.app.debug = debug

    def abort(self, code, description=""):
        _LOGGER.error(f"Aborting with code {code}: {description}")
        response = make_response(
            f'<html><head><meta http-equiv="refresh" content="60"></head><body><h1>Error {code}</h1><br>{description}</body></html>',
            code,
        )
        response.headers["Content-Type"] = "text/html"
        return response

    def setup_routes(self):
        self.app.route("/", methods=["GET"])(self.serve_index)
        self.app.route("/<path:filename>.svg", methods=["GET"])(self.serve_svg)
        self.app.route("/<path:filename>", methods=["GET", "POST"])(self.serve_file)

    def serve_index(self):
        return redirect("index.html")

    def serve_svg(self, filename):
        file_path = os.path.abspath(os.path.join(self.html_folder, f"{filename}.svg"))

        symbol_id = request.args.get("id", None)
        if symbol_id:
            svg = SVGHandler.extract_symbol(file_path, request.args.get("id", None))
            if svg is None:
                return self.abort(404, description="SVG symbol not found")
            return svg.decode("utf-8"), 200, {"Content-Type": "image/svg+xml"}

        return send_from_directory(self.html_folder, filename)

    def serve_file(self, filename):
        try:
            with WebsocketClient(
                self.homeassistant_url, self.homeassistant_token
            ) as homeassistant_client:
                if request.method == "POST":
                    service = request.form.get("service", None)
                    if service is not None:
                        dict = {
                            key: value
                            for key, value in request.form.items()
                            if key != "service"
                        }
                        domain, function = service.split(".")

                        with homeassistant_client.listen_events(
                            "state_changed"
                        ) as events:
                            homeassistant_client.trigger_service(
                                domain, function, **dict
                            )
                            for event in events:
                                break

                file_path = os.path.abspath(os.path.join(self.html_folder, filename))
                if (
                    not os.path.isfile(file_path)
                    or not os.path.commonpath([file_path, self.html_folder])
                    == self.html_folder
                ):
                    return self.abort(404)

                if filename.endswith(".html"):
                    entities = homeassistant_client.get_entities()
                    entities["weather_forecast"] = (
                        homeassistant_client.trigger_service_with_response(
                            "weather",
                            "get_forecasts",
                            entity_id="weather.home",
                            type="daily",
                        )["weather.home"]["forecast"]
                    )

                    data = {
                        "title": "Home Assistant Interactive ePaper Dashboard",
                        "menu": self.menu,
                        "entities": entities,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "page": request.args.get("page", None),
                    }
                    return render_template(filename, **data)

                return send_from_directory(self.html_folder, filename)

        except Exception as e:
            _LOGGER.exception(f"Error while rendering {filename}")
            return self.abort(
                500, description=f"Exception: {type(e).__name__}, Arguments: {e.args}"
            )


gRunning = True


def exit_signal_handler(signal, frame):
    global gRunning
    gRunning = False
    _LOGGER.info("Signal received, shutting down...")


def main():
    parser = argparse.ArgumentParser(
        prog="HA-IPaper", description="Home assistant interactive ePaper Dashboard"
    )
    parser.add_argument("-config", type=str, help="Configuration file (yaml)")
    args = parser.parse_args()

    _LOGGER.info(f"Loading configuration... ({args.config})")

    config = None
    try:
        with open(args.config, "r") as stream:
            config = yaml.safe_load(stream.read())
        logging.config.dictConfig(config["logger"])
    except Exception:
        _LOGGER.exception(f"Unable to load configuration file: {args.config}")
        sys.exit(1)

    signal.signal(signal.SIGTERM, exit_signal_handler)
    signal.signal(signal.SIGINT, exit_signal_handler)

    web_server = WebServer(
        config["general"]["html_template"],
        config["general"]["homeassistant_url"],
        config["general"]["homeassistant_token"],
        config["menu"],
        config["server"]["debug"],
    )

    server = httpserver.FlaskServer(web_server.app)
    server.setup(config["server"]["bind_addr"], config["server"]["bind_port"])
    server.start()

    _LOGGER.info(
        f"Initialization done! Server is running {config['server']['bind_addr']}:{config['server']['bind_port']} ..."
    )

    try:
        while gRunning:
            time.sleep(0.1)
    except KeyboardInterrupt:
        _LOGGER.info("Keyboard interrupt received, exiting...")

    _LOGGER.info("Stopping ...")
    server.stop()


if __name__ == "__main__":
    main()
