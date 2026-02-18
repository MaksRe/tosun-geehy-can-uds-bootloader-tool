import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Card {
    id: root

    property var appController
    property color textMain: "#1f2d3d"
    property color textSoft: "#607084"
    property color inputBg: "#f7fbff"
    property color inputBorder: "#c8d9ea"
    property color inputFocus: "#0ea5e9"
    readonly property bool controlsEnabled: root.appController ? (!root.appController.programmingActive && !root.appController.sourceAddressBusy) : false

    Layout.fillWidth: true
    Layout.preferredHeight: contentColumn.implicitHeight + 36

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 18
        spacing: 10

        Text {
            text: "Автоопределение адреса"
            color: root.textMain
            font.pixelSize: 22
            font.bold: true
            font.family: "Bahnschrift"
        }

        Text {
            text: "Анализ входящего RX J1939 потока и выбор кандидата адреса устройства"
            color: root.textSoft
            font.pixelSize: 13
            font.family: "Bahnschrift"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Text {
            text: "Кандидат адреса из потока"
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
            Layout.fillWidth: true
        }

        FancyComboBox {
            id: observedCandidatesCombo
            Layout.fillWidth: true
            model: root.appController ? root.appController.observedUdsCandidates : []
            enabled: root.appController !== null
                     && root.appController.observedUdsCandidates.length > 0
                     && root.controlsEnabled
            currentIndex: root.appController ? root.appController.selectedObservedUdsCandidateIndex : -1
            textColor: root.textMain
            bgColor: root.inputBg
            borderColor: root.inputBorder
            focusBorderColor: root.inputFocus
            onActivated: {
                if (root.appController) {
                    root.appController.setSelectedObservedUdsCandidateIndex(currentIndex)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            radius: 10
            color: "#eef5ff"
            border.color: "#c9d8ec"
            implicitHeight: statusText.implicitHeight + 16

            Text {
                id: statusText
                anchors.fill: parent
                anchors.margins: 8
                text: root.appController ? root.appController.observedUdsCandidateText : "Контроллер недоступен"
                color: root.textSoft
                font.pixelSize: 12
                font.family: "Bahnschrift"
                wrapMode: Text.WordWrap
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            FancyButton {
                Layout.fillWidth: true
                Layout.minimumWidth: 168
                text: "Применить адрес"
                enabled: root.controlsEnabled
                         && root.appController !== null
                         && root.appController.observedUdsCandidateAvailable
                tone: "#0284c7"
                toneHover: "#0369a1"
                tonePressed: "#075985"
                onClicked: if (root.appController) root.appController.applyObservedUdsIdentifiers()
            }

            FancyButton {
                Layout.fillWidth: true
                Layout.minimumWidth: 140
                text: "Сбросить"
                enabled: root.appController !== null && root.appController.observedUdsCandidateAvailable
                tone: "#64748b"
                toneHover: "#475569"
                tonePressed: "#334155"
                onClicked: if (root.appController) root.appController.resetObservedUdsCandidate()
            }
        }
    }
}
