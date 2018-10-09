import json
import threading
import time
from flask import Flask, render_template, Response
from flask_sockets import Sockets
import gevent
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from permon.frontend import MonitorApp, Monitor
from permon import exceptions, backend


class BrowserMonitor(Monitor):
    def __init__(self, *args, **kwargs):
        super(BrowserMonitor, self).__init__(*args, **kwargs)
        self.value = None
        self.top = {}

    def update(self):
        if self.stat.has_top_info:
            value, top = self.stat.get_stat()
        else:
            value = self.stat.get_stat()
            top = {}

        self.value = value
        self.top = top

    def get_json_info(self):
        return {
            'color': self.color,
            'minimum': self.stat.minimum,
            'maximum': self.stat.maximum,
            'tag': self.full_tag,
            'name': self.stat.name
        }

    def paint(self):
        pass


class BrowserApp(MonitorApp):
    def __init__(self, tags, colors, buffer_size, fps):
        super(BrowserApp, self).__init__(tags, colors, buffer_size, fps)

        self.stats = []
        for stat in backend.get_all_stats():
            if stat.get_full_tag() in tags and stat.is_available():
                instance = stat()
                self.stats.append(instance)

        self.app = Flask(__name__)
        self.sockets = Sockets(self.app)

        if len(self.stats) == 0:
            raise exceptions.NoStatError()

        self.monitors = []
        for stat in self.stats:
            self.monitors.append(BrowserMonitor(stat, buffer_size,
                                                fps, self.next_color(),
                                                self.app))

    def initialize(self):
        setup_info = [monitor.get_json_info() for monitor in self.monitors]

        @self.app.route('/')
        def page():
            print("rendering")
            return render_template('index.html', stats=setup_info)

        @self.app.route('/statInfo')
        def stat_info():
            return Response(json.dumps(setup_info), mimetype='text/json')

        @self.sockets.route('/statUpdates')
        def socket(ws):
            while not ws.closed:
                stat_updates = {monitor.full_tag: monitor.value
                                for monitor in self.monitors}
                print(stat_updates)
                ws.send(json.dumps(stat_updates))
                gevent.sleep(1)

        server = pywsgi.WSGIServer(('', 5000), self.app,
                                   handler_class=WebSocketHandler)
        update_thread = threading.Thread(target=self.update_forever)
        update_thread.start()

        server.serve_forever()

    def update_forever(self):
        while True:
            self.update()
            time.sleep(1 / self.fps)

    def paint(self):
        pass
