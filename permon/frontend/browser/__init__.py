from urllib import parse
import webbrowser
import json
import threading
import time
import logging
import bisect
from permon.frontend import MonitorApp, Monitor
from permon import backend, exceptions

flask = None
flask_sockets = None
gevent = None
geventwebsocket = None


def import_delayed():
    import flask  # noqa: F401
    import flask_sockets  # noqa: F401
    import gevent  # noqa: F401
    import geventwebsocket  # noqa: F401

    globals().update(locals().copy())


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
            'history': self.values,
        }


class BrowserApp(MonitorApp):
    def __init__(self, stats, colors, buffer_size, fps, port, ip,
                 open_browser):
        super(BrowserApp, self).__init__(stats, colors, buffer_size, fps)

        self.port = port
        self.ip = ip
        self.open_browser = open_browser
        self.stopped = False

    def _get_assets(self, path):
        return flask.send_from_directory(self.get_asset_path(), path)

    def _get_from_build_dir(self, path):
        return flask.send_from_directory('dist', path)

    def _get_index(self):
        template_args = {
                'fps': self.fps,
                'buffer_size': self.buffer_size,
                'displayed_stats': self.get_displayed_stats(),
                'not_displayed_stats': self.get_not_displayed_stats()
            }
        return flask.render_template('index.html', **template_args)

    def _get_stat(self):
        stat_info = [monitor.get_json_info() for monitor in self.monitors]
        return flask.Response(json.dumps(stat_info),
                              mimetype='application/json')

    def _get_all_stats(self):
        info = {}
        for stat in backend.get_all_stats():
            info[stat.tag] = {
                'settings': stat.settings
            }
        return flask.Response(json.dumps(info), mimetype='application/json')

    def _get_stat_updates(self, ws):
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

    def _add_stat_handler(self):
        data = flask.request.get_json()
        try:
            stat = backend.get_stats_from_tags(data['tag'])
        except (exceptions.InvalidStatError,
                exceptions.StatNotAvailableError) as e:
            return flask.Response(str(e), status=400)

        if stat in self.stats:
            return flask.Response('Stat already added.', status=400)

        stat.set_settings(data['settings'])
        monitor = self.add_stat(stat)
        return flask.Response(json.dumps(monitor.get_json_info()),
                              status=200, mimetype='application/json')

    def _remove_stat_handler(self):
        data = flask.request.get_json()
        try:
            stat = backend.get_stats_from_tags(data['tag'])
        except exceptions.InvalidStatError:
            return flask.Response(status=400)

        monitor = self.remove_stat(stat)
        return flask.Response(json.dumps(monitor.get_json_info()),
                              status=200, mimetype='application/json')

    def add_stat(self, stat):
        monitor = BrowserMonitor(stat, color=self.next_color(),
                                 buffer_size=self.buffer_size,
                                 fps=self.fps,
                                 app=self)
        tags = [stat.tag for stat in self.stats]
        new_index = bisect.bisect(tags, monitor.stat.tag)

        self.monitors.insert(new_index, monitor)
        logging.info(f'Added {stat.tag}')
        return monitor

    def remove_stat(self, stat):
        monitor_of_stat = None
        for monitor in self.monitors:
            if type(monitor.stat) == stat:
                monitor_of_stat = monitor

        if monitor_of_stat is not None:
            self.monitors.remove(monitor_of_stat)
            logging.info(f'Removed {stat.tag}')
        else:
            logging.error(f'Removing {stat.tag} failed')

        return monitor_of_stat

    def initialize(self):
        self.app = flask.Flask(__name__)
        self.sockets = flask_sockets.Sockets(self.app)

        for stat in self.stats:
            self.add_stat(stat)

        self.app.route('/')(self._get_index)
        self.app.route('/assets/<path:path>')(self._get_assets)
        self.app.route('/dist/<path:path>')(self._get_from_build_dir)
        self.app.route('/allStats', methods=['GET'])(self._get_all_stats)
        self.app.route('/stats', methods=['GET'])(self._get_stat)
        self.app.route('/stats', methods=['DELETE'])(self._remove_stat_handler)
        self.app.route('/stats', methods=['PUT'])(self._add_stat_handler)
        self.sockets.route('/stats')(self._get_stat_updates)

        if logging.getLogger().isEnabledFor(logging.INFO):
            logging_level = 'default'
        else:
            logging_level = None
        handler = geventwebsocket.handler.WebSocketHandler
        server = gevent.pywsgi.WSGIServer((self.ip, self.port), self.app,
                                          handler_class=handler,
                                          log=logging_level)
        update_thread = threading.Thread(target=self.update_forever)
        update_thread.start()

        url = parse.urlunparse(
            ('http', f'{self.ip}:{self.port}', '/', '', '', '')
        )

        if self.open_browser:
            webbrowser.open(url)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.stop()
            print()

        self.stopped = True
        update_thread.join()
        del self.monitors

    def update_forever(self):
        while not self.stopped:
            self.update()
            time.sleep(1 / self.fps)

    def make_available(self):
        self.verify_installed('flask')
        self.verify_installed('flask_sockets')

        import_delayed()
