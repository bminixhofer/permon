import sys
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt
from PySide2.QtCharts import QtCharts
import PySide2.QtGui as QtGui
from permon.frontend import Monitor, MonitorApp, utils
import permon.backend as backend


class NativeMonitor(Monitor):
    def __init__(self, stat_func, title, full_tag, buffer_size, fps, color,
                 app, fontsize, thickness, minimum=None, maximum=None):
        super(NativeMonitor, self).__init__(stat_func, title, buffer_size,
                                            fps, color, app, minimum=minimum,
                                            maximum=maximum)
        self.widget = QtWidgets.QWidget()
        self.full_tag = full_tag

        # the widget consists of a title and the chart
        # we have to create a vertical layout in order to
        # position the title above the chart
        layout = QtWidgets.QVBoxLayout(self.widget)
        layout.setMargin(0)

        self.widget.series = QtCharts.QLineSeries()
        pen = QtGui.QPen(QtGui.QColor(self.color), thickness)
        self.widget.series.setPen(pen)

        self.widget.chart = QtCharts.QChart()
        self.widget.chart.addSeries(self.widget.series)

        # a QValueAxis has tick labels per default
        # so we use a QCategoryAxis
        self.widget.axisX = QtCharts.QCategoryAxis()
        self.widget.axisX.setRange(0, buffer_size)

        # use a QCategoryAxis again for more customizability
        self.widget.axisY = QtCharts.QCategoryAxis()
        self.widget.axisY.setLabelsPosition(
            QtCharts.QCategoryAxis.AxisLabelsPositionOnValue
            )
        self._set_yrange(self.minimum or 0, self.maximum or 0)

        self.widget.chart.setAxisX(self.widget.axisX, self.widget.series)
        self.widget.chart.setAxisY(self.widget.axisY, self.widget.series)
        self.widget.chart.legend().hide()
        self.widget.chart.layout().setContentsMargins(0, 0, 0, 0)

        # create the title label and add it to the layout
        layout.addWidget(self._create_header(fontsize))

        # create a view for the chart and add it to the layout
        self.widget.chartView = QtCharts.QChartView(self.widget.chart)
        self.widget.chartView.setRenderHint(QtGui.QPainter.Antialiasing)
        layout.addWidget(self.widget.chartView)

        self.buffer = [QtCore.QPointF(x, 0) for x in range(buffer_size)]
        self.widget.series.append(self.buffer)

        # run an update every 1 / fps seconds
        timer = QtCore.QTimer(self.widget)
        timer.start(1000 / fps)
        timer.timeout.connect(self.update)

    def update(self):
        # every frame, we remove the last point of the history and
        # append a new measurement to the end
        new_point = QtCore.QPointF(self.buffer_size, self.stat_func())
        self.buffer.append(new_point)
        del self.buffer[0]

        # now that the buffer moved one to the left, we have to
        # reposition the x values
        for i in range(self.buffer_size):
            self.buffer[i].setX(i)

        self.widget.series.replace(self.buffer)

        # if minimum or maximum is unknown, we have to adjust the axis limits
        if self.minimum is None or self.maximum is None:
            buffer_values = [point.y() for point in self.buffer]

            # if we dont know the min or max and they cant be determined by
            # the history, we have to set some defaults (e. g. -1 and 1)
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

    def _create_header(self, fontsize):
        font = QtGui.QFont()
        font.setPixelSize(fontsize)
        font.setBold(True)

        title_label = QtWidgets.QLabel(self.title)
        title_label.setFont(font)

        return title_label


