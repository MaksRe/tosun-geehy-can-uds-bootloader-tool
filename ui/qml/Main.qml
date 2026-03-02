import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
import QtQuick.Window 2.15
import "components"

/*
  Главный экран приложения CAN/UDS bootloader.

  Архитектура экрана:
  - фон и глобальная палитра задаются здесь;
  - логика взаимодействия с backend идет через context-свойство appController;
  - крупные UI-блоки вынесены в отдельные компоненты в ui/qml/components.

  Важно:
  - данный файл отвечает только за композицию экрана и общие диалоги;
  - бизнес-логика находится в Python (ui/qml/app_controller.py, uds/*, app_can/*).
*/
ApplicationWindow {
    id: window

    visible: true
    width: 1320
    height: 840
    minimumWidth: 1040
    minimumHeight: 720
    title: "TOSUN Geehy CAN UDS Загрузчик"

    // Централизованная палитра для согласованного оформления всех дочерних компонентов.
    readonly property color bgStart: "#f9fcff"
    readonly property color bgEnd: "#edf4fb"
    readonly property color cardColor: "#ffffff"
    readonly property color cardBorder: "#d6e2ef"
    readonly property color textMain: "#1f2d3d"
    readonly property color textSoft: "#607084"
    readonly property color accentWarm: "#f59e0b"
    readonly property color inputBg: "#f6faff"
    readonly property color inputBorder: "#c8d9ea"
    readonly property color inputFocus: "#0ea5e9"

    property string toastTitle: ""
    property string toastText: ""
    property bool toastVisible: false
    readonly property var backendController: appController

    function showToast(title, text) {
        toastTitle = title ? title : ""
        toastText = text ? text : ""
        toastVisible = true
        toastTimer.restart()
    }

    // Декоративный фоновый слой.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: window.bgStart }
            GradientStop { position: 1.0; color: window.bgEnd }
        }

        Rectangle {
            width: 420
            height: width
            radius: width / 2
            x: -130
            y: -180
            color: "#60a5fa"
            opacity: 0.16
        }

        Rectangle {
            width: 540
            height: width
            radius: width / 2
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: -240
            color: "#22d3ee"
            opacity: 0.12
        }
    }

    // Универсальный модальный диалог для сообщений от backend.
    Timer {
        id: toastTimer
        interval: 2600
        repeat: false
        onTriggered: window.toastVisible = false
    }

    Rectangle {
        id: toast
        z: 1000
        width: Math.min(window.width - 40, 520)
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 20
        anchors.rightMargin: 20
        radius: 12
        color: "#ffffff"
        border.color: "#bfd6eb"
        border.width: 1
        opacity: window.toastVisible ? 1 : 0
        visible: opacity > 0
        implicitHeight: toastLayout.implicitHeight + 18

        Behavior on opacity {
            NumberAnimation {
                duration: 180
                easing.type: Easing.OutCubic
            }
        }

        ColumnLayout {
            id: toastLayout
            anchors.fill: parent
            anchors.margins: 10
            spacing: 4

            Text {
                text: window.toastTitle
                color: "#1f2d3d"
                font.pixelSize: 13
                font.family: "Bahnschrift"
                font.bold: true
                visible: text.length > 0
            }

            Text {
                text: window.toastText
                color: "#4f6278"
                font.pixelSize: 12
                font.family: "Bahnschrift"
                wrapMode: Text.Wrap
            }
        }

        MouseArea {
            anchors.fill: parent
            onClicked: window.toastVisible = false
        }
    }

    // Подписка на сигнал appController.infoMessage(title, text).
    Connections {
        target: window.backendController

        function onInfoMessage(title, text) {
            if (window.backendController && window.backendController.debugEnabled) {
                console.log("[UI][Main] infoMessage:", title, text)
            }
            window.showToast(title, text)
        }
    }

    // Диалог выбора BIN-файла прошивки.
    FileDialog {
        id: firmwareDialog
        title: "Выберите BIN-файл"
        nameFilters: ["BIN файлы (*.bin)", "Все файлы (*)"]
        onAccepted: {
            var chosen = ""
            if (selectedFile) {
                chosen = selectedFile.toString()
            } else if (selectedFiles && selectedFiles.length > 0) {
                chosen = selectedFiles[0].toString()
            } else if (currentFile) {
                chosen = currentFile.toString()
            }

            if (window.backendController && window.backendController.debugEnabled) {
                console.log("[UI][Main] FileDialog accepted. chosen:", chosen)
            }
            if (!window.backendController) {
                console.error("[UI][Main] appController is null in FileDialog.onAccepted")
                window.showToast("Отладка", "appController не найден в FileDialog")
                return
            }

            if (window.backendController && window.backendController.debugEnabled && window.backendController.debugEvent) {
                window.backendController.debugEvent("UI: FileDialog accepted: " + chosen)
            }

            window.backendController.loadFirmware(chosen)
        }
    }

    Window {
        id: canJournalWindow
        width: 1320
        height: 430
        minimumWidth: 980
        minimumHeight: 320
        visible: false
        modality: Qt.NonModal
        title: "Журнал CAN"
        transientParent: window

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: window.bgStart }
                GradientStop { position: 1.0; color: window.bgEnd }
            }
        }

        CanTrafficCard {
            anchors.fill: parent
            anchors.margins: 14
            appController: window.backendController
            cardColor: window.cardColor
            cardBorder: window.cardBorder
            textMain: window.textMain
            textSoft: window.textSoft
        }
    }

    ScrollView {
        id: contentScroll
        anchors.fill: parent
        anchors.margins: 16
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            id: rootColumn
            width: Math.max(0, contentScroll.availableWidth)
            spacing: 12

            HeaderCard {
                id: headerCard
                appController: window.backendController
                cardColor: window.cardColor
                cardBorder: window.cardBorder
                textMain: window.textMain
                accentWarm: window.accentWarm
                Layout.fillWidth: true
                onOpenCanJournalRequested: {
                    canJournalWindow.visible = true
                    canJournalWindow.raise()
                    canJournalWindow.requestActivate()
                }
            }

            // Адаптивная компоновка:
            // - широкое окно: две независимые колонки (левая и правая);
            // - узкое окно: карточки идут последовательно в один столбец.
            Item {
                id: dashboardArea
                Layout.fillWidth: true
                readonly property bool wideLayout: contentScroll.availableWidth > 1180
                readonly property int sidePanelWidth: Math.max(430, Math.min(500, Math.round(contentScroll.availableWidth * 0.36)))
                readonly property int gap: 12
                readonly property real viewportHeight: Math.max(0, contentScroll.availableHeight - headerCard.height - rootColumn.spacing)
                Layout.preferredHeight: Math.max(implicitHeight, viewportHeight)
                implicitHeight: dashboardLoader.item ? dashboardLoader.item.implicitHeight : 0

                Loader {
                    id: dashboardLoader
                    anchors.fill: parent
                    sourceComponent: dashboardArea.wideLayout ? wideDashboard : narrowDashboard
                    onLoaded: if (item) {
                        item.width = width
                        item.height = height
                    }
                    onWidthChanged: if (item) item.width = width
                    onHeightChanged: if (item) item.height = height
                }

                Component {
                    id: wideDashboard

                    RowLayout {
                        spacing: dashboardArea.gap
                        implicitHeight: Math.max(leftColumn.implicitHeight, rightColumn.implicitHeight)

                        ColumnLayout {
                            id: leftColumn
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.alignment: Qt.AlignTop
                            spacing: dashboardArea.gap

                            ConnectionCard {
                                appController: window.backendController
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                inputBg: window.inputBg
                                inputBorder: window.inputBorder
                                inputFocus: window.inputFocus
                                Layout.fillWidth: true
                            }

                            BootloaderCard {
                                appController: window.backendController
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                inputBg: window.inputBg
                                inputBorder: window.inputBorder
                                inputFocus: window.inputFocus
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                onOpenFirmwareDialogRequested: firmwareDialog.open()
                            }
                        }

                        ColumnLayout {
                            id: rightColumn
                            Layout.minimumWidth: dashboardArea.sidePanelWidth
                            Layout.preferredWidth: dashboardArea.sidePanelWidth
                            Layout.maximumWidth: dashboardArea.sidePanelWidth
                            Layout.alignment: Qt.AlignTop
                            spacing: dashboardArea.gap

                            SpoilerSection {
                                title: "Автоопределение адреса"
                                hintText: "Дополнительный функционал"
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                Layout.fillWidth: true

                                AutoDetectCard {
                                    appController: window.backendController
                                    cardColor: window.cardColor
                                    cardBorder: window.cardBorder
                                    textMain: window.textMain
                                    textSoft: window.textSoft
                                    inputBg: window.inputBg
                                    inputBorder: window.inputBorder
                                    inputFocus: window.inputFocus
                                    Layout.fillWidth: true
                                }
                            }

                            SpoilerSection {
                                title: "UDS CAN идентификаторы"
                                hintText: "Дополнительный функционал"
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                Layout.fillWidth: true

                                IdentifiersCard {
                                    appController: window.backendController
                                    cardColor: window.cardColor
                                    cardBorder: window.cardBorder
                                    textMain: window.textMain
                                    textSoft: window.textSoft
                                    inputBg: window.inputBg
                                    inputBorder: window.inputBorder
                                    inputFocus: window.inputFocus
                                    Layout.fillWidth: true
                                }
                            }

                            SpoilerSection {
                                title: "Параметры протокола"
                                hintText: "Дополнительный функционал"
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                Layout.fillWidth: true

                                ProtocolCard {
                                    appController: window.backendController
                                    cardColor: window.cardColor
                                    cardBorder: window.cardBorder
                                    textMain: window.textMain
                                    textSoft: window.textSoft
                                    inputBg: window.inputBg
                                    inputBorder: window.inputBorder
                                    inputFocus: window.inputFocus
                                    Layout.fillWidth: true
                                }
                            }

                            SpoilerSection {
                                title: "Сервисные команды"
                                hintText: "Дополнительный функционал (отладка)"
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                Layout.fillWidth: true

                                DebugToolsCard {
                                    appController: window.backendController
                                    cardColor: window.cardColor
                                    cardBorder: window.cardBorder
                                    textMain: window.textMain
                                    textSoft: window.textSoft
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }

                Component {
                    id: narrowDashboard

                    ColumnLayout {
                        spacing: dashboardArea.gap

                        ConnectionCard {
                            appController: window.backendController
                            cardColor: window.cardColor
                            cardBorder: window.cardBorder
                            textMain: window.textMain
                            textSoft: window.textSoft
                            inputBg: window.inputBg
                            inputBorder: window.inputBorder
                            inputFocus: window.inputFocus
                            Layout.fillWidth: true
                        }

                        SpoilerSection {
                            title: "Автоопределение адреса"
                            hintText: "Дополнительный функционал"
                            cardColor: window.cardColor
                            cardBorder: window.cardBorder
                            textMain: window.textMain
                            textSoft: window.textSoft
                            Layout.fillWidth: true

                            AutoDetectCard {
                                appController: window.backendController
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                inputBg: window.inputBg
                                inputBorder: window.inputBorder
                                inputFocus: window.inputFocus
                                Layout.fillWidth: true
                            }
                        }

                        SpoilerSection {
                            title: "UDS CAN идентификаторы"
                            hintText: "Дополнительный функционал"
                            cardColor: window.cardColor
                            cardBorder: window.cardBorder
                            textMain: window.textMain
                            textSoft: window.textSoft
                            Layout.fillWidth: true

                            IdentifiersCard {
                                appController: window.backendController
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                inputBg: window.inputBg
                                inputBorder: window.inputBorder
                                inputFocus: window.inputFocus
                                Layout.fillWidth: true
                            }
                        }

                        SpoilerSection {
                            title: "Параметры протокола"
                            hintText: "Дополнительный функционал"
                            cardColor: window.cardColor
                            cardBorder: window.cardBorder
                            textMain: window.textMain
                            textSoft: window.textSoft
                            Layout.fillWidth: true

                            ProtocolCard {
                                appController: window.backendController
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                inputBg: window.inputBg
                                inputBorder: window.inputBorder
                                inputFocus: window.inputFocus
                                Layout.fillWidth: true
                            }
                        }

                        SpoilerSection {
                            title: "Сервисные команды"
                            hintText: "Дополнительный функционал (отладка)"
                            cardColor: window.cardColor
                            cardBorder: window.cardBorder
                            textMain: window.textMain
                            textSoft: window.textSoft
                            Layout.fillWidth: true

                            DebugToolsCard {
                                appController: window.backendController
                                cardColor: window.cardColor
                                cardBorder: window.cardBorder
                                textMain: window.textMain
                                textSoft: window.textSoft
                                Layout.fillWidth: true
                            }
                        }

                        BootloaderCard {
                            appController: window.backendController
                            cardColor: window.cardColor
                            cardBorder: window.cardBorder
                            textMain: window.textMain
                            textSoft: window.textSoft
                            inputBg: window.inputBg
                            inputBorder: window.inputBorder
                            inputFocus: window.inputFocus
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            onOpenFirmwareDialogRequested: firmwareDialog.open()
                        }
                    }
                }
            }

        }
    }

    // При старте сразу запрашиваем список доступных CAN-адаптеров.
    Component.onCompleted: {
        if (window.backendController && window.backendController.debugEnabled) {
            console.log("[UI][Main] Component completed. appController exists:", !!window.backendController)
        }
        if (!window.backendController) {
            console.error("[UI][Main] appController is null on startup")
            window.showToast("Отладка", "appController не найден при старте")
            return
        }

        if (window.backendController && window.backendController.debugEnabled && window.backendController.debugEvent) {
            window.backendController.debugEvent("UI: startup scan requested")
        }
        window.backendController.scanDevices()
    }
}
