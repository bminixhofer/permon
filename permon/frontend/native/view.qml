import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.11
import QtGraphicalEffects 1.0
import QtCharts 2.2

StackView {
    height: 500
    width: 500

    initialItem: Page {
        id: monitorPage
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
                        font.pixelSize: 26
                        color: "white"
                        text: "Stats"
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    Button {
                        background: Rectangle {
                            color: "transparent"
                        }
                        icon.height: parent.height * 0.8
                        icon.width: parent.height * 0.8
                        icon.color: "white"
                        icon.source: "../assets/settings.svg"
                    }
                }
            }

            DropShadow {
                source: headerRectangle
                anchors.fill: source
                color: "black"
                radius: 10.0
                samples: radius
            }
        }

        ListView {
            id: listView
            objectName: "listView"
            model: monitorModel
            anchors.fill: parent
            delegate: ChartView {
                objectName: model.tag

                antialiasing: true
                legend.visible: false
                width: listView.width
                height: listView.height / listView.count
                margins.top: 30
                margins.right: 0
                margins.bottom: 0
                margins.left: 5

                Label {
                    text: model.name
                    topPadding: 15
                    leftPadding: 60
                    font.pixelSize: 22
                }

                ValueAxis {
                    id: axisX
                    min: 0
                    max: model.bufferSize
                    visible: false
                }

                ValueAxis {
                    id: axisY
                    min: model.minimum
                    max: model.maximum
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
                    axisY: axisY
                }

                Timer {
                    property int timeline: 0
                    interval: 1000 / model.fps
                    running: true
                    repeat: true
                    onTriggered: {
                        timeline++;
                        series.append(timeline, model.value);

                        axisX.min++;
                        axisX.max++;
                    }
                    Component.onCompleted: {
                        for(var i = 0; i < model.bufferSize; i++) {
                            series.append(timeline++, 0);
                        }
                    }
                }
            }
        }
    }
}
