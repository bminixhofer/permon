import sys
import os
import logging
import signal
from permon.frontend import Monitor, MonitorApp

# these modules will be imported later because PySide2
# might not be installed
QtWidgets = None
QtGui = None
QtCore = None
QtQuick = None
Qt = None
MonitorModel = None
SettingsModel = None


def import_delayed():
    from PySide2 import QtWidgets, QtGui, QtCore, QtQuick  # noqa: F401
    from PySide2.QtCore import Qt  # noqa: F401
    from permon.frontend.native.utils import (MonitorModel,  # noqa: F401
                                              SettingsModel)

    globals().update(locals().copy())


class NativeMonitor(Monitor):
    def __init__(self, stat, buffer_size, fps, color,
                 app, thickness):
        super(NativeMonitor, self).__init__(stat, buffer_size,
                                            fps, color, app)
        self.value = 0
        self.contributors = []

    def update(self):
        # every frame, we remove the last point of the history and
        # append a new measurement to the end
        if self.stat.has_contributor_breakdown:
            value, contributors = self.stat.get_stat()
        else:
            value = self.stat.get_stat()
            contributors = []

        self.value = value
        self.contributors = contributors


class NativeApp(MonitorApp):
    # QApplication is a global singleton. It can only ever be instantiated once
    qapp = None
    fonts = None

    def __init__(self, stats, colors, buffer_size=None, fps=None,
                 line_thickness=2):
        buffer_size = buffer_size or 500
        fps = fps or 10
        self.line_thickness = line_thickness

        super(NativeApp, self).__init__(stats, colors, buffer_size, fps)

    def add_stat(self, stat, add_to_config=True):
        monitor = NativeMonitor(stat,
                                color=self.next_color(),
                                buffer_size=self.buffer_size,
                                fps=self.fps,
                                app=self,
                                thickness=self.line_thickness)
        self.monitor_model.addMonitor(monitor)
        super(NativeApp, self).add_stat(stat, add_to_config=add_to_config)

    def remove_stat(self, stat, remove_from_config=True):
        monitor_of_stat = None
        for monitor in self.monitors:
            if isinstance(monitor.stat, stat):
                monitor_of_stat = monitor

        if monitor_of_stat is not None:
            self.monitor_model.removeMonitor(monitor_of_stat)
            super(NativeApp, self).remove_stat(
                stat, remove_from_config=remove_from_config)
        else:
            logging.error(f'Removing {stat.tag} failed')

    def initialize(self):
        # create a MonitorModel to communicate with the QML view
        self.monitor_model = MonitorModel()
        self.monitors = self.monitor_model.monitors

        # create a SettingsModel to communicate with the settings drawer
        # in the QML view
        self.settings_model = SettingsModel(self)
        # connect the statAdded and statRemoved signals
        self.settings_model.statAdded.connect(self.add_stat)
        self.settings_model.statRemoved.connect(self.remove_stat)

        if self.qapp is None:
            self.qapp = QtWidgets.QApplication(sys.argv)

            # add custom fonts
            font_db = QtGui.QFontDatabase()
            font_paths = [
                self.get_asset_path('Raleway-Regular.ttf'),
                self.get_asset_path('RobotoMono-Regular.ttf')
            ]
            for font_path in font_paths:
                font_id = font_db.addApplicationFont(font_path)
                if font_id == -1:
                    logging.warn(f'Could not load font ({font_path})')

            font = QtGui.QFont('Raleway')
            self.qapp.setFont(font)

            # set favicon
            icon_info = [
                ('icons/favicon-16x16.png', (16, 16)),
                ('icons/favicon-32x32.png', (32, 32)),
                ('icons/android-chrome-192x192.png', (192, 192)),
                ('icons/android-chrome-256x256.png', (256, 256))
            ]

            app_icon = QtGui.QIcon()
            for path, size in icon_info:
                app_icon.addFile(
                    self.get_asset_path(path), QtCore.QSize(*size))
            self.qapp.setWindowIcon(app_icon)

        for stat in self.initial_stats:
            self.add_stat(stat, add_to_config=False)

        view = QtQuick.QQuickView()
        view.setResizeMode(QtQuick.QQuickView.SizeRootObjectToView)

        root_context = view.rootContext()
        # make monitor model and settings model available in QML
        root_context.setContextProperty('monitorModel', self.monitor_model)
        root_context.setContextProperty('settingsModel', self.settings_model)

        # qml/view.qml is the root QML file
        qml_file = os.path.join(os.path.dirname(__file__), 'qml', 'view.qml')
        view.setSource(QtCore.QUrl.fromLocalFile(os.path.abspath(qml_file)))

        if view.status() == QtQuick.QQuickView.Error:
            sys.exit(-1)

        def signal_handler(signal, frame):
            # the app can not gracefully quit
            # when there is a keyboard interrupt
            # because the QAbstractListModel catches all errors
            # in a part of its code
            print()
            os._exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        view.show()
        self.qapp.exec_()
        self.quit()

    def quit(self):
        # delete everything with a reference to monitors
        # so that all stats are deleted, and possible threads
        # they are using stopped
        del self.monitors
        del self.settings_model
        del self.monitor_model
        self.qapp.exit()

    def make_available(self):
        self.verify_installed('PySide2')

        import_delayed()
