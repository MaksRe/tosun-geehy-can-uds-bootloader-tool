from PySide6.QtCore import Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QListWidgetItem, QMenu, QMessageBox, QWidget

from colors import RowColor
from uds.bootloader import Bootloader
from uds.firmware import Firmware, FirmwareState
from ui.Bootloader.bootloader_tab_ui import Ui_BootloaderTabWidget


class UiBootloaderTab(QWidget, Ui_BootloaderTabWidget):
    def __init__(self):
        super(UiBootloaderTab, self).__init__()
        self.setupUi(self)

        self._file_path = None
        self._firmware = None
        self._bootloader = Bootloader()
        self._programming_active = False

        self.btn_open_file.clicked.connect(self._load_file)
        self.btn_upload.clicked.connect(self._upload_firmware)
        self.btn_check_state.clicked.connect(self._check_state)
        self.btn_clear.clicked.connect(self._clear_progress)

        self._bootloader.signal_new_state.connect(self._ui_add_log)
        self._bootloader.signal_data_sent.connect(self._set_progress)
        self._bootloader.signal_finished.connect(self._finish_handler)

        self.menu = QMenu(self)

        action_uds_reset = QAction("переход к загрузчику", self)
        action_software_reset = QAction("переход к основной программе", self)

        action_uds_reset.triggered.connect(self._ecu_uds_reset)
        action_software_reset.triggered.connect(self._ecu_software_reset)

        self.menu.addAction(action_uds_reset)
        self.menu.addAction(action_software_reset)

        self.tool_btn_reset.setMenu(self.menu)

    def _ui_update_path_to_file(self):
        self.line_path_to_file.setText(self._file_path)

    def _load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите .bin файл",
            "",
            "Binary Files (*.bin)",
        )

        if not file_path:
            return

        self._file_path = file_path
        self._firmware = Firmware(self._file_path)

        if self._firmware.state != FirmwareState.successfully_uploaded:
            self._ui_add_log("Ошибка загрузки bin-файла", RowColor.red)
            return

        self._bootloader.set_firmware(self._firmware.binary_content)

        firmware_size = len(self._firmware.binary_content)

        self._ui_update_path_to_file()
        self._ui_config_progress_bar(firmware_size)

        self._ui_add_log(f"Успешно загружен bin-файл ({firmware_size} байт)", RowColor.green)

    def _ui_config_progress_bar(self, file_size):
        self.progress_loading.setMinimum(0)
        self.progress_loading.setMaximum(file_size)
        self.progress_loading.setValue(0)

    def _set_programming_active(self, active):
        self._programming_active = active

    @Slot(bool)
    def _finish_handler(self, _success):
        self._set_programming_active(False)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Успешное завершение")
        msg_box.setText("Программа успешно загружена!")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

        self.progress_loading.reset()

    def _clear_progress(self):
        self.list_process.clear()

    def _upload_firmware(self):
        self._set_programming_active(True)
        if not self._bootloader.start():
            self._set_programming_active(False)

    def _ecu_uds_reset(self):
        self._bootloader.ecu_uds_reset()

    def _ecu_software_reset(self):
        self._bootloader.ecu_software_reset()

    def _check_state(self):
        self._bootloader.check_state()

    def _ui_add_log(self, text, color):
        item = QListWidgetItem(text)
        item.setForeground(color)
        self.list_process.addItem(item)

        if self._programming_active and color == RowColor.red:
            self._set_programming_active(False)

    @Slot(int)
    def _set_progress(self, value):
        maximum = self.progress_loading.maximum()
        if value > maximum:
            value = maximum
        self.progress_loading.setValue(value)
