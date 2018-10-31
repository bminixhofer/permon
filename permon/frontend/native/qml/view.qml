import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Window 2.2

StackView {
    id: stack
    height: Screen.desktopAvailableHeight * 0.8
    width: Screen.desktopAvailableWidth * 0.8
    initialItem: statPage

    Component {
        id: statPage

        StatPage {
            onSettingsButtonClicked: stack.push(settingsPage)
        }
    }

    Component {
        id: settingsPage

        SettingsPage {
            onCancelButtonClicked: stack.pop()
            onAcceptButtonClicked: stack.pop()
        }
    }
}
