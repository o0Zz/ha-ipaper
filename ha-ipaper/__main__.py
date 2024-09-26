#!/bin/python3

import argparse
import sys
import logging
import logging.config
import time
import yaml
import signal

_LOGGER = logging.getLogger(__name__)

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


    
    _LOGGER.info("Starting ...")

    signal.signal(signal.SIGTERM, exit_signal_handler)
    signal.signal(signal.SIGINT, exit_signal_handler)
    
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
