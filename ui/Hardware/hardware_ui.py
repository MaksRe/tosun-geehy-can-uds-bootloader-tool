from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QMessageBox

from app_can.CanDevice import CanDevice, DeviceInfo
from libTSCANAPI import size_t, s32
from resources.icons import Icons
from ui.Hardware.hardware_tab_ui import Ui_HardwareTabWidget


class UiHardwareTab(QWidget, Ui_HardwareTabWidget):
    def __init__(self):
        super(UiHardwareTab, self).__init__()
        self.setupUi(self)

        self.btn_scan_devices.clicked.connect(self._ui_print_devices)
        self.btn_connect.clicked.connect(self.connect_to_device)
        self.btn_trace.clicked.connect(self.toggle_trace)
        self.combo_box_devices.currentIndexChanged.connect(self._ui_print_device_info)

        self._ui_init()

    def _ui_init(self):
        # Terminator is ON
        self.check_box_terminator.setChecked(True)
        # Current channel is 1
        self.combo_box_channel.setCurrentIndex(0)
        # Current baud rate is 500kbps
        self.combo_box_baud_rate.setCurrentIndex(2)

    def _ui_set_device_info(self, device_info: DeviceInfo):
        manufacturer = device_info.manufacturer.value
        product = device_info.product.value
        serial = device_info.serial.value
        if manufacturer is not None:
            self.line_manufacturer.setText(device_info.manufacturer.value.decode('utf8'))
        if product is not None:
            self.line_product.setText(device_info.product.value.decode('utf8'))
        if serial is not None:
            self.line_serial.setText(device_info.serial.value.decode('utf8'))

    def _ui_set_device_handle(self, hardware_handle: size_t):
        if hardware_handle.value is not None:
            self.line_device_handler.setText(str(hardware_handle.value))

    def _ui_toggle_connect_btn(self):
        if CanDevice.instance().is_connect:
            icon = Icons.connect_off
            text = "Отключиться"
        else:
            icon = Icons.connect_on
            text = "Подключиться"
        self.btn_connect.setIcon(QIcon(icon))
        self.btn_connect.setText(text)

    def _ui_toggle_trace_btn(self):
        if CanDevice.instance().is_trace:
            icon = Icons.trace_on
            text = "Применить настройки"
        else:
            icon = Icons.trace_off
            text = "Отменить настройки"
        self.btn_trace.setIcon(QIcon(icon))
        self.btn_trace.setText(text)

    def _ui_clear_trace_btn(self):
        self.btn_trace.setIcon(QIcon(Icons.trace_on))

    def _ui_print_devices(self):
        devices: s32 = CanDevice().get_devices()
        for i in range(devices.value):
            self.combo_box_devices.addItem(str(i))

    def _ui_print_device_info(self, device_index):
        # device_index: int = self.combo_box_devices.currentIndex()
        if device_index == -1:
            # QMessageBox.warning(
            #     self,
            #     "Ошибка получения данных",
            #     "Выберите устройство",
            #     QMessageBox.StandardButton.Ok)
            return
        CanDevice.instance().update_device_info(device_index)
        device_info: DeviceInfo = CanDevice().device_info
        self._ui_set_device_info(device_info)

    def connect_to_device(self):
        device_index: int = self.combo_box_devices.currentIndex()
        can_device: CanDevice = CanDevice()
        if device_index == -1:
            QMessageBox.warning(
                self,
                "Ошибка подключения",
                "Выберите устройство",
                QMessageBox.StandardButton.Ok)
            return
        if can_device.is_connect:
            can_device.disconnect_device()
            self._stop_trace()
            self._ui_toggle_connect_btn()
        else:
            hardware_handle: size_t = can_device.connect_to(device_index)
            if hardware_handle.value != 0:
                self._ui_set_device_handle(hardware_handle)
                self._ui_toggle_connect_btn()
            else:
                print("error connect to device")

    def toggle_trace(self):
        can_device: CanDevice = CanDevice()
        if not can_device.is_connect:
            QMessageBox.warning(self,
                                "Warning",
                                "hardware not connected",
                                QMessageBox.StandardButton.Ok)
            return

        if not can_device.is_trace:

            channel: int = self.combo_box_channel.currentIndex()
            baud_rate: int = int(self.combo_box_baud_rate.currentText())
            terminator: bool = self.check_box_terminator.isChecked()

            self._ui_toggle_trace_btn()

            can_device.start_trace(channel, baud_rate, terminator)
        else:
            self._ui_toggle_trace_btn()

            CanDevice.instance().stop_trace()

    def _stop_trace(self):
        CanDevice.instance().stop_trace()
        self._ui_clear_trace_btn()
