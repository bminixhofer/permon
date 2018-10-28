import sys
import os
import logging
import math
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QUrl, QVariant, QAbstractListModel, QModelIndex
import PyQt5.QtChart as QtCharts
import PyQt5.QtGui as QtGui
from PyQt5.QtQuick import QQuickView
from permon.frontend import Monitor, MonitorApp, utils


class NativeMonitor(Monitor):
    def __init__(self, stat, buffer_size, fps, color,
                 app, thickness):
        super(NativeMonitor, self).__init__(stat, buffer_size,
                                            fps, color, app)
        # self.thickness = thickness
        # self.widget = QtWidgets.QWidget()

        # # the widget consists of a title and the chart
        # # we have to create a vertical layout in order to
        # # position the title above the chart
        # layout = QtWidgets.QVBoxLayout(self.widget)
        # layout.setMargin(0)

        # self.widget.chart = QtCharts.QChart()

        # self._create_line_series()
        # self._create_right_axis()

        # self._set_yrange(self.stat.minimum or 0, self.stat.maximum or 0)

        # self.widget.chart.legend().hide()
        # self.widget.chart.layout().setContentsMargins(0, 0, 0, 0)

        # # create the title label and add it to the layout
        # layout.addWidget(self._create_header())

        # # create a view for the chart and add it to the layout
        # self.widget.chartView = QtCharts.QChartView(self.widget.chart)
        # self.widget.chartView.setContentsMargins(0, 0, 0, 0)
        # self.widget.chartView.setRenderHint(QtGui.QPainter.Antialiasing)
        # layout.addWidget(self.widget.chartView)

        # run an update every 1 / fps seconds

    def _create_right_axis(self):
        axisY = QtCharts.QCategoryAxis()
        axisY.setGridLineVisible(False)
        axisY.setLinePen(self.line_pen)

        if not self.stat.has_contributor_breakdown:
            axisY.setLineVisible(False)

        self.widget.chart.addAxis(axisY, Qt.AlignRight)
        self.line_series.attachAxis(axisY)

        self.right_axis = axisY

    def _create_line_series(self):
        # a QValueAxis has tick labels per default
        # so we use a QCategoryAxis
        axisX = QtCharts.QCategoryAxis()
        axisX.setRange(0, self.buffer_size)

        # use a QCategoryAxis again for more customizability
        axisY = QtCharts.QCategoryAxis()
        axisY.setLabelsPosition(
            QtCharts.QCategoryAxis.AxisLabelsPositionOnValue
        )

        # create series
        series = QtCharts.QLineSeries()
        pen = QtGui.QPen(QtGui.QColor(self.color), self.thickness)
        series.setPen(pen)

        self.widget.chart.addSeries(series)
        self.widget.chart.setAxisX(axisX, series)
        self.widget.chart.setAxisY(axisY, series)

        self.buffer = [QtCore.QPointF(x, 0) for x in range(self.buffer_size)]
        series.append(self.buffer)

        self.x_axis = axisX
        self.left_axis = axisY
        self.line_pen = pen
        self.line_series = series

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

    def _create_header(self):
        title_label = QtWidgets.QLabel(self.stat.name)
        title_label.setFont(NativeApp.fonts['h2'])

        return title_label

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
            contributors = {}

        for s in self.right_axis.categoriesLabels():
                self.right_axis.remove(s)

        agg = 0
        for i, x in enumerate(contributors):
            label = utils.format_bar_label(x[0])

            agg += x[1]
            self.right_axis.append(u'\u00A0' * 2 + label, agg)
        self.right_axis.append(u'\u00A0' * 40, math.inf)

        new_point = QtCore.QPointF(self.buffer_size, value)
        self.buffer.append(new_point)
        del self.buffer[0]

        # now that the buffer moved one to the left, we have to
        # reposition the x values
        for i in range(self.buffer_size):
            self.buffer[i].setX(i)

        self.line_series.replace(self.buffer)

        # if minimum or maximum is unknown, we have to adjust the axis limits
        if self.stat.minimum is None or self.stat.maximum is None:
            buffer_values = [point.y() for point in self.buffer]

            # if we dont know the min or max and they cant be determined by
            # the history, we have to set some defaults (e. g. -1 and 1)
            range_is_zero = max(buffer_values) == min(buffer_values)
            minimum = self.stat.minimum
            maximum = self.stat.maximum
            if minimum is None:
                if range_is_zero:
                    minimum = -1
                else:
                    minimum = min(buffer_values)
            if maximum is None:
                if range_is_zero:
                    maximum = 1
                else:
                    maximum = max(buffer_values)

            self._set_yrange(minimum, maximum)

    def paint(self):
        pass


class MonitorModel(QAbstractListModel):
    TagRole = Qt.UserRole + 1
    ValueRole = Qt.UserRole + 2
    MinimumRole = Qt.UserRole + 3
    MaximumRole = Qt.UserRole + 4
    BufferSizeRole = Qt.UserRole + 5
    FPSRole = Qt.UserRole + 6
    ColorRole = Qt.UserRole + 7

    _roles = {
        TagRole: b'tag',
        ValueRole: b'value',
        MinimumRole: b'minimum',
        MaximumRole: b'maximum',
        BufferSizeRole: b'bufferSize',
        FPSRole: b'fps'
    }

    def __init__(self, parent=None):
        super(MonitorModel, self).__init__(parent)

        self._monitors = []
        self.exposed_properties = {
            'tag': lambda monitor: monitor.stat.tag,
            'minimum': lambda monitor: monitor.stat.minimum,
            'maximum': lambda monitor: monitor.stat.maximum,
            'fps': lambda monitor: monitor.fps,
            'bufferSize': lambda monitor: monitor.buffer_size,
            'value': lambda monitor: monitor.stat.get_stat()[0],
            'color': lambda monitor: monitor.color,
            'name': lambda monitor: monitor.stat.name
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
        view.rootContext().setContextProperty('monitorModel', model)

        qml_file = os.path.join(os.path.dirname(__file__), 'view.qml')
        view.setSource(QUrl.fromLocalFile(os.path.abspath(qml_file)))

        if view.status() == QQuickView.Error:
            sys.exit(-1)

        model.addMonitor(NativeMonitor(self.stats[0], color=self.next_color(),
                         **self.monitor_params), view)

        view.show()
        self.qapp.exec_()
        del view

    def paint():
        pass
