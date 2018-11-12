import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Window 2.2

StatPage {
    id: page

    height: Screen.desktopAvailableHeight * 0.8
    width: Screen.desktopAvailableWidth * 0.8

    onSettingsButtonClicked: {
        if(settingsDrawer.opened) {
            settingsDrawer.close();
        } else {
            settingsDrawer.open();
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: settingsDrawer.close()
    }

    SettingsDrawer {
        id: settingsDrawer
        y: page.header.height
        width: page.width * 0.2
        height: page.height - page.header.height
    }
}
