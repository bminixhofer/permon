from urllib import parse
import webbrowser
import json
import threading
import time
import logging
import flask
import sys
import os
from flask import Flask, Response, request, redirect
from flask_sockets import Sockets
import gevent
from gevent import pywsgi
import geventwebsocket
from geventwebsocket.handler import WebSocketHandler
from permon.frontend import MonitorApp, Monitor
from permon import backend


class BrowserMonitor(Monitor):
    def __init__(self, *args, **kwargs):
        super(BrowserMonitor, self).__init__(*args, **kwargs)
        self.values = []
        self.value = 0
        self.contributors = {}

    def update(self):
        if self.stat.has_contributor_breakdown:
            value, contributors = self.stat.get_stat()
        else:
            value = self.stat.get_stat()
            contributors = {}

        self.value = value
        self.contributors = contributors

        self.values.append(self.value)
        if len(self.values) > self.buffer_size:
            del self.values[0]

    def get_json_info(self):
        return {
            'color': self.color,
            'minimum': self.stat.minimum,
            'maximum': self.stat.maximum,
            'tag': self.stat.tag,
            'name': self.stat.name,
            'history': self.values
        }

    def paint(self):
        pass


class BrowserApp(MonitorApp):
    def __init__(self, stats, colors, buffer_size, fps, port, ip):
        super(BrowserApp, self).__init__(stats, colors, buffer_size, fps)

        self.port = port
        self.ip = ip
        self.stopped = False

    def _get_stat_tree(self):
        stats = backend.get_all_stats()

        stat_tree = dict()
        for stat in stats:
            if stat.root_tag not in stat_tree:
                stat_tree[stat.root_tag] = []

            stat_tree[stat.root_tag].append({
                'tag': stat.tag,
                'name': stat.name,
                'checked': stat in self.stats
            })
        stat_tree = [{
            'name': root_tag,
            'stats': stats
        } for root_tag, stats in stat_tree.items()]
        return stat_tree

    def initialize(self):
        self.app = Flask(__name__)
        self.sockets = Sockets(self.app)

        self.adjust_monitors()

        @self.app.route('/assets/<path:path>')
        def assets(path):
            return flask.send_from_directory(self.get_asset_path(), path)

        @self.app.route('/')
        def index():
            return flask.render_template('index.html',
                                         fps=self.fps,
                                         buffer_size=self.buffer_size,
                                         stats=self.setup_info)

        @self.app.route('/settings')
        def settings():
            return flask.render_template('settings.html',
                                         categories=self._get_stat_tree())

        @self.app.route('/statInfo')
        def stat_info():
            return Response(json.dumps(self.setup_info), mimetype='text/json')

        @self.sockets.route('/statUpdates')
        def socket(ws):
            origin = ws.origin
            logging.info(f'{origin} connected')
            while not ws.closed:
                stat_updates = dict()
                for monitor in self.monitors:
                    if monitor.contributors:
                        stat_updates[monitor.stat.tag] = [monitor.value,
                                                          monitor.contributors]
                    else:
                        stat_updates[monitor.stat.tag] = monitor.value

                try:
                    ws.send(json.dumps(stat_updates))
                except geventwebsocket.exceptions.WebSocketError:
                    logging.info(f'{origin} disconnected')
                    ws.close()

                gevent.sleep(1 / self.fps)

        @self.app.route('/settings', methods=['POST'])
        def set_settings():
            self.stats = backend.get_stats_from_tags(list(request.form.keys()))
            self.adjust_monitors()

            return redirect('/')

        if logging.getLogger().isEnabledFor(logging.INFO):
            logging_level = 'default'
        else:
            logging_level = None
        server = pywsgi.WSGIServer((self.ip, self.port), self.app,
                                   handler_class=WebSocketHandler,
                                   log=logging_level,
                                   error_log=open('trash', 'w'))
        update_thread = threading.Thread(target=self.update_forever)
        update_thread.start()

        url = parse.urlunparse(
            ('http', f'{self.ip}:{self.port}', '/', '', '', '')
        )

        webbrowser.open(url)

        stderr = sys.stderr
        try:
            sys.stderr = open(os.devnull, 'w')
            server.serve_forever()
        except KeyboardInterrupt:
            server.stop()
            print()
        finally:
            sys.stderr = stderr

        self.stopped = True
        update_thread.join()
        del self.monitors

    def adjust_monitors(self):
        displayed_stats = []
        removed_monitors = []
        for monitor in self.monitors:
            if type(monitor.stat) in self.stats:
                displayed_stats.append(type(monitor.stat))
            else:
                removed_monitors.append(monitor)

        for monitor in removed_monitors:
            self.monitors.remove(monitor)

        new_stats = list(set(self.stats) - set(displayed_stats))
        new_stats = sorted(new_stats, key=lambda stat: stat.tag)
        for stat in new_stats:
            monitor = BrowserMonitor(stat, color=self.next_color(),
                                     buffer_size=self.buffer_size,
                                     fps=self.fps,
                                     app=self)
            self.monitors.append(monitor)

        self.monitors = sorted(self.monitors,
                               key=lambda monitor: monitor.stat.tag)

        self.setup_info = [monitor.get_json_info()
                           for monitor in self.monitors]

        if logging.getLogger().isEnabledFor(logging.INFO):
            displayed = [stat.tag for stat in displayed_stats] or 'No Monitors'
            new = [stat.tag for stat in new_stats] or 'No Monitors'
            removed = [monitor.stat.tag for monitor in removed_monitors] or \
                'No Monitors'

            logging.info('Adjusted monitors')
            logging.info(f'{displayed} were already displayed')
            logging.info(f'{new} were added')
            logging.info(f'{removed} were removed')

    def update_forever(self):
        while not self.stopped:
            self.update()
            time.sleep(1 / self.fps)

    def paint(self):
        pass
