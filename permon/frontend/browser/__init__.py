from urllib import parse
import webbrowser
import json
import threading
import time
import logging
import bisect
import secrets
from permon.frontend import MonitorApp, Monitor
from permon import backend, exceptions, security, config

# these modules will be imported later because flask
# might not be installed
flask = None
flask_sockets = None
flask_login = None
gevent = None
geventwebsocket = None
User = None


def import_delayed():
    import flask  # noqa: F401
    import flask_sockets  # noqa: F401
    import flask_login  # noqa: F401
    import gevent  # noqa: F401
    import geventwebsocket  # noqa: F401
    from permon.frontend.browser.utils import User  # noqa: F401

    globals().update(locals().copy())


class BrowserMonitor(Monitor):
    """
    A browser monitor. This class only handle updating the stat and providing
    JSON info about it. The logic is done on the frontend in src/monitors.js.
    """
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
    def __init__(self, stats, colors, port, ip, open_browser,
                 buffer_size=None, fps=None, ssl_context=None):
        buffer_size = buffer_size or 50
        fps = fps or 1
        super(BrowserApp, self).__init__(stats, colors, buffer_size, fps)

        self.port = port
        self.ip = ip
        self.open_browser = open_browser
        self.ssl_context = ssl_context
        self.password_hash = config.get_config()['password']
        self.stopped = False

    def _get_assets(self, path):
        return flask.send_from_directory(self.get_asset_path(), path)

    def _get_from_build_dir(self, path):
        return flask.send_from_directory('dist', path)

    def _get_index(self):
        # the password hash can be passes as GET parameter
        if not flask_login.current_user.is_authenticated:
            token = flask.request.args.get('token')
            # if it is not passed or incorrent, redirect to the login page
            if token and token == self.password_hash:
                flask_login.login_user(self.user)
            else:
                return flask.redirect('/login')

        template_args = {
            'fps': self.fps,
            'buffer_size': self.buffer_size,
            'displayed_stats': self.get_displayed_stats(),
            'not_displayed_stats': self.get_not_displayed_stats()
        }
        return flask.render_template('index.html', **template_args)

    def _get_login(self):
        if flask_login.current_user.is_authenticated:
            return flask.redirect('/')
        return flask.send_from_directory('static', 'login.html')

    def _post_login(self):
        json_content = flask.request.get_json()
        if not json_content:
            return flask.Response(status=400)

        password = json_content['password']
        if password == self.password_hash:
            flask_login.login_user(self.user)
            return flask.redirect('/')

        return flask.Response('Wrong password or login token.', status=401)

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
            if not flask_login.current_user.is_authenticated:
                break

            stat_updates = dict()
            for monitor in self.monitors:
                if monitor.contributors:
                    stat_updates[monitor.stat.tag] = [monitor.value,
                                                      monitor.contributors]
                else:
                    stat_updates[monitor.stat.tag] = monitor.value

            # send updates about all currently displayed stats
            try:
                ws.send(json.dumps(stat_updates))
            except geventwebsocket.exceptions.WebSocketError:
                logging.info(f'{origin} disconnected')
                ws.close()

            gevent.sleep(1 / self.fps)

    def _add_stat_handler(self):
        data = flask.request.get_json()
        try:
            stat = backend.get_stats_from_repr(data)
        except (exceptions.InvalidStatError,
                exceptions.StatNotAvailableError) as e:
            return flask.Response(str(e), status=400)

        if stat in self.stats:
            return flask.Response('Stat already added.', status=400)

        # send info about the stat when a stat is added successfully
        monitor = self.add_stat(stat)
        return flask.Response(json.dumps(monitor.get_json_info()),
                              status=200, mimetype='application/json')

    def _remove_stat_handler(self):
        data = flask.request.get_json()
        try:
            stat = backend.get_stats_from_repr(data['tag'])
        except exceptions.InvalidStatError:
            return flask.Response(status=400)

        monitor = self.remove_stat(stat)

        if monitor is None:
            return flask.Response('Stat already removed.', status=400)

        # send info about the stat if it was removed successfully
        return flask.Response(json.dumps(monitor.get_json_info()),
                              status=200, mimetype='application/json')

    def add_stat(self, stat, add_to_config=True):
        monitor = BrowserMonitor(stat, color=self.next_color(),
                                 buffer_size=self.buffer_size,
                                 fps=self.fps,
                                 app=self)
        tags = [stat.tag for stat in self.stats]
        # make sure that the stats stay in alphabetical order
        new_index = bisect.bisect(tags, monitor.stat.tag)
        self.monitors.insert(new_index, monitor)

        super(BrowserApp, self).add_stat(stat, add_to_config=add_to_config)

        return monitor

    def remove_stat(self, stat, remove_from_config=True):
        monitor_of_stat = None
        for monitor in self.monitors:
            if isinstance(monitor.stat, stat):
                monitor_of_stat = monitor

        if monitor_of_stat is not None:
            self.monitors.remove(monitor_of_stat)
            super(BrowserApp, self).remove_stat(
                stat, remove_from_config=remove_from_config)
        else:
            logging.error(f'Removing {stat.tag} failed')

        return monitor_of_stat

    def initialize(self):
        if self.password_hash is None:
            token = secrets.token_hex()
            logging.warning(('No password set. '
                             'A random token to login has been generated: '
                             f'{token}'))
            self.password_hash = security.encrypt_password(token)

        # make the user id a function of the password so that sessions
        # are invalidated when the password changes
        self.user = User(security.encrypt_password(self.password_hash))

        self.app = flask.Flask(__name__)
        self.app.config.update(
            SECRET_KEY=security.get_secret_key()
        )
        self.login_manager = flask_login.LoginManager(app=self.app)
        self.login_manager.login_view = '_get_login'

        def user_loader(user_id):
            return self.user if user_id == self.user.id else None

        self.login_manager.user_loader(user_loader)
        self.sockets = flask_sockets.Sockets(self.app)

        for stat in self.initial_stats:
            self.add_stat(stat, add_to_config=False)

        # Routings can not be done in the regular Flask way with
        # decorators because the app is not available when the class definition
        # is executed
        routings = {
            ('/', 'GET'): [self._get_index],
            ('/login', 'GET'): [self._get_login],
            ('/login', 'POST'): [self._post_login],
            ('/assets/<path:path>', 'GET'): [self._get_assets],
            ('/dist/<path:path>', 'GET'): [self._get_from_build_dir],
            ('/allStats', 'GET'): [flask_login.login_required,
                                   self._get_all_stats],
            ('/stats', 'GET'): [flask_login.login_required, self._get_stat],
            ('/stats', 'DELETE'): [flask_login.login_required,
                                   self._remove_stat_handler],
            ('/stats', 'PUT'): [flask_login.login_required,
                                self._add_stat_handler]
        }

        for (rule, method), functions in routings.items():
            # start with the last function in the list (index n)
            result_func = functions[-1]
            # apply functions with indeces from n - 1 to 0 to the base function
            for function in functions[:-1][::-1]:
                result_func = function(result_func)

            self.app.route(rule, methods=[method])(result_func)

        self.sockets.route('/stats')(flask_login.login_required(
            self._get_stat_updates))

        if logging.getLogger().isEnabledFor(logging.INFO):
            logging_level = 'default'
        else:
            logging_level = None

        handler = geventwebsocket.handler.WebSocketHandler
        ssl_args = {
            'certfile': self.ssl_context[0],
            'keyfile': self.ssl_context[1]
        } if self.ssl_context else {}

        server = gevent.pywsgi.WSGIServer((self.ip, self.port), self.app,
                                          handler_class=handler,
                                          log=logging_level, **ssl_args)
        update_thread = threading.Thread(target=self.update_forever)
        update_thread.start()

        protocol = 'https' if self.ssl_context else 'http'
        url = parse.urlunparse(
            (protocol, f'{self.ip}:{self.port}', '/',
             '', f'token={self.password_hash}', '')
        )

        if self.open_browser:
            logging.info(f'Opening {url}')
            webbrowser.open(url)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.stop()
            print()

        self.stopped = True
        update_thread.join()
        # delete the monitors explicitly so that threads inside stats stop
        del self.monitors

    def update_forever(self):
        while not self.stopped:
            self.update()
            time.sleep(1 / self.fps)

    def make_available(self):
        self.verify_installed('flask')
        self.verify_installed('flask_sockets')
        self.verify_installed('flask_login')

        import_delayed()
