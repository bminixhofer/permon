import sys
import os
import logging
import bisect
from PySide2 import QtWidgets
from PySide2.QtCore import (Qt, QUrl, QAbstractListModel, QModelIndex, Slot,
                            Signal)
import PySide2.QtGui as QtGui
from PySide2.QtQuick import QQuickView
from permon.frontend import Monitor, MonitorApp
from permon import backend


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

    def paint(self):
        pass


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


class SettingsModel(QAbstractListModel):
    submitted = Signal(set)

    TypeRole = Qt.UserRole + 1
    CheckedRole = Qt.UserRole + 2
    TagRole = Qt.UserRole + 3
    NameRole = Qt.UserRole + 4

    _roles = {
        TypeRole: b'type',
        CheckedRole: b'checked',
        TagRole: b'tag',
        NameRole: b'name'
    }

    def __init__(self, displayed_monitors):
        super(SettingsModel, self).__init__()
        all_stats = backend.get_all_stats()

        prev_root_tag = ''
        for i, stat in enumerate(all_stats):
            root_tag = stat.root_tag

            if root_tag != prev_root_tag:
                all_stats.insert(i, root_tag)
            prev_root_tag = root_tag

        self.monitors = displayed_monitors
        self.stats = all_stats
        self.resetSettings()

    def _get_displayed_stats(self):
        return [type(monitor.stat) for monitor in self.monitors]

    def _handle_category(self, item, role):
        if role == self.TypeRole:
            return 'category'
        if role == self.NameRole:
            return item

    def _handle_stat(self, item, role):
        if role == self.TypeRole:
            return 'stat'
        if role == self.NameRole:
            return item.name
        if role == self.TagRole:
            return item.tag
        if role == self.CheckedRole:
            return item in self._get_displayed_stats()

    @Slot(str, bool)
    def toggleStat(self, tag, checked):
        stat = backend.get_stats_from_tags(tag)
        if checked:
            self.added_stats.add(stat)

            try:
                self.removed_stats.remove(stat)
            except KeyError:
                pass
        else:
            self.removed_stats.add(stat)

            try:
                self.added_stats.remove(stat)
            except KeyError:
                pass

    @Slot()
    def resetSettings(self):
        self.removed_stats = set()
        self.added_stats = set()

    @Slot()
    def submitSettings(self):
        displayed_stats = set(self._get_displayed_stats())
        displayed_stats -= self.removed_stats
        displayed_stats |= self.added_stats

        self.submitted.emit(list(displayed_stats))

    def rowCount(self, parent=QModelIndex()):
        return len(self.stats)

    def data(self, index, role=Qt.DisplayRole):
        try:
            item = self.stats[index.row()]
        except IndexError:
            return

        inherits_stat = False
        try:
            inherits_stat = issubclass(item, backend.Stat)
        except TypeError:
            pass

        if inherits_stat:
            return self._handle_stat(item, role)
        else:
            return self._handle_category(item, role)

    def roleNames(self):
        return self._roles


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

        self.settings_model = SettingsModel(self.monitors)
        self.settings_model.submitted.connect(self.adjust_monitors)

    def adjust_monitors(self, stats):
        displayed_stats = []
        removed_monitors = []

        for monitor in self.monitors.copy():
            if type(monitor.stat) in stats:
                displayed_stats.append(type(monitor.stat))
            else:
                removed_monitors.append(monitor)
                self.monitor_model.removeMonitor(monitor)

        new_stats = list(set(stats) - set(displayed_stats))
        new_stats = sorted(new_stats, key=lambda stat: stat.tag)

        for stat in new_stats:
            monitor = NativeMonitor(stat, color=self.next_color(),
                                    **self.monitor_params)
            self.monitor_model.addMonitor(monitor)

        if logging.getLogger().isEnabledFor(logging.INFO):
            displayed = [stat.tag for stat in displayed_stats] or 'No Monitors'
            new = [stat.tag for stat in new_stats] or 'No Monitors'
            removed = [monitor.stat.tag for monitor in removed_monitors] or \
                'No Monitors'

            logging.info('Adjusted monitors')
            logging.info(f'{displayed} were already displayed')
            logging.info(f'{new} were added')
            logging.info(f'{removed} were removed')

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

        self.adjust_monitors(self.stats)

        view = QQuickView()
        view.setResizeMode(QQuickView.SizeRootObjectToView)

        root_context = view.rootContext()
        root_context.setContextProperty('monitorModel', self.monitor_model)
        root_context.setContextProperty('settingsModel', self.settings_model)

        qml_file = os.path.join(os.path.dirname(__file__), 'qml', 'view.qml')
        view.setSource(QUrl.fromLocalFile(os.path.abspath(qml_file)))

        if view.status() == QQuickView.Error:
            sys.exit(-1)

        view.show()
        self.qapp.exec_()
        del view

    def paint():
        pass
