import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Window 2.2

StatPage {
    id: page

    height: Math.min(Screen.desktopAvailableHeight * 0.8, 1080)
    width: Math.min(Screen.desktopAvailableWidth * 0.8, 1920)

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
        width: Math.max(page.width * 0.2, 400)
        height: page.height - page.header.height
    }
}
