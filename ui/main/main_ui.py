from PySide6.QtWidgets import QMainWindow

from ui.Bootloader.bootloader_ui import UiBootloaderTab
from ui.Hardware.hardware_ui import UiHardwareTab
from ui.main.main_window import Ui_MainWindow


class MainUi(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainUi, self).__init__()
        self.setupUi(self)

        self._ui_init()

    def _ui_init(self):
        self._tabs = {
            "Hardware": UiHardwareTab(),
            "Bootloader": UiBootloaderTab(),
        }

        for label, widget in self._tabs.items():
            self.tab_sections.addTab(widget, label)

        self.tab_sections.setCurrentIndex(0)
        self.frame_trace.hide()
