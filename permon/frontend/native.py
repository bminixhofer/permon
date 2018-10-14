import sys
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt, Signal
from PySide2.QtCharts import QtCharts
import PySide2.QtGui as QtGui
from permon.frontend import Monitor, MonitorApp, utils
import permon.backend as backend
from permon import config, exceptions
import math


class SettingsWidget(QtWidgets.QWidget):
    accepted = Signal(list)
    cancelled = Signal()

    def __init__(self, parent, stats):
        super(SettingsWidget, self).__init__(parent=parent)
        self.set_stats = stats.copy()

        layout = QtWidgets.QVBoxLayout(self)

        font = QtGui.QFont()
        font.setPixelSize(14)
        font.setBold(True)

        monitor_label = QtWidgets.QLabel('Displayed Monitors')
        monitor_label.setFont(font)

        layout.addWidget(monitor_label)

        model = QtGui.QStandardItemModel()
        font = QtGui.QFont()
        font.setBold(True)

        all_stats = backend.get_all_stats()

        category_map = dict()
        for root_tag in set(x.root_tag for x in all_stats):
            item = QtGui.QStandardItem(root_tag)
            item.setFont(font)
            model.appendRow(item)

            category_map[root_tag] = item

        for stat in all_stats:
            item = QtGui.QStandardItem(stat.base_tag)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

            check_state = Qt.Checked if stat in self.set_stats \
                else Qt.Unchecked
            item.setData(check_state, Qt.CheckStateRole)
            item.setData(stat.tag)
            category_map[stat.root_tag].appendRow(item)

        model.itemChanged.connect(self._check_monitor)

        tree = QtWidgets.QTreeView()
        tree.header().hide()
        tree.setModel(model)

        layout.addWidget(tree)

        continue_widget = QtWidgets.QWidget()
        continue_layout = QtWidgets.QHBoxLayout(continue_widget)

        cancel_button = QtWidgets.QPushButton('Cancel')
        accept_button = QtWidgets.QPushButton('Accept')

        cancel_button.clicked.connect(self._cancel)
        accept_button.clicked.connect(self._accept)

        continue_layout.addWidget(cancel_button)
        continue_layout.addWidget(accept_button)

        layout.addWidget(continue_widget)

    def open(self, stats):
        self.set_stats = stats.copy()

    def _check_monitor(self, item):
        state = item.checkState()
        is_selected = state == Qt.Checked

        stat = backend.get_stats_from_tags(item.data())
        if is_selected:
            self.set_stats.append(stat)
        else:
            self.set_stats.remove(stat)

    def _accept(self):
        self.accepted.emit(self.set_stats)

    def _cancel(self):
        self.cancelled.emit()


class NativeMonitor(Monitor):
    def _create_right_axis(self):
        top_axis = QtCharts.QCategoryAxis()
        top_axis.setGridLineVisible(False)

        font = QtGui.QFont()
        font.setPixelSize(8)
        top_axis.setLabelsFont(font)
        top_axis.setLinePen(self.line_pen)

        if not self.stat.has_contributor_breakdown:
            top_axis.setLineVisible(False)

        self.widget.chart.addAxis(top_axis, Qt.AlignRight)
        self.line_series.attachAxis(top_axis)

        self.top_axis = top_axis

    def _create_line_series(self):
        # a QValueAxis has tick labels per default
        # so we use a QCategoryAxis
        axisX = QtCharts.QCategoryAxis()
        axisX.setRange(0, self.buffer_size)

        # create series
        series = QtCharts.QLineSeries()
        pen = QtGui.QPen(QtGui.QColor(self.color), self.thickness)
        series.setPen(pen)

        self.widget.chart.addSeries(series)
        self.widget.chart.setAxisX(axisX, series)
        self.widget.chart.setAxisY(self.widget.axisY, series)

        self.buffer = [QtCore.QPointF(x, 0) for x in range(self.buffer_size)]
        series.append(self.buffer)

        self.line_pen = pen
        self.line_series = series

    def __init__(self, stat, buffer_size, fps, color,
                 app, fontsize, thickness):
        super(NativeMonitor, self).__init__(stat, buffer_size,
                                            fps, color, app)
        self.fontsize = fontsize
        self.thickness = thickness
        self.widget = QtWidgets.QWidget()

        # the widget consists of a title and the chart
        # we have to create a vertical layout in order to
        # position the title above the chart
        layout = QtWidgets.QVBoxLayout(self.widget)
        layout.setMargin(0)

        self.widget.chart = QtCharts.QChart()

        # use a QCategoryAxis again for more customizability
        self.widget.axisY = QtCharts.QCategoryAxis()
        self.widget.axisY.setLabelsPosition(
            QtCharts.QCategoryAxis.AxisLabelsPositionOnValue
        )

        self._create_line_series()
        self._create_right_axis()

        self._set_yrange(self.stat.minimum or 0, self.stat.maximum or 0)

        self.widget.chart.legend().hide()
        self.widget.chart.layout().setContentsMargins(0, 0, 0, 0)

        # create the title label and add it to the layout
        layout.addWidget(self._create_header(fontsize))

        # create a view for the chart and add it to the layout
        self.widget.chartView = QtCharts.QChartView(self.widget.chart)
        self.widget.chartView.setRenderHint(QtGui.QPainter.Antialiasing)
        layout.addWidget(self.widget.chartView)

        # run an update every 1 / fps seconds
        timer = QtCore.QTimer(self.widget)
        timer.start(1000 / fps)
        timer.timeout.connect(self.update)

    def update(self):
        # every frame, we remove the last point of the history and
        # append a new measurement to the end
        if self.stat.has_contributor_breakdown:
            value, contributors = self.stat.get_stat()
        else:
            value = self.stat.get_stat()
            contributors = {}

        for s in self.top_axis.categoriesLabels():
                self.top_axis.remove(s)

        agg = 0
        for i, x in enumerate(contributors):
            label = utils.format_bar_label(x[0])

            agg += x[1]
            self.top_axis.append(u'\u00A0' * 2 + label, agg)
        self.top_axis.append(u'\u00A0' * 40, math.inf)

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

    def _set_yrange(self, minimum, maximum, n_labels=5):
        axis = self.widget.axisY
        if minimum == axis.min() and maximum == axis.max():
            return

        axis.setRange(minimum, maximum)
        self.top_axis.setRange(minimum, maximum)

        for s in axis.categoriesLabels():
            axis.remove(s)

        axis_values = [minimum + ((maximum - minimum) / (n_labels - 1)) * i
                       for i in range(n_labels)]
        axis_labels = utils.format_labels(axis_values)
        for value, label in zip(axis_values, axis_labels):
            # qt strips spaces from labels, to make them have the same size
            # we have to pad them with non-breaking spaces (U+00A0)
            axis.append(label.rjust(10, u'\u00A0'), value)

    def _create_header(self, fontsize):
        font = QtGui.QFont()
        font.setPixelSize(fontsize)
        font.setBold(True)

        title_label = QtWidgets.QLabel(self.stat.name)
        title_label.setFont(font)

        return title_label


