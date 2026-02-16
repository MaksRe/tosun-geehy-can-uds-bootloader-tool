import QtQuick 2.15

/*
  Пара "подпись + значение" для отображения диагностических данных.
  Назначение:
  - компактно показывать read-only информацию (производитель, модель, серийный номер и т.д.);
  - визуально разделять заголовок поля и его значение.

  Публичные свойства:
  - labelText: текст подписи;
  - valueText: текст значения;
  - labelColor/valueColor: цвета подписи и значения;
  - fontFamily: семейство шрифта.
*/
Item {
    property string labelText: ""
    property string valueText: ""
    property color labelColor: "#607084"
    property color valueColor: "#1f2d3d"
    property string fontFamily: "Bahnschrift"

    implicitHeight: 52
    implicitWidth: 320

    Column {
        anchors.fill: parent
        spacing: 5

        Text {
            text: labelText
            color: labelColor
            font.pixelSize: 11
            font.letterSpacing: 0.6
            font.capitalization: Font.AllUppercase
            font.family: fontFamily
        }

        Text {
            text: valueText.length > 0 ? valueText : "-"
            color: valueColor
            font.pixelSize: 16
            font.family: fontFamily
            elide: Text.ElideRight
        }
    }
}
