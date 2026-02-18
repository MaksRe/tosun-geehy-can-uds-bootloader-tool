import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

/*
  Top header card with global runtime status chips and debug toggle.
*/
Card {
    id: root

    property var appController
    property color textMain: "#1f2d3d"
    property color accentWarm: "#f59e0b"
    readonly property bool compactLayout: width < 1120

    readonly property bool canConnected: appController ? appController.connected : false
    readonly property bool traceActive: appController ? appController.tracing : false
    readonly property bool programmingActive: appController ? appController.programmingActive : false
    signal openCanJournalRequested()

    implicitHeight: root.compactLayout ? 208 : 154

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 10

        Text {
            text: "Панель программирования CAN / UDS"
            color: root.textMain
            font.pixelSize: 30
            font.bold: true
            font.family: "Bahnschrift"
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.compactLayout ? 2 : 4
            columnSpacing: 10
            rowSpacing: 8

            StatusChip {
                Layout.fillWidth: root.compactLayout
                label: root.canConnected ? "CAN: подключен" : "CAN: отключен"
                chipColor: root.canConnected ? "#e6f8ef" : "#fdecec"
                chipBorder: root.canConnected ? "#7acda5" : "#f5a5a5"
                textColor: root.textMain
            }

            StatusChip {
                Layout.fillWidth: root.compactLayout
                label: root.traceActive ? "Трассировка: активна" : "Трассировка: выкл"
                chipColor: root.traceActive ? "#e9f2ff" : "#f1f5fa"
                chipBorder: root.traceActive ? "#93c5fd" : "#c6d7ea"
                textColor: root.textMain
            }

            StatusChip {
                Layout.fillWidth: root.compactLayout
                label: root.programmingActive ? "Программирование: идет" : "Программирование: готово"
                chipColor: root.programmingActive ? "#fff4e6" : "#f1f5fa"
                chipBorder: root.programmingActive ? root.accentWarm : "#c6d7ea"
                textColor: root.textMain
            }

            Rectangle {
                Layout.fillWidth: root.compactLayout
                Layout.alignment: root.compactLayout ? Qt.AlignLeft : Qt.AlignRight
                radius: 10
                color: root.appController && root.appController.debugEnabled ? "#e7f8ef" : "#f1f5fa"
                border.color: root.appController && root.appController.debugEnabled ? "#88d4af" : "#c6d7ea"
                border.width: 1
                implicitHeight: 34
                implicitWidth: 168

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 8
                    spacing: 8

                    Text {
                        text: "Отладка"
                        color: root.textMain
                        font.pixelSize: 13
                        font.family: "Bahnschrift"
                    }

                    Item { Layout.fillWidth: true }

                    FancySwitch {
                        id: debugSwitch
                        trackWidth: 50
                        trackHeight: 28
                        onColor: "#10b981"
                        offColor: "#dfe9f5"
                        borderOnColor: "#059669"
                        borderOffColor: "#b4c8df"
                        checked: root.appController ? root.appController.debugEnabled : false
                        onToggled: {
                            if (root.appController) {
                                root.appController.setDebugEnabled(checked)
                            }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Item { Layout.fillWidth: true }

            FancyButton {
                Layout.preferredWidth: 176
                Layout.minimumWidth: 160
                text: "Открыть журнал CAN"
                tone: "#0ea5a4"
                toneHover: "#0f766e"
                tonePressed: "#115e59"
                onClicked: root.openCanJournalRequested()
            }
        }
    }
}
