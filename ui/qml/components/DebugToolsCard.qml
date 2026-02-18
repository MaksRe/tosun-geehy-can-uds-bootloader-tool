import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

/*
  Отдельная карточка сервисных команд, используемых только для отладки.
  Эти команды не требуются для штатного сценария программирования.
*/
Card {
    id: root

    property var appController
    property color textMain: "#1f2d3d"
    property color textSoft: "#607084"
    property bool showCardHeader: false
    readonly property int contentPadding: 12

    readonly property bool debugEnabled: root.appController ? root.appController.debugEnabled : false
    readonly property bool controlsEnabled: root.debugEnabled && root.appController
        && !root.appController.programmingActive && !root.appController.firmwareLoading

    Layout.fillWidth: true
    Layout.preferredHeight: root.debugEnabled ? 188 : 92

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.contentPadding
        spacing: 8

        Text {
            text: "Сервисные команды (Отладка)"
            visible: root.showCardHeader
            color: root.textMain
            font.pixelSize: 18
            font.bold: true
            font.family: "Bahnschrift"
        }

        Text {
            text: root.debugEnabled
                ? "Команды сброса вынесены сюда. Используйте их только для диагностики и тестов."
                : "Команды сброса доступны только в режиме отладки. Включите «Отладка» в шапке окна."
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: root.debugEnabled

            FancyButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                text: "Проверить статус"
                enabled: root.controlsEnabled
                tone: "#3b82f6"
                toneHover: "#2563eb"
                tonePressed: "#1d4ed8"
                onClicked: if (root.appController) root.appController.checkState()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: root.debugEnabled

            FancyButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                text: "Сброс в загрузчик"
                enabled: root.controlsEnabled
                tone: "#14b8a6"
                toneHover: "#0d9488"
                tonePressed: "#0f766e"
                onClicked: if (root.appController) root.appController.resetToBootloader()
            }

            FancyButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                text: "Сброс в основное ПО"
                enabled: root.controlsEnabled
                tone: "#6366f1"
                toneHover: "#4f46e5"
                tonePressed: "#4338ca"
                onClicked: if (root.appController) root.appController.resetToMainProgram()
            }
        }

        Item {
            visible: !root.debugEnabled
            Layout.preferredHeight: 2
        }
    }
}
