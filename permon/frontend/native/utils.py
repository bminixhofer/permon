import bisect
import json
from PySide2 import QtCore
from PySide2.QtCore import Qt
from permon import exceptions
from permon.backend import Stat


class MonitorModel(QtCore.QAbstractListModel):
    """
    Model to manage communication between QML and Python concerning
    adding and removing of monitors.
    """
    def __init__(self, parent=None):
        super(MonitorModel, self).__init__(parent)

        self.monitors = []

        def get_and_update_value(monitor):
            monitor.update()
            return monitor.value

        # determine which properties of a monitor are exposed to QML
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

        self.beginInsertRows(QtCore.QModelIndex(), new_index, new_index)
        self.monitors.insert(new_index, monitor)
        self.endInsertRows()

    def removeMonitor(self, monitor):
        monitor_index = self.monitors.index(monitor)
        self.beginRemoveRows(QtCore.QModelIndex(), monitor_index,
                             monitor_index)
        del self.monitors[monitor_index]
        self.endRemoveRows()

    def rowCount(self, parent=QtCore.QModelIndex()):
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


class SettingsModel(QtCore.QObject):
    """
    Model to manage communication between QML and Python concerning
    changing settings.
    """
    statAdded = QtCore.Signal(Stat)
    statRemoved = QtCore.Signal(Stat)

    def __init__(self, app):
        super(SettingsModel, self).__init__()
        self.app = app

    @QtCore.Slot(int, str, result=str)
    def addStat(self, index, settings_str):
        settings = json.loads(settings_str)
        stat = self.app.get_not_displayed_stats()[index]
        stat.set_settings(settings)

        try:
            stat.check_availability()
        except exceptions.StatNotAvailableError as e:
            return str(e)

        self.statAdded.emit(stat)

    @QtCore.Slot(int)
    def removeStat(self, index):
        stat = self.app.get_displayed_stats()[index]
        self.statRemoved.emit(stat)

    @QtCore.Slot(int, result=str)
    def getSettings(self, index):
        """Get the current settings for the stat at index `index`."""
        stat = self.app.get_not_displayed_stats()[index]
        settings_list = [{
            'name': key,
            'defaultValue': value
        } for key, value in stat.default_settings.items()]

        return json.dumps(settings_list)

    @QtCore.Slot(bool, result=str)
    def getStats(self, displayed):
        """
        If `displayed` is true, get all displayed stat classes.
        Otherwise, get all stat classes that are not displayed.
        """
        stats = self.app.get_displayed_stats() if displayed else \
            self.app.get_not_displayed_stats()
        return json.dumps([stat.name for stat in stats])
