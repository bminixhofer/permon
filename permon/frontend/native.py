import sys
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt
from PySide2.QtCharts import QtCharts
from PySide2.QtGui import QPainter, QPalette, QFont, QPen, QColor
from permon.classes import Monitor, MonitorApp
from permon.frontend import utils


class NativeMonitor(Monitor):
    def __init__(self, stat_func, title, buffer_size, fps, color,
                 minimum=None, maximum=None):
        super(NativeMonitor, self).__init__(stat_func, title, buffer_size,
                                            fps, color, minimum=minimum,
                                            maximum=maximum)
        self.widget = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout(self.widget)
        layout.setMargin(0)

        self.widget.series = QtCharts.QLineSeries()
        pen = QPen(self.color, 3)
        self.widget.series.setPen(pen)

        self.widget.chart = QtCharts.QChart()
        self.widget.chart.addSeries(self.widget.series)

        self.widget.axisX = QtCharts.QCategoryAxis()
        self.widget.axisX.setRange(0, buffer_size)

        self.widget.axisY = QtCharts.QCategoryAxis()
        self.widget.axisY.setLabelsPosition(
            QtCharts.QCategoryAxis.AxisLabelsPositionOnValue
            )
        self._set_yrange(self.minimum or 0, self.maximum or 0)

        self.widget.chart.setAxisX(self.widget.axisX, self.widget.series)
        self.widget.chart.setAxisY(self.widget.axisY, self.widget.series)
        self.widget.chart.legend().hide()
        self.widget.chart.layout().setContentsMargins(0, 0, 0, 0)

        titleFont = QFont()
        titleFont.setPixelSize(14)
        titleFont.setBold(True)

        titleLabel = QtWidgets.QLabel(self.title)
        titleLabel.setFont(titleFont)
        layout.addWidget(titleLabel)

        self.widget.chartView = QtCharts.QChartView(self.widget.chart)
        self.widget.chartView.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.widget.chartView)

        self.buffer = [QtCore.QPointF(x, 0) for x in range(buffer_size)]
        self.widget.series.append(self.buffer)

        timer = QtCore.QTimer(self.widget)
        timer.start(1000 / fps)
        timer.timeout.connect(self.update)

    def update(self):
        new_point = QtCore.QPointF(self.buffer_size, self.stat_func())
        self.buffer.append(new_point)
        del self.buffer[0]

        for i in range(self.buffer_size):
            self.buffer[i].setX(i)

        self.widget.series.replace(self.buffer)

        if self.minimum is None or self.maximum is None:
            buffer_values = [point.y() for point in self.buffer]

            range_is_zero = max(buffer_values) == min(buffer_values)
            minimum = self.minimum
            maximum = self.maximum
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

    def _set_yrange(self, minimum, maximum, n_labels=4):
        axis = self.widget.axisY
        if minimum == axis.min() and maximum == axis.max():
            return

        axis.setRange(minimum, maximum)

        for s in axis.categoriesLabels():
            axis.remove(s)

        axis_values = [minimum + ((maximum - minimum) / (n_labels - 1)) * i
                       for i in range(n_labels)]
        axis_labels = utils.format_labels(axis_values)
        for value, label in zip(axis_values, axis_labels):
            # qt strips spaces from labels, to make them have the same size
            # we have to pad them with non-breaking spaces (U+00A0)
            axis.append(label.rjust(10, u'\u00A0'), value)


class NativeApp(MonitorApp):
    def __init__(self, stat_funcs, colors, buffer_size, fps):
        super(NativeApp, self).__init__(stat_funcs, colors, buffer_size, fps)

        self.qapp = QtWidgets.QApplication(sys.argv)
        self.window = QtWidgets.QMainWindow()

        palette = self.qapp.palette()
        palette.setColor(QPalette.Window, Qt.white)
        self.qapp.setPalette(palette)

        availableGeometry = self.qapp.desktop().availableGeometry(self.window)
        size = availableGeometry.height() * 3 / 4
        self.window.resize(size, size)

    def initialize(self):
        self.colors = ['#ed5565', '#ffce54', '#48cfad', '#sd9cec', '#ec87c0',
                       '#fc6e51', '#a0d468', '#4fc1e9', '#ac92ec']
        self.colors = [QColor(x) for x in self.colors]
        self._main = QtWidgets.QWidget()
        self.window.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        # graph_selector = GraphSelector()
        # layout.addWidget(graph_selector)

        for i, (func, info) in enumerate(self.stat_funcs):
            monitor = NativeMonitor(func, info['title'],
                                    buffer_size=self.buffer_size,
                                    fps=self.fps,
                                    color=self.colors[i],
                                    minimum=info['minimum'],
                                    maximum=info['maximum'])
            self.monitors.append(monitor)
            layout.addWidget(monitor.widget)
        self.window.show()
        self.qapp.exec_()

    def paint(self):
        pass
