import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.0
import QtGraphicalEffects 1.0

Page {
    signal cancelButtonClicked
    signal acceptButtonClicked
    id: settingsPage

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
                    text: "Settings"
                }

                Item {
                    Layout.fillWidth: true
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
        id: listView
        anchors.fill: parent
        model: settingsModel

        delegate: Loader {
            x: 20

            sourceComponent: {
                switch(model.type) {
                    case "category": return category;
                    case "stat": return stat;
                }
            }

            Component {
                id: category

                Label {
                    height: 40
                    verticalAlignment: Text.AlignBottom
                    text: model.name
                    font.pixelSize: 22
                }
            }

            Component {
                id: stat
                RowLayout {
                    height: 30
                    width: parent.width

                    CheckBox {
                        id: checkbox
                        Layout.leftMargin: 15
                        checked: model.checked
                        text: model.name

                        indicator: Rectangle {
                            x: 5
                            y: 5
                            height: parent.height - 10
                            width: height
                            border.color: "#333"
                            border.width: 2

                            Rectangle {
                                visible: checkbox.checked
                                x: 4
                                y: 4
                                width: parent.width - x * 2
                                height: parent.height - y * 2
                                color: "#48cfad"
                            }
                        }

                        contentItem: Text {
                            text: parent.text
                            font.family: "Roboto Mono"
                            anchors.left: parent.indicator.right
                            anchors.leftMargin: 10
                        }

                        onClicked: {
                            settingsModel.toggleStat(model.tag, checked);
                        }
                    }
                }
            }
        }
    }

    footer: RowLayout {
        Button {
            Layout.bottomMargin: 20
            Layout.leftMargin: 20
            text: "Cancel"
            font.pixelSize: 20
            font.bold: true
            background: Rectangle {
                id: cancelButtonBackground
                implicitWidth: 100
                implicitHeight: 50
            }

            DropShadow {
                anchors.fill: cancelButtonBackground
                color: "#777"
                radius: 10.0
                samples: radius * 2
                source: cancelButtonBackground
                horizontalOffset: 3
                verticalOffset: 3
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    settingsModel.resetSettings();
                    settingsPage.cancelButtonClicked();
                }
            }
        }

        Item {
            Layout.fillWidth: true
        }

        Button {
            Layout.bottomMargin: 20
            Layout.rightMargin: 20
            text: "<font color='white'>Accept</font>"
            font.pixelSize: 20
            font.bold: true
            background: Rectangle {
                id: acceptButtonBackground
                implicitWidth: 100
                implicitHeight: 50
                color: "#48cfad"
            }

            DropShadow {
                anchors.fill: acceptButtonBackground
                color: "#777"
                radius: 10.0
                samples: radius * 2
                source: acceptButtonBackground
                horizontalOffset: 3
                verticalOffset: 3
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    settingsModel.submitSettings();
                    settingsPage.acceptButtonClicked();
                }
            }
        }
    }
}