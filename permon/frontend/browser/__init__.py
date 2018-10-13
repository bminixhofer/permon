from urllib import parse
import webbrowser
import json
import threading
import time
from flask import Flask, render_template, Response, request, redirect
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
    def __init__(self, tags, colors, buffer_size, fps, port, ip):
        super(BrowserApp, self).__init__(tags, colors, buffer_size, fps)

        self.port = port
        self.ip = ip
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
        self.adjust_monitors()

    def adjust_monitors(self):
        displayed_monitor_tags = []
        removed_monitors = []
        for monitor in self.monitors:
            if monitor.full_tag in self.tags:
                displayed_monitor_tags.append(monitor.full_tag)
            else:
                removed_monitors.append(monitor)

        for monitor in removed_monitors:
            self.monitors.remove(monitor)

        new_tags = list(set(self.tags) - set(displayed_monitor_tags))

        for stat in backend.get_all_stats():
            if stat.get_full_tag() in new_tags and stat.is_available():
                instance = stat()
                monitor = BrowserMonitor(instance, color=self.next_color(),
                                         **self.monitor_params)
                self.monitors.append(monitor)

        self.setup_info = [monitor.get_json_info()
                           for monitor in self.monitors]

    def _get_stat_tree(self):
        stats = backend.get_all_stats()
        stats = [(x.get_full_tag().split('.')[0], x) for x in stats]
        stat_tree = dict()
        for root, stat in stats:
            if root not in stat_tree:
                stat_tree[root] = []

            stat_tree[root].append({
                'tag': stat.tag,
                'name': stat.name,
                'checked': stat.get_full_tag() in self.tags
            })
        stat_tree = [{
            'name': root,
            'stats': stats
        } for root, stats in stat_tree.items()]
        return stat_tree

    def initialize(self):
        @self.app.route('/')
        def index():
            return render_template('index.html', stats=self.setup_info)

        @self.app.route('/settings', methods=['POST'])
        def set_settings():
            self.tags = list(request.form.keys())
            self.adjust_monitors()

            return redirect('/')

        @self.app.route('/settings')
        def settings():
            return render_template('settings.html',
                                   categories=self._get_stat_tree())

        @self.app.route('/statInfo')
        def stat_info():
            return Response(json.dumps(self.setup_info), mimetype='text/json')

        @self.sockets.route('/statUpdates')
        def socket(ws):
            while not ws.closed:
                stat_updates = {monitor.full_tag: monitor.value
                                for monitor in self.monitors}
                ws.send(json.dumps(stat_updates))
                gevent.sleep(1)

        server = pywsgi.WSGIServer((self.ip, self.port), self.app,
                                   handler_class=WebSocketHandler)
        update_thread = threading.Thread(target=self.update_forever)
        update_thread.start()

        url = parse.urlunparse(
            ('http', f'{self.ip}:{self.port}', '/', '', '', '')
        )

        # DEBUG: added settings
        webbrowser.open(url + '/settings')
        server.serve_forever()

    def update_forever(self):
        while True:
            self.update()
            time.sleep(1 / self.fps)

    def paint(self):
        pass
