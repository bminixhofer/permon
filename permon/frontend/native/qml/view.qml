import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Window 2.2

StackView {
    id: stack
    height: Screen.desktopAvailableHeight * 0.8
    width: Screen.desktopAvailableWidth * 0.8
    initialItem: statPage

    SettingsPage {
        id: settingsPage
    }
    StatPage {
        id: statPage
        onSettingsButtonClicked: stack.push(settingsPage)
    }
}
