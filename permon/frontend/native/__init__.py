import sys
import os
import logging
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QUrl, QVariant, QAbstractListModel, QModelIndex
import PyQt5.QtGui as QtGui
from PyQt5.QtQuick import QQuickView
from permon.frontend import Monitor, MonitorApp, utils


class NativeMonitor(Monitor):
    def __init__(self, stat, buffer_size, fps, color,
                 app, thickness):
        super(NativeMonitor, self).__init__(stat, buffer_size,
                                            fps, color, app)
        self.value = 0
        self.contributors = []

    def _set_yrange(self, minimum, maximum, n_labels=5):
        axis = self.left_axis
        if minimum == axis.min() and maximum == axis.max():
            return

        axis.setRange(minimum, maximum)
        self.right_axis.setRange(minimum, maximum)

        for s in axis.categoriesLabels():
            axis.remove(s)

        axis_values = [minimum + ((maximum - minimum) / (n_labels - 1)) * i
                       for i in range(n_labels)]
        axis_labels = utils.format_labels(axis_values)
        for value, label in zip(axis_values, axis_labels):
            # qt strips spaces from labels, to make them have the same size
            # we have to pad them with non-breaking spaces (U+00A0)
            axis.append(label, value)

    def adjust_fonts(self, app_height, app_width, n_monitors):
        font = QtGui.QFont(NativeApp.fonts['axis_label'])
        real_fontsize = font.pixelSize() / n_monitors * app_height / 250
        real_fontsize = min(real_fontsize, 16)
        font.setPixelSize(real_fontsize)

        self.right_axis.setLabelsFont(font)
        self.left_axis.setLabelsFont(font)

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

        self._monitors = []

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

    def addMonitor(self, monitor, view):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._monitors.append(monitor)
        self.endInsertRows()

    def rowCount(self, parent=QModelIndex()):
        return len(self._monitors)

    def data(self, index, role=Qt.DisplayRole):
        try:
            monitor = self._monitors[index.row()]
        except IndexError:
            return QVariant()

        key = self._roles[role].decode()
        if key in self.exposed_properties:
            return self.exposed_properties[key](monitor)

        return QVariant()

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

    def initialize(self):
        if self.qapp is None:
            self.qapp = QtWidgets.QApplication(sys.argv)

            font_path = self.get_asset_path('Raleway-Regular.ttf')
            font_db = QtGui.QFontDatabase()
            font_id = font_db.addApplicationFont(font_path)
            if font_id == -1:
                logging.warn('Could not load custom font')

            font = QtGui.QFont('Raleway')
            self.qapp.setFont(font)

        view = QQuickView()
        view.setResizeMode(QQuickView.SizeRootObjectToView)

        model = MonitorModel()
        root_context = view.rootContext()
        root_context.setContextProperty('monitorModel', model)

        qml_file = os.path.join(os.path.dirname(__file__), 'view.qml')
        view.setSource(QUrl.fromLocalFile(os.path.abspath(qml_file)))

        if view.status() == QQuickView.Error:
            sys.exit(-1)

        for stat in self.stats:
            monitor = NativeMonitor(stat, color=self.next_color(),
                                    **self.monitor_params)
            model.addMonitor(monitor, view)
            self.monitors.append(monitor)

        view.show()
        self.qapp.exec_()
        del view

    def paint():
        pass