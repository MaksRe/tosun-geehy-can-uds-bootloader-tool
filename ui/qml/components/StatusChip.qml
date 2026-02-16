import QtQuick 2.15

/*
  Небольшой индикатор статуса в шапке экрана.
  Назначение:
  - отображает текущее состояние системы кратким текстом;
  - цветом показывает норму/ошибку/активность.

  Публичные свойства:
  - label: текст статуса;
  - chipColor/chipBorder: цвета фона и рамки;
  - textColor: цвет текста.
*/
Rectangle {
    id: root

    property string label: ""
    property color chipColor: "#eef4fb"
    property color chipBorder: "#c6d7ea"
    property color textColor: "#1f2d3d"

    radius: 10
    color: chipColor
    border.color: chipBorder
    border.width: 1
    implicitHeight: 30
    implicitWidth: labelText.implicitWidth + 18

    Text {
        id: labelText
        anchors.centerIn: parent
        text: root.label
        color: root.textColor
        font.pixelSize: 13
        font.family: "Bahnschrift"
    }
}
