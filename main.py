import logging
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from ui.qml.app_controller import AppController


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    controller = AppController()
    engine.rootContext().setContextProperty("appController", controller)

    qml_path = Path(__file__).resolve().parent / "ui" / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
