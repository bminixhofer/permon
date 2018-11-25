import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.4
import QtGraphicalEffects 1.0

Drawer {
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    edge: Qt.RightEdge
    interactive: false
    modal: false

    background: Rectangle {
        anchors.fill: parent
        opacity: 0.9

        Rectangle {
            z: -1
            anchors.fill: parent
            border.width: 2
            border.color: "#888"
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 10
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        anchors.bottomMargin: 10
        spacing: 20

        ColumnLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: parent.height / 2
            Layout.alignment: Qt.AlignTop

            Label {
                Layout.alignment: Qt.AlignTop
                text: "Add Stat"
                font.pixelSize: 26
            }

            ComboBox {
                function refreshModel() {
                    this.model = JSON.parse(settingsModel.getStats(false));
                    this.refreshSettings();
                }
                function refreshSettings() {
                    page.errorMessage = "";
                    settingsRepeater.model = JSON.parse(settingsModel.getSettings(currentIndex));
                }
                Layout.topMargin: 5
                Layout.alignment: Qt.AlignTop
                id: addStatBox
                Layout.fillWidth: true

                Component.onCompleted: refreshModel()
                onCurrentIndexChanged: refreshSettings()
            }

            Column {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.bottomMargin: 40
                spacing: 8

                Repeater {
                    id: settingsRepeater

                    RowLayout {
                        property string key: modelData["name"]
                        property string value: textField.text

                        width: parent.width

                        Label {
                            font.pixelSize: 18
                            font.capitalization: Font.Capitalize
                            text: modelData["name"]
                        }
                        TextField {
                            id: textField
                            Layout.alignment: Qt.AlignRight
                            horizontalAlignment: TextInput.AlignRight
                            font.family: "Roboto Mono"
                            text: modelData["defaultValue"]

                            background: Rectangle {
                                implicitWidth: 220
                                implicitHeight: 40
                            }

                            DropShadow {
                                z: -1
                                anchors.fill: source
                                color: "#777"
                                radius: 10.0
                                samples: radius * 2
                                source: parent.background
                                horizontalOffset: 3
                                verticalOffset: 3
                            }
                        }
                    }
                }
            }

            Button {
                Layout.alignment: Qt.AlignRight
                text: "<font color='white'>Add</font>"
                font.pixelSize: 20
                font.bold: true
                background: Rectangle {
                    implicitWidth: 100
                    implicitHeight: 50
                    color: "#48cfad"
                }

                DropShadow {
                    anchors.fill: source
                    color: "#777"
                    radius: 10.0
                    samples: radius * 2
                    source: parent.background
                    horizontalOffset: 3
                    verticalOffset: 3
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        var settings = {};
                        for(var i = 0; i < settingsRepeater.count; i++) {
                            var key = settingsRepeater.itemAt(i).key;
                            var value = settingsRepeater.itemAt(i).value;

                            settings[key] = value;
                        }

                        var errorMessage = settingsModel.addStat(addStatBox.currentIndex, JSON.stringify(settings));
                        removeStatBox.refreshModel();
                        addStatBox.refreshModel();

                        page.errorMessage = errorMessage;
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: parent.height / 2
            Layout.alignment: Qt.AlignTop

            Label {
                Layout.alignment: Qt.AlignTop
                text: "Remove Stat"
                font.pixelSize: 26
            }

            ComboBox {
                id: removeStatBox
                function refreshModel() {
                    this.model = JSON.parse(settingsModel.getStats(true));
                }
                Layout.topMargin: 5
                Layout.alignment: Qt.AlignTop
                Layout.fillWidth: true
                Component.onCompleted: refreshModel()
            }

            Item {
                Layout.fillHeight: true
            }

            Button {
                Layout.alignment: Qt.AlignRight
                text: "<font color='white'>Remove</font>"
                font.pixelSize: 20
                font.bold: true
                background: Rectangle {
                    implicitWidth: 100
                    implicitHeight: 50
                    color: "#48cfad"
                }

                DropShadow {
                    anchors.fill: source
                    color: "#777"
                    radius: 10.0
                    samples: radius * 2
                    source: parent.background
                    horizontalOffset: 3
                    verticalOffset: 3
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if(removeStatBox.count == 0) {
                            return;
                        }
                        var errorMessage = settingsModel.removeStat(removeStatBox.currentIndex);
                        removeStatBox.refreshModel();
                        addStatBox.refreshModel();
                    }
                }
            }
        }
    }
}