class NativeApp(MonitorApp):
    # QApplication is a global singleton. It can only ever be instantiated once
    qapp = None

    def __init__(self, tags, colors, buffer_size, fps, fontsize=14,
                 line_thickness=3):
        super(NativeApp, self).__init__(tags, colors, buffer_size, fps)

        self.line_thickness = line_thickness
        self.fontsize = fontsize

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
        self._monitor_page = self._create_monitor_page()
        self._settings_page = self._create_settings_page()

        self._main.addWidget(self._monitor_page)
        self._main.addWidget(self._settings_page)

        self.window.setCentralWidget(self._main)
        self.window.show()
        self.qapp.exec_()

    def paint(self):
        pass

    def _create_monitor_page(self):
        page_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page_widget)

        # add button for switching to settings page
        settings_button = QtWidgets.QPushButton('Settings')

        def set_settings_page():
            self._settings_tags = self.tags.copy()
            self._main.setCurrentWidget(self._settings_page)
        settings_button.clicked.connect(set_settings_page)

        layout.addWidget(settings_button)

        # add monitors
        for i, stat in enumerate(self.stats):
            monitor = NativeMonitor(stat.get_stat, stat.name,
                                    stat.get_full_tag(),
                                    buffer_size=self.buffer_size,
                                    fps=self.fps,
                                    color=self.next_color(),
                                    app=self,
                                    fontsize=self.fontsize,
                                    thickness=self.line_thickness,
                                    minimum=stat.minimum,
                                    maximum=stat.maximum)
            self.monitors.append(monitor)
            layout.addWidget(monitor.widget)
        return page_widget

    def adjust_monitors(self):
        displayed_monitor_tags = []
        removed_monitors = []
        for monitor in self.monitors:
            if monitor.full_tag in self.tags:
                displayed_monitor_tags.append(monitor.full_tag)
            else:
                removed_monitors.append(monitor)

                layout = monitor.widget.layout()
                for i in reversed(range(layout.count())):
                    layout.itemAt(i).widget().setParent(None)
                self._monitor_page.layout().removeWidget(monitor.widget)

        for monitor in removed_monitors:
            self.monitors.remove(monitor)

        new_tags = list(set(self.tags) - set(displayed_monitor_tags))
        for stat in backend.get_available_stats():
            if stat.get_full_tag() in new_tags:
                instance = stat()
                monitor = NativeMonitor(instance.get_stat, instance.name,
                                        instance.get_full_tag(),
                                        buffer_size=self.buffer_size,
                                        fps=self.fps,
                                        color=self.next_color(),
                                        app=self,
                                        fontsize=self.fontsize,
                                        thickness=self.line_thickness,
                                        minimum=instance.minimum,
                                        maximum=instance.maximum)
                self.monitors.append(monitor)
                self._monitor_page.layout().addWidget(monitor.widget)

    def _create_settings_page(self):
        page_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page_widget)

        font = QtGui.QFont()
        font.setPixelSize(self.fontsize)
        font.setBold(True)

        monitor_label = QtWidgets.QLabel('Displayed Monitors')
        monitor_label.setFont(font)

        layout.addWidget(monitor_label)

        model = QtGui.QStandardItemModel()
        font = QtGui.QFont()
        font.setBold(True)

        stats = backend.get_available_stats()
        stats = [x.get_full_tag().split('.')[:2] for x in stats]

        category_map = dict()
        for category in set(x[0] for x in stats):
            item = QtGui.QStandardItem(category)
            item.setFont(font)
            model.appendRow(item)

            category_map[category] = item

        for category, base in stats:
            item = QtGui.QStandardItem(base)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

            full_tag = f'{category}.{base}'
            check_state = Qt.Checked if full_tag in self.tags \
                else Qt.Unchecked
            item.setData(check_state, Qt.CheckStateRole)
            item.setData(full_tag)
            category_map[category].appendRow(item)

        def check_monitor(item):
            state = item.checkState()
            is_selected = state == Qt.Checked

            full_tag = item.data()
            if is_selected:
                self._settings_tags.append(full_tag)
            else:
                self._settings_tags.remove(full_tag)

        model.itemChanged.connect(check_monitor)

        tree = QtWidgets.QTreeView()
        tree.header().hide()
        tree.setModel(model)

        layout.addWidget(tree)

        continue_widget = QtWidgets.QWidget()
        continue_layout = QtWidgets.QHBoxLayout(continue_widget)

        cancel_button = QtWidgets.QPushButton('Cancel')
        accept_button = QtWidgets.QPushButton('Accept')

        def cancel():
            self._main.setCurrentWidget(self._monitor_page)

        def accept():
            self.tags = self._settings_tags
            self.adjust_monitors()
            self._main.setCurrentWidget(self._monitor_page)

        cancel_button.clicked.connect(cancel)
        accept_button.clicked.connect(accept)

        continue_layout.addWidget(cancel_button)
        continue_layout.addWidget(accept_button)

        layout.addWidget(continue_widget)

        return page_widget