class NativeApp(MonitorApp):
    # QApplication is a global singleton. It can only ever be instantiated once
    qapp = None

    def __init__(self, stats, colors, buffer_size, fps, fontsize=14,
                 line_thickness=2):
        super(NativeApp, self).__init__(stats, colors, buffer_size, fps)

        self.monitor_params = {
            'buffer_size': buffer_size,
            'fps': fps,
            'app': self,
            'thickness': line_thickness,
            'fontsize': fontsize
        }

    def initialize(self):
        if not self.qapp:
            NativeApp.qapp = QtWidgets.QApplication(sys.argv)

        self.window = QtWidgets.QMainWindow()
        self._settings_tags = []

        # make the background white (the default is some ugly gray)
        palette = self.qapp.palette()
        palette.setColor(QtGui.QPalette.Window, Qt.white)
        self.qapp.setPalette(palette)

        # resize the app to take up 3 / 4 of the vertical space
        # this is relatively arbitrary, but 3 / 4 is reasonably large
        availableGeometry = self.qapp.desktop().availableGeometry(self.window)
        size = availableGeometry.height() * 3 / 4
        self.window.resize(size, size)

        # create the main widget and add monitors to it
        self._main = QtWidgets.QStackedWidget()
        self._settings_page = SettingsWidget(self._main, self.stats)

        def accept_settings(stats):
            if len(stats) == 0:
                raise exceptions.NoStatError()

            self.stats = stats

            config.set_config({
                'stats': [stat.tag for stat in stats]
            })

            self.adjust_monitors()
            self._main.setCurrentWidget(self._monitor_page)

        def cancel_settings():
            self._main.setCurrentWidget(self._monitor_page)

        self._settings_page.accepted.connect(accept_settings)
        self._settings_page.cancelled.connect(cancel_settings)

        self._monitor_page = self._create_monitor_page()
        self.adjust_monitors()

        self._main.addWidget(self._monitor_page)
        self._main.addWidget(self._settings_page)

        self.window.setCentralWidget(self._main)
        self.window.show()
        self.qapp.exec_()

        # when done executing (window is closed by user), delete the monitors
        del self.monitors

    def paint(self):
        pass

    def _create_monitor_page(self):
        page_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page_widget)

        # add button for switching to settings page
        settings_button = QtWidgets.QPushButton('Settings')

        def open_settings():
            self._settings_page.open(self.stats)
            self._main.setCurrentWidget(self._settings_page)

        settings_button.clicked.connect(open_settings)
        layout.addWidget(settings_button)

        self.monitors = []
        return page_widget

    def adjust_monitors(self):
        displayed_stats = []
        removed_monitors = []
        for monitor in self.monitors:
            if monitor.stat in self.stats:
                displayed_stats.append(monitor.stat)
            else:
                removed_monitors.append(monitor)

                layout = monitor.widget.layout()
                for i in reversed(range(layout.count())):
                    layout.itemAt(i).widget().setParent(None)
                self._monitor_page.layout().removeWidget(monitor.widget)

        for monitor in removed_monitors:
            self.monitors.remove(monitor)

        new_stats = list(set(self.stats) - set(displayed_stats))
        for stat in new_stats:
            monitor = NativeMonitor(stat, color=self.next_color(),
                                    **self.monitor_params)
            self.monitors.append(monitor)
            self._monitor_page.layout().addWidget(monitor.widget)

        # keep all charts equally large
        for i in range(self._monitor_page.layout().count()):
            self._monitor_page.layout().setStretch(i, 1)
