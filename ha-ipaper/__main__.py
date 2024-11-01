#!/bin/python3

import argparse
import sys
import logging
import logging.config
import time
import yaml
import signal
from homeassistant_api import Client
from flask import Flask, redirect, render_template, request, send_from_directory, abort, url_for
import time
import datetime
import httpserver
import os
from werkzeug.utils import secure_filename

_LOGGER = logging.getLogger(__name__)

app = Flask(__name__)

sRunning = True
HTML_TEMPLATE_DIRECTORY = ""  # Update this path to your files directory

def format_exception(e):
    return f"Exception: {type(e).__name__}, Arguments: {e.args}"

# -------------------------------------------------------------------

#Handle
@app.route('/')
def index():
    return redirect('index.html')

# -------------------------------------------------------------------

@app.route('/<path:filename>')
def serve_file(filename):

    # Ensure the requested file is within the specified directory
    file_path = os.path.abspath(os.path.join(HTML_TEMPLATE_DIRECTORY, filename))

    # Check if the file exists and is within the specified directory
    if not os.path.isfile(file_path) or not os.path.commonpath([file_path, HTML_TEMPLATE_DIRECTORY]) == HTML_TEMPLATE_DIRECTORY:
        abort(404)
    
    if not filename.endswith(".html"):
        return send_from_directory(HTML_TEMPLATE_DIRECTORY, filename)
    
    with Client(config['general']['homeassistant_url'], config['general']['homeassistant_token'] ) as client: 
        entities = client.get_entities()

    try:
        data = {
            "title": "Home Assistant Interactive ePaper Dashboard",
            "entities": entities,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "page": request.args.get('page', 'home'),
        }
        
        return render_template(filename, **data)
    except Exception as e:
        _LOGGER.exception("Error while rendering index page")
        abort(500, description=format_exception(e))

# -------------------------------------------------------------------

def exit_signal_handler(signal, frame):
    global sRunning
    sRunning = False

# -------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog = 'HA-IPaper',  description = 'Home assistant interactive ePaper Dashboard')
    parser.add_argument("-config", type=str, help="Configuration file (yaml)")
    
    args = parser.parse_args()

    config = None
    try:
        with open(args.config, "r") as stream:
            config = yaml.safe_load(stream.read())
    except:
        _LOGGER.exception("Unable to load configuration file: %s" % (args.config))
        sys.exit(1)

    logging.config.dictConfig(config["logger"])

    _LOGGER.info("Intializating ...")

    HTML_TEMPLATE_DIRECTORY = os.path.abspath(config["general"]["html_template"])
    app.template_folder = HTML_TEMPLATE_DIRECTORY
    app.debug = True #Avoid template caching
    
    _LOGGER.info("Starting ...")

    signal.signal(signal.SIGTERM, exit_signal_handler)
    signal.signal(signal.SIGINT, exit_signal_handler)
    
    server = httpserver.FlaskServer(app)
    
    server.setup( config["server"]["bind_addr"], config["server"]["bind_port"])
    
    server.start()
   
    _LOGGER.info("Running ...")
    try:
        while sRunning:
            signal.pause()
    except AttributeError:
        # signal.pause() is missing for Windows; wait 100ms and loop instead
        while sRunning:
            try:
                time.sleep(0.1)
            except KeyboardInterrupt:
                pass

    _LOGGER.info("Stopping ...")    
    
    server.stop()