import sys
import logging
import math
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt, Signal
from PySide2.QtCharts import QtCharts
import PySide2.QtGui as QtGui
from permon.frontend import Monitor, MonitorApp, utils
import permon.backend as backend
from permon import config, exceptions


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
        for root_tag in sorted(set(x.root_tag for x in all_stats)):
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

    def open(self, stats):
        self.set_stats = stats.copy()


class NativeMonitor(Monitor):
    def __init__(self, stat, buffer_size, fps, color,
                 app, thickness):
        super(NativeMonitor, self).__init__(stat, buffer_size,
                                            fps, color, app)
        self.thickness = thickness
        self.widget = QtWidgets.QWidget()

        # the widget consists of a title and the chart
        # we have to create a vertical layout in order to
        # position the title above the chart
        layout = QtWidgets.QVBoxLayout(self.widget)
        layout.setMargin(0)

        self.widget.chart = QtCharts.QChart()

        self._create_line_series()
        self._create_right_axis()

        self._set_yrange(self.stat.minimum or 0, self.stat.maximum or 0)

        self.widget.chart.legend().hide()
        self.widget.chart.layout().setContentsMargins(0, 0, 0, 0)

        # create the title label and add it to the layout
        layout.addWidget(self._create_header())

        # create a view for the chart and add it to the layout
        self.widget.chartView = QtCharts.QChartView(self.widget.chart)
        self.widget.chartView.setContentsMargins(0, 0, 0, 0)
        self.widget.chartView.setRenderHint(QtGui.QPainter.Antialiasing)
        layout.addWidget(self.widget.chartView)

        # run an update every 1 / fps seconds
        timer = QtCore.QTimer(self.widget)
        timer.start(1000 / fps)
        timer.timeout.connect(self.update)

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
        title_label.setFont(NativeApp.fonts['chart_title'])

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

    def _create_monitor_page(self):
        page_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page_widget)

        title_widget = QtWidgets.QWidget()
        title_layout = QtWidgets.QHBoxLayout(title_widget)

        """button for switching to settings page"""
        icon = QtGui.QIcon(self.get_asset_path('settings.svg'))
        settings_size = QtCore.QSize(40, 40)
        settings_button = QtWidgets.QPushButton()
        settings_button.setFlat(True)
        settings_button.setIcon(icon)
        settings_button.setMaximumSize(settings_size)
        settings_button.setIconSize(settings_size)

        def open_settings():
            self._settings_page.open(self.stats)
            self._main.setCurrentWidget(self._settings_page)

        settings_button.clicked.connect(open_settings)
        """"""

        """title label"""
        title_label = QtWidgets.QLabel('permon '
                                       '<font color="#FBB829">Stats</font>')
        title_label.setFont(NativeApp.fonts['app_title'])
        title_layout.addWidget(title_label)
        title_layout.addWidget(settings_button)
        title_layout.setContentsMargins(0, 0, 0, 0)
        """"""

        layout.addWidget(title_widget)
        return page_widget

    def _create_settings_page(self):
        page_widget = SettingsWidget(self._main, self.stats)

        def accept_settings(stats):
            if len(stats) == 0:
                raise exceptions.NoStatError()

            self.stats = stats

            stat_tags = [stat.tag for stat in stats]
            logging.info('Setting tags: ' + str(stat_tags))
            config.set_config({
                'stats': stat_tags
            })

            self.adjust_monitors()
            self._main.setCurrentWidget(self._monitor_page)

        def cancel_settings():
            self._main.setCurrentWidget(self._monitor_page)

        page_widget.accepted.connect(accept_settings)
        page_widget.cancelled.connect(cancel_settings)
        return page_widget

    def _initialize_app(cls):
        NativeApp.qapp = QtWidgets.QApplication(sys.argv)

        # load fonts
        font_path = cls.get_asset_path('Raleway-Light.ttf')
        font_db = QtGui.QFontDatabase()
        font_id = font_db.addApplicationFont(font_path)
        if font_id == -1:
            logging.warn('Could not load custom font')

        NativeApp.fonts = {}

        title_font = QtGui.QFont('Raleway')
        title_font.setPixelSize(32)
        NativeApp.fonts['app_title'] = title_font

        chart_title_font = QtGui.QFont('Raleway')
        chart_title_font.setPixelSize(20)
        NativeApp.fonts['chart_title'] = chart_title_font

        axis_label_font = QtGui.QFont('Raleway')
        # this size will be rescaled by NativeMonitor.adjust_fonts
        axis_label_font.setPixelSize(10)
        NativeApp.fonts['axis_label'] = axis_label_font

    def initialize(self):
        if not self.qapp:
            self._initialize_app()

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

        def resize_event(event):
            QtWidgets.QMainWindow.resizeEvent(self.window, event)
            self.adjust_fonts(event.size().height(), event.size().width())

        self.window.resizeEvent = resize_event

        # create the main widget and add monitors to it
        self._main = QtWidgets.QStackedWidget()

        # create monitor and settings pages
        self._settings_page = self._create_settings_page()
        self._monitor_page = self._create_monitor_page()
        self.adjust_monitors()

        self._main.addWidget(self._monitor_page)
        self._main.addWidget(self._settings_page)

        self.window.setCentralWidget(self._main)
        self.window.show()
        self.qapp.exec_()

        logging.info('Application closing')
        # when done executing (window is closed by user), delete the monitors
        del self.monitors

    def paint(self):
        pass

    def adjust_fonts(self, app_height, app_width):
        n_monitors = len(self.monitors)
        for monitor in self.monitors:
            monitor.adjust_fonts(app_height, app_width, n_monitors)

    def adjust_monitors(self):
        displayed_stats = []
        removed_monitors = []

        for monitor in self.monitors:
            if type(monitor.stat) in self.stats:
                displayed_stats.append(type(monitor.stat))
            else:
                removed_monitors.append(monitor)

                layout = monitor.widget.layout()
                for i in reversed(range(layout.count())):
                    layout.itemAt(i).widget().setParent(None)
                self._monitor_page.layout().removeWidget(monitor.widget)

        for monitor in removed_monitors:
            self.monitors.remove(monitor)

        new_stats = list(set(self.stats) - set(displayed_stats))
        new_stats = sorted(new_stats, key=lambda stat: stat.tag)
        for stat in new_stats:
            monitor = NativeMonitor(stat, color=self.next_color(),
                                    **self.monitor_params)
            self.monitors.append(monitor)
            self._monitor_page.layout().addWidget(monitor.widget)

        # keep all charts equally large
        for i in range(self._monitor_page.layout().count() - 1):
            self._monitor_page.layout().setStretch(i + 1, 1)

        # adjust axis font sizes of all monitors
        availableGeometry = self.qapp.desktop().availableGeometry(self.window)
        self.adjust_fonts(availableGeometry.height(),
                          availableGeometry.width())

        if logging.getLogger().isEnabledFor(logging.INFO):
            displayed = [stat.tag for stat in displayed_stats] or 'No Monitors'
            new = [stat.tag for stat in new_stats] or 'No Monitors'
            removed = [monitor.stat.tag for monitor in removed_monitors] or \
                'No Monitors'

            logging.info('Adjusted monitors')
            logging.info(f'{displayed} were already displayed')
            logging.info(f'{new} were added')
            logging.info(f'{removed} were removed')
