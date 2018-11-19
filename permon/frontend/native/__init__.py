import sys
import os
import logging
import bisect
import signal
import json
from PySide2 import QtWidgets
from PySide2.QtCore import (Qt, QUrl, QAbstractListModel, QObject, QModelIndex,
                            Slot, Signal)
import PySide2.QtGui as QtGui
from PySide2.QtQuick import QQuickView
from permon.frontend import Monitor, MonitorApp
from permon.backend import Stat
from permon import exceptions


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


class MonitorModel(QAbstractListModel):
    def __init__(self, parent=None):
        super(MonitorModel, self).__init__(parent)

        self.monitors = []

        def get_and_update_value(monitor):
            monitor.update()
            return monitor.value

        self.exposed_properties = {
            'tag': lambda monitor: monitor.stat.tag,
            'minimum': lambda monitor: monitor.stat.minimum,
            'maximum': lambda monitor: monitor.stat.maximum,
            'fps': lambda monitor: monitor.fps,
            'bufferSize': lambda monitor: monitor.buffer_size,
            'value': get_and_update_value,
            'contributors': lambda monitor: monitor.contributors,
            'color': lambda monitor: monitor.color,
            'name': lambda monitor: monitor.stat.name,
        }
        self._roles = {(Qt.UserRole + i): key.encode()
                       for i, key in enumerate(self.exposed_properties.keys())}

    def addMonitor(self, monitor):
        # make sure monitors stay in the same order
        monitor_tags = [monitor.stat.tag for monitor in self.monitors]
        new_index = bisect.bisect(monitor_tags, monitor.stat.tag)

        self.beginInsertRows(QModelIndex(), new_index, new_index)
        self.monitors.insert(new_index, monitor)
        self.endInsertRows()

    def removeMonitor(self, monitor):
        monitor_index = self.monitors.index(monitor)
        self.beginRemoveRows(QModelIndex(), monitor_index, monitor_index)
        del self.monitors[monitor_index]
        self.endRemoveRows()

    def rowCount(self, parent=QModelIndex()):
        return len(self.monitors)

    def data(self, index, role=Qt.DisplayRole):
        try:
            monitor = self.monitors[index.row()]
        except IndexError:
            return

        key = self._roles[role].decode()
        if key in self.exposed_properties:
            return self.exposed_properties[key](monitor)

    def roleNames(self):
        return self._roles


class SettingsModel(QObject):
    statAdded = Signal(Stat)
    statRemoved = Signal(Stat)

    def __init__(self, app):
        super(SettingsModel, self).__init__()
        self.app = app

    @Slot(int, str, result=str)
    def addStat(self, index, settings_str):
        settings = json.loads(settings_str)
        stat = self.app.get_not_displayed_stats()[index]
        stat.set_settings(settings)

        try:
            stat.check_availability()
        except exceptions.StatNotAvailableError as e:
            return str(e)

        self.statAdded.emit(stat)

    @Slot(int)
    def removeStat(self, index):
        stat = self.app.get_displayed_stats()[index]
        self.statRemoved.emit(stat)

    @Slot(int, result=str)
    def getSettings(self, index):
        stat = self.app.get_not_displayed_stats()[index]
        settings_list = [{
            'name': key,
            'defaultValue': value
        } for key, value in stat.default_settings.items()]

        return json.dumps(settings_list)

    @Slot(bool, result=str)
    def getStats(self, displayed):
        stats = self.app.get_displayed_stats() if displayed else \
                self.app.get_not_displayed_stats()
        return json.dumps([stat.name for stat in stats])


class NativeApp(MonitorApp):
    # QApplication is a global singleton. It can only ever be instantiated once
    qapp = None
    fonts = None

    def __init__(self, stats, colors, buffer_size, fps, line_thickness=2):
        super(NativeApp, self).__init__(stats, colors, buffer_size, fps)

        self.monitor_params = {
            'buffer_size': buffer_size,
            'fps': fps,
            'app': self,
            'thickness': line_thickness
        }
        self.monitor_model = MonitorModel()
        self.monitors = self.monitor_model.monitors

        self.settings_model = SettingsModel(self)
        self.settings_model.statAdded.connect(self.add_stat)
        self.settings_model.statRemoved.connect(self.remove_stat)

    def add_stat(self, stat):
        monitor = NativeMonitor(stat, color=self.next_color(),
                                **self.monitor_params)
        self.monitor_model.addMonitor(monitor)
        logging.info(f'Added {stat.tag}')

    def remove_stat(self, stat):
        monitor_of_stat = None
        for monitor in self.monitors:
            if type(monitor.stat) == stat:
                monitor_of_stat = monitor

        if monitor is not None:
            self.monitor_model.removeMonitor(monitor_of_stat)
            logging.info(f'Removed {stat.tag}')
        else:
            logging.error(f'Removing {stat.tag} failed')

    def initialize(self):
        if self.qapp is None:
            self.qapp = QtWidgets.QApplication(sys.argv)

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

        for stat in self.stats:
            self.add_stat(stat)

        view = QQuickView()
        view.setResizeMode(QQuickView.SizeRootObjectToView)

        root_context = view.rootContext()
        root_context.setContextProperty('monitorModel', self.monitor_model)
        root_context.setContextProperty('settingsModel', self.settings_model)

        qml_file = os.path.join(os.path.dirname(__file__), 'qml', 'view.qml')
        view.setSource(QUrl.fromLocalFile(os.path.abspath(qml_file)))

        if view.status() == QQuickView.Error:
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
