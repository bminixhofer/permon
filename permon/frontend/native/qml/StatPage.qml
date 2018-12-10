import QtQuick 2.11
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.11
import QtGraphicalEffects 1.0
import QtCharts 2.2

Page {
    property int labelCount: 5
    property int leftMargin: 8
    property int rightMargin: 20
    property alias errorMessage: errorMessage.message
    signal settingsButtonClicked

    id: statPage
    header: ToolBar {
        height: 50

        Rectangle {
            id: headerRectangle
            anchors.fill: parent
            color: "#333"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 3
                anchors.rightMargin: 3
                spacing: 5

                Label {
                    font.pixelSize: 26
                    font.bold: true
                    color: "white"
                    text: "permon"
                }

                Label {
                    Layout.fillWidth: true
                    property string message;

                    id: errorMessage
                    font.family: "Roboto Mono"
                    horizontalAlignment: Text.AlignRight
                    color: "#ed5565"
                    text: message ? "Error: " + message : ""
                }

                Button {
                    background: Rectangle {
                        color: "transparent"
                    }
                    icon.height: parent.height * 0.8
                    icon.width: parent.height * 0.8
                    icon.color: "white"
                    icon.source: "../../assets/settings.svg"

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: statPage.settingsButtonClicked()
                    }
                }
            }
        }

        DropShadow {
            source: headerRectangle
            anchors.fill: source
            color: "black"
            radius: 10.0
            samples: radius * 2
        }
    }

    ListView {
        z: 1
        id: listView
        objectName: "listView"
        model: monitorModel
        anchors.fill: parent
        delegate: ChartView {
            objectName: model.tag
            id: chartView

            antialiasing: true
            legend.visible: false
            width: listView.width
            height: listView.height / listView.count
            margins.top: 30
            margins.right: 0
            margins.bottom: 8
            margins.left: 0

            Label {
                text: model.name
                topPadding: 10
                // the left margin of charts depends on the font size (unfortunately)
                // so the left paddding of the title label also has to depend on the same things as the font size
                leftPadding: valueAxis.labelsFont.pixelSize * 6.4
                font.pixelSize: 22
            }

            ValueAxis {
                id: axisX
                min: 0
                max: model.bufferSize
                visible: false
            }

            CategoryAxis {
                id: valueAxis
                min: model.minimum == null ? -1 : model.minimum
                max: model.maximum == null ? 1 : model.maximum
                labelsPosition: CategoryAxis.AxisLabelsPositionOnValue
                labelsFont.family: "Roboto Mono"
                labelsFont.pixelSize: Math.min(12 / listView.count * listView.height / 250, 16)
                gridVisible: false
                color: "black"
            }

            CategoryAxis {
                id: contributorAxis
                min: valueAxis.min
                max: valueAxis.max
                labelsFont.family: "Roboto Mono"
                labelsFont.pixelSize: Math.min(12 / listView.count * listView.height / 250, 16)
                gridVisible: false
                color: "black"
            }

            LineSeries {
                color: model.color
                width: 3
                id: series
                XYPoint {
                    x: 0
                    y: 0
                }
                axisX: axisX
                axisY: valueAxis
            }

            LineSeries {
                axisYRight: contributorAxis
            }

            MouseArea {
                y: tooltip.y
                height: tooltip.height
                x: chartView.plotArea.x
                width: chartView.plotArea.width
                cursorShape: Qt.PointingHandCursor

                hoverEnabled: true
                onPositionChanged: function(event) {
                    tooltip.x = Math.min(Math.max(x + event.x, tooltip.minimum), tooltip.maximum);
                    timer.refreshTooltip();
                }
                onEntered: {
                    tooltip.visible = true;
                }
                onExited: {
                    tooltip.visible = false;
                }
            }

            Rectangle {
                id: tooltip
                property var minimum: chartView.plotArea.x
                property var maximum: chartView.plotArea.x + chartView.plotArea.width
                property var relativePosition: (x - minimum) / (maximum - minimum)
                property var text: ""

                color: '#333'
                opacity: 0.7
                height: chartView.plotArea.height
                y: chartView.plotArea.y
                width: 2
                visible: false

                Text {
                    x: 5
                    font.family: "Roboto Mono"
                    font.pixelSize: 10
                    text: tooltip.text
                }
            }

            Timer {
                property int timeline: 0
                property bool valueLabelsInitialized: false
                property var values: []
                id: timer
                interval: 1000 / model.fps
                running: true
                repeat: true
                onTriggered: {
                    timeline++;

                    if(model.tag == null) {
                        return;
                    }
                    values.push(model.value);
                    values.shift();
                    series.append(timeline, values[model.bufferSize - 1]);
                    series.remove(0);

                    axisX.min++;
                    axisX.max++;

                    // update tooltip
                    if(tooltip.visible) {
                        refreshTooltip();
                    }

                    // update contributors
                    var contributorCount = contributorAxis.count;
                    for(var i = 0; i < contributorCount; i++) {
                        contributorAxis.remove(contributorAxis.categoriesLabels[0]);
                    }

                    var agg = 0;
                    var paddingLeft = '\u00A0';
                    if(model.contributors) {
                        model.contributors.forEach(function(contributor, index) {
                            agg += contributor[1];
                            contributorAxis.append(paddingLeft + contributor[0], agg);
                            });
                        contributorAxis.append('<font color="white">' + '\u00A0'.repeat(statPage.rightMargin) + '</font>', contributorAxis.max + 1);
                    }

                    if(model.maximum == null || model.minimum == null) {
                        var dataMax = Math.max.apply(null, values);
                        var dataMin = Math.min.apply(null, values);

                        var rangeisZero = dataMax == dataMin;

                        var minimum = model.minimum;
                        var maximum = model.maximum;

                        if(minimum == null) {
                            if(rangeisZero) {
                                minimum = -1;
                            } else {
                                minimum = dataMin;
                            }
                        }
                        if(maximum == null) {
                            if(rangeisZero) {
                                maximum = 1;
                            } else {
                                maximum = dataMax;
                            }
                        }
                        if(minimum != valueAxis.min || maximum != valueAxis.max) {
                            valueAxis.min = minimum;
                            valueAxis.max = maximum;
                            refreshLabels(minimum, maximum);
                        }
                    }
                }
                function refreshLabels(minimum, maximum) {
                    var distanceBetweenLabels = (maximum - minimum) / (statPage.labelCount - 1);
                    var axisValues = Array.apply(null, Array(statPage.labelCount)).map(function (_, i) {
                        return minimum + distanceBetweenLabels * i;
                    });
                    var axisLabels = formatLabels(axisValues);
                    for(var i = 0; i < statPage.labelCount; i++) {
                        valueAxis.remove(valueAxis.categoriesLabels[0]);
                    }
                    for(var i = 0; i < statPage.labelCount; i++) {
                        valueAxis.append(axisLabels[i], axisValues[i]);
                    }
                }
                function formatValue(x, maxValue) {
                    var result;
                    if(maxValue <= 10) {
                        result = x.toFixed(3);
                    } else if(maxValue <= 100) {
                        result = x.toFixed(2);
                    } else if(maxValue <= 1000) {
                        result = x.toFixed(1);
                    } else if(maxValue <= 10000) {
                        result = Math.floor(x / 50) * 50;
                    } else if(maxValue > 10000) {
                        result = Math.floor(x / 50) * 50;
                    }
                    return result ? result.toString() : "";
                }
                function formatLabels(axisValues) {
                    var maxValue = Math.abs(Math.max.apply(null, axisValues));

                    return axisValues.map(function(x) {
                        var result = formatValue(x, maxValue);
                        var paddingLeft = '\u00A0'.repeat(Math.max(statPage.leftMargin - result.length, 0));
                        var paddingRight = '\u00A0';

                        return paddingLeft + result + paddingRight;
                    });
                }
                function refreshTooltip() {
                    var hoveredValue = values[Math.floor(tooltip.relativePosition * (model.bufferSize - 1))];
                    tooltip.text = formatValue(hoveredValue, hoveredValue);
                }
                Component.onCompleted: {
                    for(var i = 0; i < model.bufferSize; i++) {
                        values.push(0);
                        series.append(timeline++, 0);
                    }
                    onTriggered();
                    if(valueAxis.min != null && valueAxis.max != null) {
                        refreshLabels(valueAxis.min, valueAxis.max);
                    }
                }
            }
        }
    }
}