import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

/*
  Карточка управления UDS bootloader-процессом.
  Назначение:
  - выбор BIN-файла;
  - запуск программирования и сервисные команды reset/check;
  - отображение прогресса передачи;
  - отображение журнала состояний.

  Контракт:
  - appController предоставляет методы startProgramming/checkState/resetToBootloader/
    resetToMainProgram/clearLogs и свойства firmwarePath/progressValue/progressMax/logs/programmingActive.

  Сигналы:
  - openFirmwareDialogRequested: пробрасывается в Main.qml,
    где открывается FileDialog (чтобы диалог был в одном месте).
*/
Card {
    id: root

    property var appController
    property color textMain: "#1f2d3d"
    property color textSoft: "#607084"
    property color inputBg: "#f7fbff"
    property color inputBorder: "#c8d9ea"
    property color inputFocus: "#0ea5e9"

    signal openFirmwareDialogRequested()

    Layout.fillWidth: true
    Layout.preferredHeight: 568

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12

        Text {
            text: "Bootloader"
            color: root.textMain
            font.pixelSize: 22
            font.bold: true
            font.family: "Bahnschrift"
        }

        Text {
            text: "Загрузите BIN, запустите программирование и контролируйте процесс"
            color: root.textSoft
            font.pixelSize: 13
            font.family: "Bahnschrift"
        }

        // Выбор прошивки и показ текущего пути к файлу.
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            FancyTextField {
                Layout.fillWidth: true
                text: root.appController ? root.appController.firmwarePath : ""
                readOnly: true
                placeholderText: "BIN-файл не выбран"
                textColor: root.textMain
                bgColor: root.inputBg
                borderColor: root.inputBorder
                focusBorderColor: root.inputFocus
            }

            FancyButton {
                text: root.appController && root.appController.firmwareLoading ? "Загрузка BIN..." : "Открыть BIN"
                loading: root.appController ? root.appController.firmwareLoading : false
                debugLog: root.appController ? root.appController.debugEnabled : false
                tone: "#d97706"
                toneHover: "#b45309"
                tonePressed: "#92400e"
                onClicked: {
                    if (root.appController && root.appController.debugEnabled) {
                        console.log("[UI][BootloaderCard] Open BIN clicked. appController exists:", !!root.appController)
                    }
                    if (root.appController && root.appController.debugEnabled && root.appController.debugEvent) {
                        root.appController.debugEvent("UI: Open BIN clicked")
                    }
                    if (!root.appController) {
                        console.error("[UI][BootloaderCard] appController is null on Open BIN click")
                    }
                    root.openFirmwareDialogRequested()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? 20 : 0
            spacing: 8
            visible: root.appController ? root.appController.firmwareLoading : false
            opacity: visible ? 1 : 0

            Behavior on opacity {
                NumberAnimation {
                    duration: 140
                    easing.type: Easing.OutCubic
                }
            }

            Item {
                id: firmwareBusySpinner
                width: 14
                height: 14
                rotation: 0

                Rectangle {
                    anchors.fill: parent
                    radius: width / 2
                    color: "transparent"
                    border.width: 2
                    border.color: "#0ea5e9"
                    opacity: 0.35
                }

                Rectangle {
                    width: 4
                    height: 4
                    radius: 2
                    color: "#1d4ed8"
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                }

                RotationAnimator on rotation {
                    running: firmwareBusySpinner.visible
                    loops: Animation.Infinite
                    from: 0
                    to: 360
                    duration: 760
                }
            }

            Text {
                text: "Чтение BIN файла, подождите..."
                color: "#2563eb"
                font.pixelSize: 12
                font.family: "Bahnschrift"
            }

            Item {
                Layout.fillWidth: true
            }
        }

        // Основные действия по программированию и диагностике.
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: "Byte order"
                color: root.textSoft
                font.pixelSize: 13
                font.family: "Bahnschrift"
                Layout.preferredWidth: 130
            }

            FancyComboBox {
                id: endianCombo
                Layout.fillWidth: true
                model: ["Big Endian (MSB first)", "Little Endian (LSB first)"]
                currentIndex: root.appController ? root.appController.transferByteOrderIndex : 0
                enabled: root.appController ? !root.appController.programmingActive : false
                textColor: root.textMain
                bgColor: root.inputBg
                borderColor: root.inputBorder
                focusBorderColor: root.inputFocus

                onActivated: if (root.appController) root.appController.setTransferByteOrderIndex(currentIndex)
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            FancyButton {
                Layout.fillWidth: true
                text: root.appController && root.appController.programmingActive ? "Идет загрузка..." : "Начать программирование"
                enabled: root.appController ? (!root.appController.programmingActive && !root.appController.firmwareLoading) : false
                tone: "#10b981"
                toneHover: "#059669"
                tonePressed: "#047857"
                onClicked: if (root.appController) root.appController.startProgramming()
            }

            FancyButton {
                Layout.fillWidth: true
                text: "Проверить статус"
                tone: "#3b82f6"
                toneHover: "#2563eb"
                tonePressed: "#1d4ed8"
                onClicked: if (root.appController) root.appController.checkState()
            }

            FancyButton {
                text: "Очистить лог"
                tone: "#ef4444"
                toneHover: "#dc2626"
                tonePressed: "#b91c1c"
                onClicked: if (root.appController) root.appController.clearLogs()
            }
        }

        // Быстрые reset-команды ЭБУ.
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            FancyButton {
                Layout.fillWidth: true
                text: "Сброс в загрузчик"
                tone: "#14b8a6"
                toneHover: "#0d9488"
                tonePressed: "#0f766e"
                onClicked: if (root.appController) root.appController.resetToBootloader()
            }

            FancyButton {
                Layout.fillWidth: true
                text: "Сброс в основное ПО"
                tone: "#6366f1"
                toneHover: "#4f46e5"
                tonePressed: "#4338ca"
                onClicked: if (root.appController) root.appController.resetToMainProgram()
            }
        }

        // Виджет прогресса передачи данных в bootloader.
        Rectangle {
            Layout.fillWidth: true
            radius: 12
            color: "#f4f8fd"
            border.color: "#d6e2ef"
            implicitHeight: 88

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 6

                FancyProgressBar {
                    Layout.fillWidth: true
                    from: 0
                    to: root.appController ? root.appController.progressMax : 1
                    value: root.appController ? root.appController.progressValue : 0
                }

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: {
                            if (!root.appController) {
                                return "0 / 0 байт"
                            }
                            return root.appController.progressValue + " / " + root.appController.progressMax + " байт"
                        }
                        color: root.textSoft
                        font.pixelSize: 12
                        font.family: "Bahnschrift"
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: {
                            if (!root.appController || root.appController.progressMax <= 0) {
                                return "0%"
                            }
                            return Math.round((root.appController.progressValue / root.appController.progressMax) * 100) + "%"
                        }
                        color: root.textMain
                        font.pixelSize: 12
                        font.family: "Bahnschrift"
                        font.bold: true
                    }
                }
            }
        }

        // Журнал состояния bootloader-сценария.
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 14
            color: "#f4f8fd"
            border.color: "#d6e2ef"

            ListView {
                id: logList
                anchors.fill: parent
                anchors.margins: 10
                clip: true
                spacing: 6
                model: root.appController ? root.appController.logs : []

                // Автоскролл к последнему сообщению.
                onCountChanged: if (count > 0) positionViewAtEnd()

                delegate: Rectangle {
                    width: logList.width
                    height: logText.implicitHeight + 10
                    radius: 8
                    color: index % 2 === 0 ? "#f8fbff" : "#edf3fa"

                    Text {
                        id: logText
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        text: modelData.time + "   " + modelData.text
                        color: modelData.color
                        wrapMode: Text.Wrap
                        font.pixelSize: 13
                        font.family: "Bahnschrift"
                    }
                }

                ScrollBar.vertical: ScrollBar {}
            }
        }
    }
}


