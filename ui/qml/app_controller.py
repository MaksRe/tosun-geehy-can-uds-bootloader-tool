from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path

from PySide6.QtCore import QObject, Property, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor

from app_can.CanDevice import CanDevice
from colors import RowColor
from uds.bootloader import Bootloader
from uds.firmware import Firmware, FirmwareState

LOGGER = logging.getLogger(__name__)


class FirmwareLoadWorker(QObject):
    finished = Signal(str, bool, bytes, str)

    def __init__(self, file_path: str):
        super().__init__()
        self._file_path = file_path

    @Slot()
    def run(self):
        firmware = Firmware(self._file_path)
        if firmware.state == FirmwareState.successfully_uploaded and firmware.binary_content is not None:
            self.finished.emit(self._file_path, True, firmware.binary_content, "")
            return
        self.finished.emit(self._file_path, False, b"", "Не удалось открыть BIN файл.")


class AppController(QObject):
    devicesChanged = Signal()
    selectedDeviceIndexChanged = Signal()
    deviceInfoChanged = Signal()
    connectionStateChanged = Signal()
    traceStateChanged = Signal()
    firmwarePathChanged = Signal()
    progressChanged = Signal()
    logsChanged = Signal()
    infoMessage = Signal(str, str)
    programmingActiveChanged = Signal()
    debugEnabledChanged = Signal()
    firmwareLoadingChanged = Signal()
    transferByteOrderIndexChanged = Signal()

    def __init__(self):
        super().__init__()

        self._can = CanDevice.instance()
        self._bootloader = Bootloader()
        self._bootloader.set_transfer_byte_order("big")

        # Display labels for ComboBox and actual hardware indexes from TSCAN.
        self._devices: list[str] = []
        self._device_indices: list[int] = []
        self._selected_device_index = -1

        self._manufacturer = ""
        self._product = ""
        self._serial = ""
        self._device_handle = ""

        self._firmware_path = ""
        self._firmware = None
        self._progress_value = 0
        self._progress_max = 1

        self._logs: list[dict[str, str]] = []
        self._programming_active = False
        self._debug_enabled = False
        self._firmware_loading = False
        self._transfer_byte_order_index = 0

        self._firmware_loader_thread: QThread | None = None
        self._firmware_loader_worker: FirmwareLoadWorker | None = None

        self._bootloader.signal_new_state.connect(self._on_bootloader_state)
        self._bootloader.signal_data_sent.connect(self._on_data_sent)
        self._bootloader.signal_finished.connect(self._on_programming_finished)

        self._can.signal_tracing_started.connect(self._on_trace_state_event)
        self._can.signal_tracing_stopped.connect(self._on_trace_state_event)

    @Property("QStringList", notify=devicesChanged)
    def devices(self):
        return self._devices

    @Property(int, notify=selectedDeviceIndexChanged)
    def selectedDeviceIndex(self):
        return self._selected_device_index

    @Property(str, notify=deviceInfoChanged)
    def manufacturer(self):
        return self._manufacturer

    @Property(str, notify=deviceInfoChanged)
    def product(self):
        return self._product

    @Property(str, notify=deviceInfoChanged)
    def serial(self):
        return self._serial

    @Property(str, notify=deviceInfoChanged)
    def deviceHandle(self):
        return self._device_handle

    @Property(bool, notify=connectionStateChanged)
    def connected(self):
        return self._can.is_connect

    @Property(str, notify=connectionStateChanged)
    def connectionActionText(self):
        return "Отключиться" if self._can.is_connect else "Подключиться"

    @Property(bool, notify=traceStateChanged)
    def tracing(self):
        return self._can.is_trace

    @Property(str, notify=traceStateChanged)
    def traceActionText(self):
        return "Остановить трассировку" if self._can.is_trace else "Запустить трассировку"

    @Property(str, notify=firmwarePathChanged)
    def firmwarePath(self):
        return self._firmware_path

    @Property(int, notify=progressChanged)
    def progressValue(self):
        return self._progress_value

    @Property(int, notify=progressChanged)
    def progressMax(self):
        return self._progress_max

    @Property("QVariantList", notify=logsChanged)
    def logs(self):
        return self._logs

    @Property(bool, notify=programmingActiveChanged)
    def programmingActive(self):
        return self._programming_active

    @Property(bool, notify=debugEnabledChanged)
    def debugEnabled(self):
        return self._debug_enabled

    @Property(bool, notify=firmwareLoadingChanged)
    def firmwareLoading(self):
        return self._firmware_loading

    @Property(int, notify=transferByteOrderIndexChanged)
    def transferByteOrderIndex(self):
        return self._transfer_byte_order_index

    @Slot(bool)
    def setDebugEnabled(self, enabled):
        value = bool(enabled)
        if self._debug_enabled == value:
            return
        self._debug_enabled = value
        self.debugEnabledChanged.emit()
        self.infoMessage.emit("Debug", "Debug mode enabled." if value else "Debug mode disabled.")

    @Slot(int)
    def setTransferByteOrderIndex(self, index):
        try:
            parsed_index = int(index)
        except (TypeError, ValueError):
            parsed_index = 0

        new_index = 1 if parsed_index == 1 else 0
        if self._transfer_byte_order_index == new_index:
            return

        self._transfer_byte_order_index = new_index
        self.transferByteOrderIndexChanged.emit()

        byte_order = "little" if new_index == 1 else "big"
        self._bootloader.set_transfer_byte_order(byte_order)

        label = "Little Endian" if new_index == 1 else "Big Endian"
        self._append_log(f"Transfer byte order: {label}", QColor("#0ea5e9"))
        self.infoMessage.emit("Bootloader", f"Selected transfer byte order: {label}.")

    @Slot(str)
    def debugEvent(self, text):
        if not self._debug_enabled:
            return
        message = str(text)
        LOGGER.info("QML debug: %s", message)
        self._append_log(f"DEBUG: {message}", QColor("#93c5fd"))
        self.infoMessage.emit("Debug", message)

    @Slot()
    def scanDevices(self):
        if self._debug_enabled:
            LOGGER.info("scanDevices() called")
        devices_count = self._can.get_devices()
        if devices_count is None:
            self.infoMessage.emit("Scan", "TSCAN API returned no data.")
            self._devices = []
            self._device_indices = []
            self.devicesChanged.emit()
            self._selected_device_index = -1
            self.selectedDeviceIndexChanged.emit()
            self._refresh_device_info()
            return

        count = int(getattr(devices_count, "value", 0) or 0)
        count = max(count, 0)

        self._device_indices = list(range(count))
        labels: list[str] = []

        for hw_index in self._device_indices:
            manufacturer = ""
            product = ""
            serial = ""

            try:
                self._can.update_device_info(hw_index)
                info = self._can.device_info
                manufacturer = self._decode_bytes(getattr(info.manufacturer, "value", None))
                product = self._decode_bytes(getattr(info.product, "value", None))
                serial = self._decode_bytes(getattr(info.serial, "value", None))
            except Exception:
                # Keep scan resilient even if one adapter fails info query.
                pass

            base_name = product or manufacturer or "CAN adapter"
            label = f"{hw_index}: {base_name}"
            if serial:
                label += f" [{serial}]"

            labels.append(label)

        self._devices = labels
        self.devicesChanged.emit()

        if self._selected_device_index >= len(self._devices):
            self._selected_device_index = -1

        if self._selected_device_index == -1 and self._devices:
            self._selected_device_index = 0

        self.selectedDeviceIndexChanged.emit()
        self._refresh_device_info()

        if count == 0:
            self.infoMessage.emit("Scan", "No CAN adapters found.")
        else:
            self.infoMessage.emit("Scan", f"Found {count} CAN adapter(s).")

    @Slot(int)
    def setSelectedDeviceIndex(self, index):
        if index < 0 or index >= len(self._devices):
            return

        if self._selected_device_index == index:
            return

        self._selected_device_index = index
        self.selectedDeviceIndexChanged.emit()
        self._refresh_device_info()

    @Slot()
    def toggleConnection(self):
        if self._can.is_connect:
            self._can.disconnect_device()
            self._can.stop_trace()
            self._device_handle = ""
            self.deviceInfoChanged.emit()
            self.connectionStateChanged.emit()
            self.traceStateChanged.emit()
            return

        hw_index = self._selected_hw_index()
        if hw_index < 0:
            self.infoMessage.emit("Connection", "Select a CAN device first.")
            return

        handle = self._can.connect_to(hw_index)
        if handle is None or handle.value == 0:
            self.infoMessage.emit("Connection", "Failed to connect to CAN device.")
        else:
            self._device_handle = str(handle.value)
            self._refresh_device_info()

        self.connectionStateChanged.emit()
        self.traceStateChanged.emit()

    @Slot(int, int, bool)
    def toggleTrace(self, channel_index, baud_rate, terminator):
        if not self._can.is_connect:
            self.infoMessage.emit("Trace", "Connect CAN device first.")
            return

        if self._can.is_trace:
            self._can.stop_trace()
        else:
            self._can.start_trace(channel_index, baud_rate, terminator)

        self.traceStateChanged.emit()

    @Slot(str)
    def loadFirmware(self, path_or_url):
        file_path = self._to_local_path(path_or_url)
        if not file_path:
            self.infoMessage.emit("Firmware", "No file selected.")
            return

        if self._firmware_loading:
            self.infoMessage.emit("Firmware", "Загрузка BIN файла уже выполняется. Подождите.")
            return

        # Update UI path immediately after selection, even before file validation.
        self._firmware_path = str(Path(file_path))
        self.firmwarePathChanged.emit()

        self._set_firmware_loading(True)
        self._append_log("Чтение BIN файла...", RowColor.blue)
        self.infoMessage.emit("Firmware", "BIN файл выбран. Идет загрузка...")

        # Defer actual worker start to the next event loop turn so UI updates instantly.
        QTimer.singleShot(0, lambda p=file_path: self._start_firmware_loading(p))

    @Slot()
    def startProgramming(self):
        self._set_programming_active(True)
        if not self._bootloader.start():
            self._set_programming_active(False)

    @Slot()
    def checkState(self):
        self._bootloader.check_state()

    @Slot()
    def resetToBootloader(self):
        self._bootloader.ecu_uds_reset()

    @Slot()
    def resetToMainProgram(self):
        self._bootloader.ecu_software_reset()

    @Slot()
    def clearLogs(self):
        self._logs = []
        self.logsChanged.emit()

    def _on_bootloader_state(self, text, color):
        self._append_log(text, color)

    def _on_data_sent(self, value):
        clamped_value = min(max(value, 0), self._progress_max)
        if self._progress_value == clamped_value:
            return
        self._progress_value = clamped_value
        self.progressChanged.emit()

    def _on_programming_finished(self, success):
        self._set_programming_active(False)
        if success:
            self._progress_value = self._progress_max
            self.progressChanged.emit()
            self.infoMessage.emit("Programming", "Firmware uploaded successfully.")

    def _on_trace_state_event(self):
        self.traceStateChanged.emit()

    @Slot(str, bool, bytes, str)
    def _on_firmware_loaded(self, _file_path, success, binary_content, error_text):
        try:
            if not success:
                self._append_log("Ошибка загрузки BIN файла", RowColor.red)
                self.infoMessage.emit("Firmware", error_text if error_text else "Не удалось открыть BIN файл.")
                return

            self._bootloader.set_firmware(binary_content)

            file_size = len(binary_content)
            self._progress_max = max(file_size, 1)
            self._progress_value = 0
            self.progressChanged.emit()

            self._append_log(f"BIN файл загружен ({file_size} байт)", RowColor.green)
            self.infoMessage.emit("Firmware", f"BIN файл успешно загружен. Размер: {file_size} байт.")
        finally:
            self._set_firmware_loading(False)

    def _start_firmware_loading(self, file_path: str):
        self._firmware_loader_thread = QThread(self)
        self._firmware_loader_worker = FirmwareLoadWorker(file_path)
        self._firmware_loader_worker.moveToThread(self._firmware_loader_thread)

        self._firmware_loader_thread.started.connect(self._firmware_loader_worker.run)
        self._firmware_loader_worker.finished.connect(self._on_firmware_loaded)
        self._firmware_loader_worker.finished.connect(self._firmware_loader_thread.quit)
        self._firmware_loader_worker.finished.connect(self._firmware_loader_worker.deleteLater)
        self._firmware_loader_thread.finished.connect(self._firmware_loader_thread.deleteLater)
        self._firmware_loader_thread.finished.connect(self._clear_firmware_loader)
        self._firmware_loader_thread.start()

    def _clear_firmware_loader(self):
        self._firmware_loader_thread = None
        self._firmware_loader_worker = None

    def _refresh_device_info(self):
        hw_index = self._selected_hw_index()
        if hw_index < 0:
            self._manufacturer = ""
            self._product = ""
            self._serial = ""
            self.deviceInfoChanged.emit()
            return

        self._can.update_device_info(hw_index)
        info = self._can.device_info

        self._manufacturer = self._decode_bytes(getattr(info.manufacturer, "value", None))
        self._product = self._decode_bytes(getattr(info.product, "value", None))
        self._serial = self._decode_bytes(getattr(info.serial, "value", None))
        self.deviceInfoChanged.emit()

    def _selected_hw_index(self) -> int:
        if self._selected_device_index < 0 or self._selected_device_index >= len(self._device_indices):
            return -1
        return self._device_indices[self._selected_device_index]

    @staticmethod
    def _decode_bytes(raw_value):
        if raw_value is None:
            return ""
        if isinstance(raw_value, bytes):
            try:
                return raw_value.decode("utf-8")
            except UnicodeDecodeError:
                return raw_value.decode("cp1251", errors="ignore")
        return str(raw_value)

    @staticmethod
    def _to_local_path(path_or_url):
        if not path_or_url:
            return ""

        if isinstance(path_or_url, QUrl):
            parsed = path_or_url
        else:
            parsed = QUrl(path_or_url)

        if parsed.isLocalFile():
            return parsed.toLocalFile()

        if parsed.scheme() == "file":
            return parsed.toLocalFile()

        return str(path_or_url)

    def _set_programming_active(self, active):
        if self._programming_active == active:
            return
        self._programming_active = active
        self.programmingActiveChanged.emit()

    def _set_firmware_loading(self, loading):
        value = bool(loading)
        if self._firmware_loading == value:
            return
        self._firmware_loading = value
        self.firmwareLoadingChanged.emit()

    def _append_log(self, text, color):
        if isinstance(color, QColor):
            color_value = color.name()
        else:
            color_value = "#cbd5e1"

        self._logs.append(
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "text": str(text),
                "color": color_value,
            }
        )

        if len(self._logs) > 2000:
            self._logs = self._logs[-2000:]

        self.logsChanged.emit()

        if self._programming_active and isinstance(color, QColor) and color == RowColor.red:
            self._set_programming_active(False)
