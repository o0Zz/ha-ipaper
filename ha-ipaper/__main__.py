#!/bin/python3

import argparse
import sys
import logging
import logging.config
import time
import yaml
import signal
from homeassistant_api import Client
from flask import Flask, redirect, render_template, request, send_from_directory, abort
import time
import datetime
import httpserver
import os
from functools import lru_cache

from xml.etree import ElementTree as ET

_LOGGER = logging.getLogger(__name__)

app = Flask(__name__)

gConfig = None
gRunning = True

# -------------------------------------------------------------------

@lru_cache(maxsize=64) # Cache the result of the last 64 calls (So at the end 64 icons will be cached which is enough, today we only use < 20)
def extract_svg_symbol(svg_fullpath, symbol_id):
    root = ET.parse(svg_fullpath).getroot()

    _LOGGER.debug(f"Extracting symbol {symbol_id} from {svg_fullpath}")

    namespace = {'svg': 'http://www.w3.org/2000/svg'}
    ET.register_namespace('', namespace['svg'])

    # Find the symbol with the specified ID
    symbol = root.find(f".//svg:symbol[@id='{symbol_id}']", namespaces=namespace)

    if symbol is None:
        return None

    standalone_svg = ET.Element('svg', {'viewBox': symbol.get('viewBox', '0 0 100 100') })

    for element in symbol:
        standalone_svg.append(element)
    
    return ET.tostring(standalone_svg, encoding='utf-8', xml_declaration=True)

# -------------------------------------------------------------------

#Handle
@app.route('/')
def index():
    return redirect('index.html')

# -------------------------------------------------------------------

@app.route('/<path:filename>.svg', methods=['GET'])
def serve_svg(filename):
    html_folder = os.path.abspath(gConfig["general"]["html_template"])
    file_path = os.path.abspath(os.path.join(html_folder, f"{filename}.svg"))
     
    symbol_id = request.args.get('id', None)        
    if symbol_id:
        svg = extract_svg_symbol(file_path, request.args.get('id', None))
        if svg is None:
            abort(404, description="SVG symbol not found")

        return svg.decode('utf-8'), 200, {'Content-Type': 'image/svg+xml'}

    return send_from_directory(html_folder, filename)

# -------------------------------------------------------------------

@app.route('/<path:filename>', methods=['GET', 'POST'])
def serve_file(filename):
        
    with Client(gConfig['general']['homeassistant_url'], gConfig['general']['homeassistant_token'], cache_session=False ) as homeassistant_client:
        
        html_folder = os.path.abspath(gConfig["general"]["html_template"])

        # Ensure the requested file is within the specified directory
        file_path = os.path.abspath(os.path.join(html_folder, filename))

        if request.method == 'POST':
            service = request.form.get('service', None)
            if service is not None:
                dict = {key: value for key, value in request.form.items() if key != "service"}
                domain, function = service.split(".")
                homeassistant_client.trigger_service(domain, function, **dict)
               
            time.sleep(0.5) #FIXME: workaround wait for HA to update the state (Need to properly wait state change)

        # Check if the file exists and is within the specified directory
        if not os.path.isfile(file_path) or not os.path.commonpath([file_path, html_folder]) == html_folder:
            abort(404)

        if filename.endswith(".html"):
            try:
                data = {
                    "title": "Home Assistant Interactive ePaper Dashboard",
                    "menu": gConfig["menu"],
                    "entities": homeassistant_client.get_entities(),
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "page": request.args.get('page', None),
                }
                
                return render_template(filename, **data)
            except Exception as e:
                _LOGGER.exception("Error while rendering index page")
                abort(500, description=f"Exception: {type(e).__name__}, Arguments: {e.args}")

        return send_from_directory(html_folder, filename)
    
# -------------------------------------------------------------------

def exit_signal_handler(signal, frame):
    global gRunning
    gRunning = False
    _LOGGER.info("Signal received, shutting down...")

# -------------------------------------------------

def main():
    global gConfig
    parser = argparse.ArgumentParser(prog = 'HA-IPaper',  description = 'Home assistant interactive ePaper Dashboard')
    parser.add_argument("-config", type=str, help="Configuration file (yaml)")
    
    args = parser.parse_args()

    gConfig = None
    try:
        with open(args.config, "r") as stream:
            gConfig = yaml.safe_load(stream.read())
    except:
        _LOGGER.exception("Unable to load configuration file: %s" % (args.config))
        sys.exit(1)

    logging.config.dictConfig(gConfig["logger"])

    _LOGGER.info("Intializating ...")

    app.template_folder = os.path.abspath(gConfig["general"]["html_template"])
    app.debug = gConfig["server"]["debug"]

    _LOGGER.info("Starting ...")

    signal.signal(signal.SIGTERM, exit_signal_handler)
    signal.signal(signal.SIGINT, exit_signal_handler)
    
    server = httpserver.FlaskServer(app)
    
    server.setup( gConfig["server"]["bind_addr"], gConfig["server"]["bind_port"])
    
    server.start()
   
    _LOGGER.info("Running ...")
    try:
        while gRunning:
            time.sleep(0.1)
    except KeyboardInterrupt:
        _LOGGER.info("Keyboard interrupt received, exiting...")

    _LOGGER.info("Stopping ...")    
    
    server.stop()

if __name__ == '__main__':
    main()