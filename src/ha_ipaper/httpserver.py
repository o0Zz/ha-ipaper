from werkzeug.serving import make_server
import threading
import flask
import logging

_LOGGER = logging.getLogger(__name__)

class FlaskServer(threading.Thread):

    def __init__(self, app: flask.Flask):
        threading.Thread.__init__(self)
        self.app = app
    
    def setup(self, bind: str, port: int):
        self.server = make_server(bind, port, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()
        
    def start(self):
        threading.Thread.start(self)
        
    def stop(self):
        self.server.shutdown()