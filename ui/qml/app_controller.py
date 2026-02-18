from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
import time

from PySide6.QtCore import QObject, Property, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor

from app_can.CanDevice import CanDevice
from colors import RowColor
from j1939.j1939_can_identifier import J1939CanIdentifier
from uds.bootloader import Bootloader
from uds.firmware import Firmware, FirmwareState
from uds.uds_identifiers import UdsIdentifiers

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
    CAN_FILTER_FIELDS = ("time", "dir", "frameId", "pgn", "src", "dst", "j1939", "dlc", "uds", "data")

    devicesChanged = Signal()
    selectedDeviceIndexChanged = Signal()
    deviceInfoChanged = Signal()
    connectionStateChanged = Signal()
    traceStateChanged = Signal()
    firmwarePathChanged = Signal()
    progressChanged = Signal()
    logsChanged = Signal()
    canTrafficLogsChanged = Signal()
    canFilterOptionsChanged = Signal()
    infoMessage = Signal(str, str)
    programmingActiveChanged = Signal()
    debugEnabledChanged = Signal()
    firmwareLoadingChanged = Signal()
    transferByteOrderIndexChanged = Signal()
    sourceAddressTextChanged = Signal()
    sourceAddressBusyChanged = Signal()
    sourceAddressOperationChanged = Signal()
    udsIdentifiersChanged = Signal()
    observedUdsCandidateChanged = Signal()

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
        self._can_traffic_logs: list[dict[str, str]] = []
        self._filtered_can_traffic_logs: list[dict[str, str]] = []
        self._can_filter_values: dict[str, str] = {field: "" for field in self.CAN_FILTER_FIELDS}
        self._can_filter_options: dict[str, list[str]] = {field: [] for field in self.CAN_FILTER_FIELDS}
        self._can_filter_option_seen: dict[str, set[str]] = {field: set() for field in self.CAN_FILTER_FIELDS}
        self._can_filter_option_limits: dict[str, int] = {
            "time": 60,
            "dir": 10,
            "frameId": 120,
            "pgn": 120,
            "src": 120,
            "dst": 120,
            "j1939": 120,
            "dlc": 20,
            "uds": 120,
            "data": 80,
        }
        self._programming_active = False
        self._debug_enabled = False
        self._firmware_loading = False
        self._transfer_byte_order_index = 0
        self._source_address_text = f"0x{UdsIdentifiers.rx.src:02X}"
        self._source_address_busy = False
        self._source_address_operation = ""

        self._tx_priority_text = ""
        self._tx_pgn_text = ""
        self._tx_src_text = ""
        self._tx_dst_text = ""
        self._tx_identifier_text = ""
        self._rx_priority_text = ""
        self._rx_pgn_text = ""
        self._rx_src_text = ""
        self._rx_dst_text = ""
        self._rx_identifier_text = ""
        self._observed_node_stats: dict[int, dict[str, object]] = {}
        self._observed_candidate_order: list[int] = []
        self._observed_candidate_values: list[int] = []
        self._observed_candidate_items: list[str] = []
        self._observed_candidate_index = -1
        self._observed_frame_seq = 0
        self._observed_uds_text = "Ожидание входящих J1939 RX кадров для автоопределения адреса..."
        self._perf_origin = time.perf_counter()
        self._wall_origin = time.time()
        self._rx_time_anchor_raw: float | None = None
        self._rx_time_anchor_wall: float | None = None

        self._refresh_uds_identifier_texts(emit_signal=False)

        self._firmware_loader_thread: QThread | None = None
        self._firmware_loader_worker: FirmwareLoadWorker | None = None

        self._bootloader.signal_new_state.connect(self._on_bootloader_state)
        self._bootloader.signal_data_sent.connect(self._on_data_sent)
        self._bootloader.signal_finished.connect(self._on_programming_finished)
        self._bootloader.signal_source_address_applied.connect(self._on_source_address_applied)
        self._bootloader.signal_source_address_read.connect(self._on_source_address_read)

        self._can.signal_new_message.connect(self._on_can_message)
        self._can.signal_tracing_started.connect(self._on_trace_state_event)
        self._can.signal_tracing_stopped.connect(self._on_trace_state_event)

        self._can_filter_rebuild_timer = QTimer(self)
        self._can_filter_rebuild_timer.setSingleShot(True)
        self._can_filter_rebuild_timer.setInterval(90)
        self._can_filter_rebuild_timer.timeout.connect(self._rebuild_can_traffic_view)

        self._rebuild_can_traffic_view()

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

    @Property("QVariantList", notify=canTrafficLogsChanged)
    def canTrafficLogs(self):
        return self._can_traffic_logs

    @Property("QVariantList", notify=canTrafficLogsChanged)
    def filteredCanTrafficLogs(self):
        return self._filtered_can_traffic_logs

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterTimeOptions(self):
        return self._can_filter_options.get("time", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterDirOptions(self):
        return self._can_filter_options.get("dir", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterIdOptions(self):
        return self._can_filter_options.get("frameId", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterPgnOptions(self):
        return self._can_filter_options.get("pgn", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterSrcOptions(self):
        return self._can_filter_options.get("src", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterDstOptions(self):
        return self._can_filter_options.get("dst", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterJ1939Options(self):
        return self._can_filter_options.get("j1939", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterDlcOptions(self):
        return self._can_filter_options.get("dlc", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterUdsOptions(self):
        return self._can_filter_options.get("uds", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterDataOptions(self):
        return self._can_filter_options.get("data", [])

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

    @Property(str, notify=sourceAddressTextChanged)
    def sourceAddressText(self):
        return self._source_address_text

    @Property(bool, notify=sourceAddressBusyChanged)
    def sourceAddressBusy(self):
        return self._source_address_busy

    @Property(str, notify=sourceAddressOperationChanged)
    def sourceAddressOperation(self):
        return self._source_address_operation

    @Property(str, notify=udsIdentifiersChanged)
    def txPriorityText(self):
        return self._tx_priority_text

    @Property(str, notify=udsIdentifiersChanged)
    def txPgnText(self):
        return self._tx_pgn_text

    @Property(str, notify=udsIdentifiersChanged)
    def txSrcText(self):
        return self._tx_src_text

    @Property(str, notify=udsIdentifiersChanged)
    def txDstText(self):
        return self._tx_dst_text

    @Property(str, notify=udsIdentifiersChanged)
    def txIdentifierText(self):
        return self._tx_identifier_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxPriorityText(self):
        return self._rx_priority_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxPgnText(self):
        return self._rx_pgn_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxSrcText(self):
        return self._rx_src_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxDstText(self):
        return self._rx_dst_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxIdentifierText(self):
        return self._rx_identifier_text

    @Property(bool, notify=observedUdsCandidateChanged)
    def observedUdsCandidateAvailable(self):
        return 0 <= self._observed_candidate_index < len(self._observed_candidate_values)

    @Property(str, notify=observedUdsCandidateChanged)
    def observedUdsCandidateText(self):
        return self._observed_uds_text

    @Property("QStringList", notify=observedUdsCandidateChanged)
    def observedUdsCandidates(self):
        return self._observed_candidate_items

    @Property(int, notify=observedUdsCandidateChanged)
    def selectedObservedUdsCandidateIndex(self):
        return self._observed_candidate_index

    @Slot(bool)
    def setDebugEnabled(self, enabled):
        value = bool(enabled)
        if self._debug_enabled == value:
            return
        self._debug_enabled = value
        self.debugEnabledChanged.emit()
        self.infoMessage.emit("Отладка", "Режим отладки включен." if value else "Режим отладки отключен.")

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
        self._append_log(f"Выбран порядок байтов: {label}", QColor("#0ea5e9"))
        self.infoMessage.emit("Протокол", f"Выбран порядок байтов: {label}.")

    @Slot(str)
    def setSourceAddressText(self, text):
        value = str(text).strip()
        if self._source_address_text == value:
            return
        self._source_address_text = value
        self.sourceAddressTextChanged.emit()

    @Slot(str)
    def applySourceAddress(self, text):
        if self._source_address_busy:
            self.infoMessage.emit("Протокол", "Изменение Source Address уже выполняется.")
            return

        if self._programming_active:
            self.infoMessage.emit("Протокол", "Нельзя менять Source Address во время программирования.")
            return

        try:
            source_address = self._parse_source_address(text)
        except ValueError:
            self.infoMessage.emit("Протокол", "Некорректный Source Address. Допустимо 0..255 или 0x00..0xFF.")
            return

        self._set_source_address_operation("write")
        self._set_source_address_busy(True)
        if not self._bootloader.write_can_source_address(source_address):
            self._set_source_address_busy(False)
            self.infoMessage.emit("Протокол", "Не удалось отправить запрос на изменение Source Address.")
            return

        self._source_address_text = f"0x{source_address:02X}"
        self.sourceAddressTextChanged.emit()

    @Slot()
    def readSourceAddress(self):
        if self._source_address_busy:
            self.infoMessage.emit("Протокол", "Операция с Source Address уже выполняется.")
            return

        if self._programming_active:
            self.infoMessage.emit("Протокол", "Нельзя читать Source Address во время программирования.")
            return

        self._set_source_address_operation("read")
        self._set_source_address_busy(True)
        if not self._bootloader.read_can_source_address():
            self._set_source_address_busy(False)
            self.infoMessage.emit("Протокол", "Не удалось отправить запрос на чтение Source Address.")

    @Slot()
    def refreshUdsIdentifiers(self):
        self._refresh_uds_identifier_texts()
        if len(self._observed_candidate_values) > 0:
            self._rebuild_observed_candidate_list()

    @Slot()
    def applyObservedUdsIdentifiers(self):
        if self._programming_active:
            self.infoMessage.emit("Протокол", "Нельзя менять UDS идентификаторы во время программирования.")
            return

        if self._source_address_busy:
            self.infoMessage.emit("Протокол", "Подождите завершения операции Source Address.")
            return

        if not (0 <= self._observed_candidate_index < len(self._observed_candidate_values)):
            self.infoMessage.emit("Протокол", "Нет кандидатов из RX J1939 потока для автоопределения адреса.")
            return

        device_sa = int(self._observed_candidate_values[self._observed_candidate_index]) & 0xFF
        node = self._observed_node_stats.get(device_sa, {})
        tester_sa, _ = self._choose_tester_sa_for_node(node, int(UdsIdentifiers.tx.src) & 0xFF)
        tester_sa = int(tester_sa) & 0xFF

        UdsIdentifiers.tx.src = tester_sa
        UdsIdentifiers.tx.dst = device_sa
        UdsIdentifiers.rx.src = device_sa
        UdsIdentifiers.rx.dst = tester_sa

        self._source_address_text = f"0x{UdsIdentifiers.rx.src:02X}"
        self.sourceAddressTextChanged.emit()
        self._refresh_uds_identifier_texts()

        self.infoMessage.emit(
            "Протокол",
            (
                f"Идентификаторы обновлены из RX потока: "
                f"SA устройства=0x{device_sa:02X}, SA тестера=0x{tester_sa:02X}."
            ),
        )

    @Slot()
    def resetObservedUdsCandidate(self):
        self._reset_observed_uds_candidate()

    @Slot(int)
    def setSelectedObservedUdsCandidateIndex(self, index):
        try:
            new_index = int(index)
        except (TypeError, ValueError):
            return

        if new_index < 0 or new_index >= len(self._observed_candidate_values):
            return

        if self._observed_candidate_index == new_index:
            return

        self._observed_candidate_index = new_index
        self._update_observed_candidate_text()
        self.observedUdsCandidateChanged.emit()

    @Slot(str, str, str, str, str, str, str, str)
    def applyUdsIdentifiers(self, tx_priority, tx_pgn, tx_src, tx_dst, rx_priority, rx_pgn, rx_src, rx_dst):
        if self._programming_active:
            self.infoMessage.emit("Протокол", "Нельзя менять UDS идентификаторы во время программирования.")
            return

        if self._source_address_busy:
            self.infoMessage.emit("Протокол", "Подождите завершения операции Source Address.")
            return

        try:
            tx_priority_value = self._parse_uint_field(tx_priority, 0, 0x7, "TX Priority")
            tx_pgn_value = self._parse_uint_field(tx_pgn, 0, 0xFFFF, "TX PGN")
            tx_src_value = self._parse_uint_field(tx_src, 0, 0xFF, "TX Source")
            tx_dst_value = self._parse_uint_field(tx_dst, 0, 0xFF, "TX Destination")

            rx_priority_value = self._parse_uint_field(rx_priority, 0, 0x7, "RX Priority")
            rx_pgn_value = self._parse_uint_field(rx_pgn, 0, 0xFFFF, "RX PGN")
            rx_src_value = self._parse_uint_field(rx_src, 0, 0xFF, "RX Source")
            rx_dst_value = self._parse_uint_field(rx_dst, 0, 0xFF, "RX Destination")
        except ValueError as exc:
            self.infoMessage.emit("Протокол", str(exc))
            return

        UdsIdentifiers.tx.priority = tx_priority_value
        UdsIdentifiers.tx.pgn = tx_pgn_value
        UdsIdentifiers.tx.src = tx_src_value
        UdsIdentifiers.tx.dst = tx_dst_value

        UdsIdentifiers.rx.priority = rx_priority_value
        UdsIdentifiers.rx.pgn = rx_pgn_value
        UdsIdentifiers.rx.src = rx_src_value
        UdsIdentifiers.rx.dst = rx_dst_value

        self._source_address_text = f"0x{UdsIdentifiers.rx.src:02X}"
        self.sourceAddressTextChanged.emit()

        self._refresh_uds_identifier_texts()
        self.infoMessage.emit(
            "Протокол",
            f"UDS идентификаторы обновлены: TX={self._tx_identifier_text}, RX={self._rx_identifier_text}.",
        )

    @Slot(str)
    def debugEvent(self, text):
        if not self._debug_enabled:
            return
        message = str(text)
        LOGGER.info("QML debug: %s", message)
        self._append_log(f"DEBUG: {message}", QColor("#93c5fd"))
        self.infoMessage.emit("РћС‚Р»Р°РґРєР°", message)

    @Slot()
    def scanDevices(self):
        if self._debug_enabled:
            LOGGER.info("scanDevices() called")
        devices_count = self._can.get_devices()
        if devices_count is None:
            self.infoMessage.emit("Сканирование", "TSCAN API не вернул список устройств.")
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

            base_name = product or manufacturer or "CAN-адаптер"
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
            self.infoMessage.emit("Сканирование", "CAN-адаптеры не найдены.")
        else:
            self.infoMessage.emit("Сканирование", f"Найдено CAN-адаптеров: {count}.")

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
            self._reset_observed_uds_candidate()
            self.deviceInfoChanged.emit()
            self.connectionStateChanged.emit()
            self.traceStateChanged.emit()
            return

        hw_index = self._selected_hw_index()
        if hw_index < 0:
            self.infoMessage.emit("Подключение", "Выберите устройство CAN-адаптера.")
            return

        handle = self._can.connect_to(hw_index)
        if handle is None or handle.value == 0:
            self.infoMessage.emit("Подключение", "Не удалось подключиться к CAN-адаптеру.")
        else:
            self._device_handle = str(handle.value)
            self._refresh_device_info()

        self.connectionStateChanged.emit()
        self.traceStateChanged.emit()

    @Slot(int, int, bool)
    def toggleTrace(self, channel_index, baud_rate, terminator):
        if not self._can.is_connect:
            self.infoMessage.emit("Подключение", "Сначала подключите CAN-адаптер.")
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
            self.infoMessage.emit("Прошивка", "Путь не выбран.")
            return

        if self._firmware_loading:
            self.infoMessage.emit("Прошивка", "Загрузка BIN файла уже выполняется. Подождите.")
            return

        # Update UI path immediately after selection, even before file validation.
        self._firmware_path = str(Path(file_path))
        self.firmwarePathChanged.emit()

        self._set_firmware_loading(True)
        self._append_log("Чтение BIN файла...", RowColor.blue)
        self.infoMessage.emit("Прошивка", "BIN файл выбран. Идет загрузка...")

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

    @Slot()
    def clearCanTrafficLogs(self):
        if self._can_filter_rebuild_timer.isActive():
            self._can_filter_rebuild_timer.stop()
        self._can_traffic_logs = []
        self._rebuild_can_traffic_view()

    @Slot(str, str)
    def setCanTrafficFilter(self, field, value):
        key = str(field or "").strip()
        if key not in self._can_filter_values:
            return

        text = str(value or "").strip()
        if self._can_filter_values.get(key, "") == text:
            return

        self._can_filter_values[key] = text
        self._schedule_can_traffic_rebuild(restart=True)

    @Slot()
    def resetCanTrafficFilters(self):
        updated = False
        for field in self.CAN_FILTER_FIELDS:
            if self._can_filter_values.get(field):
                self._can_filter_values[field] = ""
                updated = True
        if updated:
            self._schedule_can_traffic_rebuild(restart=True)

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
            self.infoMessage.emit("Программирование", "Программирование успешно завершено.")

    def _on_trace_state_event(self):
        self._rx_time_anchor_raw = None
        self._rx_time_anchor_wall = None
        self.traceStateChanged.emit()

    @Slot(str, str, str, str, list)
    def _on_can_message(self, msg_time, msg_id, msg_dir, msg_dlc, msg_data):
        try:
            identifier = int(str(msg_id), 0)
        except (TypeError, ValueError):
            identifier = 0

        direction = self._normalize_can_direction(msg_dir)
        payload = []
        if isinstance(msg_data, list):
            for value in msg_data:
                try:
                    payload.append(int(value) & 0xFF)
                except (TypeError, ValueError):
                    continue

        data_hex = " ".join(f"{byte:02X}" for byte in payload)
        formatted_time = self._format_can_time(msg_time, direction)

        pgn_text = "-"
        src_text = "-"
        dst_text = "-"
        j1939_text = "-"
        parsed_id = None
        try:
            parsed_id = J1939CanIdentifier(int(identifier))
            parsed_pgn = int(parsed_id.pgn) & 0x3FFFF
            parsed_src = int(parsed_id.src) & 0xFF
            parsed_dst = int(parsed_id.dst) & 0xFF

            pgn_text = f"0x{parsed_pgn & 0xFFFF:04X}"
            src_text = f"0x{parsed_src:02X}"
            dst_text = f"0x{parsed_dst:02X}"
            app_summary = self._parse_j1939_application_summary(parsed_pgn, payload)
            if app_summary:
                j1939_text = app_summary
        except Exception:
            pass

        uds_text = "-"
        is_uds_frame = self._is_uds_identifier(identifier)
        if (not is_uds_frame) and parsed_id is not None:
            is_uds_frame = self._is_uds_diagnostic_pgn(int(parsed_id.pgn))
        if is_uds_frame:
            uds_text = self._parse_isotp_summary(payload)

        if direction == "RX" and parsed_id is not None:
            self._update_observed_uds_candidate(parsed_id)

        if direction == "TX":
            dir_color = "#1d4ed8"
            dir_bg = "#dbeafe"
            dir_border = "#93c5fd"
        elif direction == "RX":
            dir_color = "#15803d"
            dir_bg = "#dcfce7"
            dir_border = "#86efac"
        else:
            dir_color = "#334155"
            dir_bg = "#e2e8f0"
            dir_border = "#cbd5e1"

        row = {
            "time": formatted_time,
            "dir": direction,
            "frameId": f"0x{int(identifier) & 0x1FFFFFFF:08X}",
            "pgn": pgn_text,
            "src": src_text,
            "dst": dst_text,
            "j1939": j1939_text,
            "dlc": str(msg_dlc),
            "uds": uds_text,
            "data": data_hex,
            "dirColor": dir_color,
            "dirBg": dir_bg,
            "dirBorder": dir_border,
        }
        self._append_can_traffic_entry(row)

    @staticmethod
    def _normalize_can_direction(direction) -> str:
        raw = str(direction).strip().upper()
        if raw.startswith("T"):
            return "TX"
        if raw.startswith("R"):
            return "RX"
        return raw or "-"

    def _format_can_time(self, raw_time, direction: str) -> str:
        raw_text = str(raw_time).strip()
        try:
            value = float(raw_text)
        except (TypeError, ValueError):
            return raw_text

        # Unix epoch in seconds.
        if value >= 946684800.0:
            try:
                return datetime.fromtimestamp(value).strftime("%H:%M:%S.%f")[:-3]
            except Exception:
                return raw_text

        if direction == "RX":
            if (self._rx_time_anchor_raw is None) or (value < (self._rx_time_anchor_raw - 0.001)):
                self._rx_time_anchor_raw = value
                self._rx_time_anchor_wall = time.time()

            anchor_raw = self._rx_time_anchor_raw if self._rx_time_anchor_raw is not None else value
            anchor_wall = self._rx_time_anchor_wall if self._rx_time_anchor_wall is not None else time.time()
            wall_ts = anchor_wall + (value - anchor_raw)
        else:
            # TX timestamp comes from perf_counter().
            wall_ts = self._wall_origin + (value - self._perf_origin)

        try:
            return datetime.fromtimestamp(wall_ts).strftime("%H:%M:%S.%f")[:-3]
        except Exception:
            return raw_text

    @staticmethod
    def _parse_isotp_summary(payload: list[int]) -> str:
        if not payload:
            return "-"

        pci_type = (payload[0] >> 4) & 0x0F
        if pci_type == 0x0:
            data_len = payload[0] & 0x0F
            if len(payload) > 1:
                sid = payload[1] & 0xFF
                if sid == 0x7F and len(payload) > 3:
                    return f"SF NRC=0x{payload[3] & 0xFF:02X} SID=0x{payload[2] & 0xFF:02X}"
                return f"SF LEN={data_len} SID=0x{sid:02X}"
            return f"SF LEN={data_len}"

        if pci_type == 0x1:
            total_len = ((payload[0] & 0x0F) << 8) | (payload[1] & 0xFF if len(payload) > 1 else 0)
            if len(payload) > 2:
                return f"FF LEN={total_len} SID=0x{payload[2] & 0xFF:02X}"
            return f"FF LEN={total_len}"

        if pci_type == 0x2:
            return f"CF SN={payload[0] & 0x0F}"

        if pci_type == 0x3:
            flow_status = payload[0] & 0x0F
            flow_labels = {0: "CTS", 1: "WAIT", 2: "OVFLW"}
            block_size = payload[1] & 0xFF if len(payload) > 1 else 0
            st_min = payload[2] & 0xFF if len(payload) > 2 else 0
            return f"FC {flow_labels.get(flow_status, 'UNK')} BS={block_size} ST=0x{st_min:02X}"

        return f"ISO-TP PCI=0x{pci_type:X}"

    @staticmethod
    def _parse_j1939_application_summary(pgn: int, payload: list[int]) -> str:
        if not payload:
            return ""

        # PGN 0xFEFC: fuel level, byte[1], scale 0.4%/bit.
        if int(pgn) == 0xFEFC and len(payload) > 1:
            raw = int(payload[1]) & 0xFF
            if raw >= 0xFE:
                return f"FuelLevel=N/A raw=0x{raw:02X}"
            return f"FuelLevel={raw * 0.4:.1f}% raw=0x{raw:02X}"

        # PGN 0xFDA2: temperature, byte[4], offset -40 C.
        if int(pgn) == 0xFDA2 and len(payload) > 4:
            raw = int(payload[4]) & 0xFF
            if raw >= 0xFE:
                return f"Temperature=N/A raw=0x{raw:02X}"
            return f"Temperature={raw - 40}C raw=0x{raw:02X}"

        return ""

    def _append_can_traffic_entry(self, row: dict[str, str]):
        self._can_traffic_logs.append(row)
        self._update_can_filter_options_with_row(row)
        hard_limit = 5000
        keep_tail = 1500
        if len(self._can_traffic_logs) > hard_limit:
            self._can_traffic_logs = self._can_traffic_logs[-keep_tail:]
            self._can_traffic_logs.insert(
                0,
                {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "dir": "SYS",
                    "frameId": "-",
                    "pgn": "-",
                    "src": "-",
                    "dst": "-",
                    "j1939": "-",
                    "dlc": "-",
                    "uds": "Автоочистка журнала",
                    "data": f"Оставлены последние {keep_tail} записей",
                    "dirColor": "#334155",
                    "dirBg": "#e2e8f0",
                    "dirBorder": "#cbd5e1",
                },
            )
        self._schedule_can_traffic_rebuild()

    def _schedule_can_traffic_rebuild(self, restart: bool = False):
        if self._can_filter_rebuild_timer.isActive():
            if restart:
                self._can_filter_rebuild_timer.stop()
                self._can_filter_rebuild_timer.start()
            return
        self._can_filter_rebuild_timer.start()

    def _rebuild_can_traffic_view(self):
        normalized_filters: dict[str, str] = {}
        for field in self.CAN_FILTER_FIELDS:
            normalized_filters[field] = str(self._can_filter_values.get(field, "")).strip().lower()

        has_filters = any(bool(value) for value in normalized_filters.values())
        if not has_filters:
            self._filtered_can_traffic_logs = list(self._can_traffic_logs)
        else:
            filtered: list[dict[str, str]] = []
            for row in self._can_traffic_logs:
                match = True
                for field, filter_value in normalized_filters.items():
                    if not filter_value:
                        continue
                    value = str(row.get(field, "")).lower()
                    if filter_value not in value:
                        match = False
                        break
                if match:
                    filtered.append(row)
            self._filtered_can_traffic_logs = filtered

        self.canTrafficLogsChanged.emit()

    def _normalize_filter_option_value(self, field: str, value: str) -> str:
        text = str(value or "").strip()
        if (not text) or text == "-":
            return ""

        if field == "time":
            # For options keep second precision to avoid flooding by unique milliseconds.
            if len(text) >= 8 and text[2] == ":" and text[5] == ":":
                return text[:8]
            return text

        if field == "data":
            # Keep first bytes as stable prefix for easier selection.
            parts = text.split()
            if len(parts) > 8:
                return " ".join(parts[:8])
            return text

        return text

    def _update_can_filter_options_with_row(self, row: dict[str, str]):
        changed = False
        for field in self.CAN_FILTER_FIELDS:
            value = self._normalize_filter_option_value(field, row.get(field, ""))
            if not value:
                continue

            seen = self._can_filter_option_seen[field]
            if value in seen:
                continue

            limit = int(self._can_filter_option_limits.get(field, 120))
            values = self._can_filter_options[field]
            if len(values) >= limit:
                continue

            seen.add(value)
            values.append(value)
            changed = True

        if changed:
            self.canFilterOptionsChanged.emit()

    @staticmethod
    def _is_uds_identifier(identifier: int) -> bool:
        try:
            parsed = J1939CanIdentifier(int(identifier))
            pgn = int(parsed.pgn) & 0x3FFFF
            return pgn in (int(UdsIdentifiers.tx.pgn) & 0x3FFFF, int(UdsIdentifiers.rx.pgn) & 0x3FFFF)
        except Exception:
            return False

    @staticmethod
    def _is_uds_diagnostic_pgn(pgn: int) -> bool:
        return ((int(pgn) >> 8) & 0xFF) == 0xDA

    @Slot(int, bool)
    def _on_source_address_applied(self, source_address, success):
        self._set_source_address_busy(False)
        if success:
            self._source_address_text = f"0x{int(source_address) & 0xFF:02X}"
            self.sourceAddressTextChanged.emit()
            self._refresh_uds_identifier_texts()
            self.infoMessage.emit("Протокол", f"Source Address изменен: {self._source_address_text}.")
        else:
            self._source_address_text = f"0x{UdsIdentifiers.rx.src:02X}"
            self.sourceAddressTextChanged.emit()
            self._refresh_uds_identifier_texts()
            self.infoMessage.emit("Протокол", "Не удалось применить Source Address.")

    @Slot(int, bool)
    def _on_source_address_read(self, source_address, success):
        self._set_source_address_busy(False)
        if success:
            self._source_address_text = f"0x{int(source_address) & 0xFF:02X}"
            self.sourceAddressTextChanged.emit()
            self._refresh_uds_identifier_texts()
            self.infoMessage.emit("Протокол", f"Source Address считан: {self._source_address_text}.")
        else:
            self.infoMessage.emit("Протокол", "Не удалось прочитать Source Address.")

    @Slot(str, bool, bytes, str)
    def _on_firmware_loaded(self, _file_path, success, binary_content, error_text):
        try:
            if not success:
                self._append_log("Ошибка загрузки BIN файла", RowColor.red)
                self.infoMessage.emit("Прошивка", error_text if error_text else "Не удалось открыть BIN файл.")
                return

            self._bootloader.set_firmware(binary_content)

            file_size = len(binary_content)
            self._progress_max = max(file_size, 1)
            self._progress_value = 0
            self.progressChanged.emit()

            self._append_log(f"BIN файл загружен ({file_size} байт)", RowColor.green)
            self.infoMessage.emit("Прошивка", f"BIN файл успешно загружен. Размер: {file_size} байт.")
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
    def _parse_uint_field(text, minimum: int, maximum: int, field_name: str) -> int:
        raw = str(text).strip()
        if not raw:
            raise ValueError(f"Поле '{field_name}' не заполнено.")

        base = 16 if raw.lower().startswith("0x") else 10
        try:
            value = int(raw, base)
        except ValueError as exc:
            raise ValueError(f"Поле '{field_name}' содержит некорректное число.") from exc

        if value < minimum or value > maximum:
            raise ValueError(f"Поле '{field_name}' вне диапазона {minimum}..{maximum}.")

        return value

    def _refresh_uds_identifier_texts(self, emit_signal: bool = True):
        tx = UdsIdentifiers.tx
        rx = UdsIdentifiers.rx

        self._tx_priority_text = str(int(tx.priority) & 0x7)
        self._tx_pgn_text = f"0x{int(tx.pgn) & 0xFFFF:04X}"
        self._tx_src_text = f"0x{int(tx.src) & 0xFF:02X}"
        self._tx_dst_text = f"0x{int(tx.dst) & 0xFF:02X}"
        self._tx_identifier_text = f"0x{int(tx.identifier) & 0x1FFFFFFF:08X}"

        self._rx_priority_text = str(int(rx.priority) & 0x7)
        self._rx_pgn_text = f"0x{int(rx.pgn) & 0xFFFF:04X}"
        self._rx_src_text = f"0x{int(rx.src) & 0xFF:02X}"
        self._rx_dst_text = f"0x{int(rx.dst) & 0xFF:02X}"
        self._rx_identifier_text = f"0x{int(rx.identifier) & 0x1FFFFFFF:08X}"

        if emit_signal:
            self.udsIdentifiersChanged.emit()

    @staticmethod
    def _parse_source_address(text):
        raw = str(text).strip()
        if not raw:
            raise ValueError("Empty Source Address")

        base = 16 if raw.lower().startswith("0x") else 10
        value = int(raw, base)
        if value < 0 or value > 0xFF:
            raise ValueError("Source Address out of range")
        return value

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

    def _set_source_address_busy(self, busy):
        value = bool(busy)
        if self._source_address_busy == value:
            return
        self._source_address_busy = value
        if not value:
            self._set_source_address_operation("")
        self.sourceAddressBusyChanged.emit()

    def _set_source_address_operation(self, operation: str):
        value = str(operation).strip().lower()
        if value not in ("", "read", "write"):
            value = ""
        if self._source_address_operation == value:
            return
        self._source_address_operation = value
        self.sourceAddressOperationChanged.emit()

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

    @staticmethod
    def _choose_tester_sa_for_node(node: dict[str, object], default_tester_sa: int) -> tuple[int, int]:
        votes = node.get("tester_votes", {}) if isinstance(node, dict) else {}
        if not isinstance(votes, dict) or len(votes) == 0:
            return int(default_tester_sa) & 0xFF, 0
        best_sa, best_count = max(votes.items(), key=lambda item: int(item[1]))
        return int(best_sa) & 0xFF, int(best_count)

    def _rebuild_observed_candidate_list(self):
        previous_items = list(self._observed_candidate_items)
        previous_values = list(self._observed_candidate_values)
        previous_index = self._observed_candidate_index
        previous_text = self._observed_uds_text

        current_selected_sa = None
        if 0 <= previous_index < len(previous_values):
            current_selected_sa = int(previous_values[previous_index]) & 0xFF

        # Stable append-only ordering for UI list: existing order is kept,
        # new addresses are appended and never reshuffled by live counters.
        known_stats = self._observed_node_stats
        stable_order: list[int] = []
        seen_sa: set[int] = set()

        for sa in self._observed_candidate_order:
            device_sa = int(sa) & 0xFF
            if device_sa in seen_sa:
                continue
            if device_sa in known_stats:
                stable_order.append(device_sa)
                seen_sa.add(device_sa)

        for sa in sorted(int(key) & 0xFF for key in known_stats.keys()):
            if sa in seen_sa:
                continue
            stable_order.append(sa)
            seen_sa.add(sa)

        self._observed_candidate_order = stable_order

        default_tester_sa = int(UdsIdentifiers.tx.src) & 0xFF
        new_values: list[int] = []
        new_items: list[str] = []
        for device_sa in stable_order:
            node = known_stats.get(device_sa, {})
            total_count = int(node.get("total", 0))
            uds_count = int(node.get("uds", 0))
            guessed_tester_sa, _ = self._choose_tester_sa_for_node(node, default_tester_sa)
            label = (
                f"Устройство 0x{device_sa:02X}  |  RX: {total_count}  |  UDS: {uds_count}  |  Тестер: 0x{guessed_tester_sa:02X}"
            )
            new_values.append(device_sa)
            new_items.append(label)

        self._observed_candidate_values = new_values
        self._observed_candidate_items = new_items

        if len(new_values) == 0:
            self._observed_candidate_index = -1
        elif current_selected_sa is not None and current_selected_sa in new_values:
            self._observed_candidate_index = new_values.index(current_selected_sa)
        elif 0 <= previous_index < len(new_values):
            self._observed_candidate_index = previous_index
        else:
            self._observed_candidate_index = 0

        self._update_observed_candidate_text()

        if (
            previous_items != self._observed_candidate_items
            or previous_index != self._observed_candidate_index
            or previous_text != self._observed_uds_text
        ):
            self.observedUdsCandidateChanged.emit()

    def _update_observed_candidate_text(self):
        if not (0 <= self._observed_candidate_index < len(self._observed_candidate_values)):
            self._observed_uds_text = "Ожидание входящих J1939 RX кадров для автоопределения адреса..."
            return

        device_sa = int(self._observed_candidate_values[self._observed_candidate_index]) & 0xFF
        node = self._observed_node_stats.get(device_sa, {})
        total_count = int(node.get("total", 0)) if isinstance(node, dict) else 0
        uds_count = int(node.get("uds", 0)) if isinstance(node, dict) else 0
        tester_sa, tester_votes = self._choose_tester_sa_for_node(node, int(UdsIdentifiers.tx.src) & 0xFF)

        self._observed_uds_text = (
            f"Кандидат SA устройства: 0x{device_sa:02X}. "
            f"Всего RX кадров: {total_count}, диагностических: {uds_count}. "
            f"Предполагаемый SA тестера: 0x{tester_sa:02X}"
            + (f" (по {tester_votes} UDS кадр.)" if tester_votes > 0 else " (по умолчанию).")
            + f" Найдено устройств: {len(self._observed_candidate_values)}."
        )

    def _update_observed_uds_candidate(self, parsed_id: J1939CanIdentifier):
        device_sa = int(parsed_id.src) & 0xFF
        tester_sa = int(parsed_id.dst) & 0xFF
        current_tester_sa = int(UdsIdentifiers.tx.src) & 0xFF

        # Исключаем собственный SA тестера, чтобы не подхватывать эхо своих сообщений.
        if device_sa == current_tester_sa:
            return

        pgn = int(parsed_id.pgn) & 0x3FFFF
        is_diag = self._is_uds_diagnostic_pgn(pgn)

        stats = self._observed_node_stats.get(device_sa)
        if stats is None:
            stats = {"total": 0, "uds": 0, "last": 0, "tester_votes": {}}
            self._observed_node_stats[device_sa] = stats
            if device_sa not in self._observed_candidate_order:
                self._observed_candidate_order.append(device_sa)

        stats["total"] = int(stats.get("total", 0)) + 1
        if is_diag:
            stats["uds"] = int(stats.get("uds", 0)) + 1
            votes = stats.get("tester_votes", {})
            if not isinstance(votes, dict):
                votes = {}
            votes[tester_sa] = int(votes.get(tester_sa, 0)) + 1
            stats["tester_votes"] = votes

        self._observed_frame_seq += 1
        stats["last"] = self._observed_frame_seq

        if len(self._observed_node_stats) > 256:
            trimmed = sorted(
                self._observed_node_stats.items(),
                key=lambda item: (
                    int(item[1].get("uds", 0)),
                    int(item[1].get("total", 0)),
                    int(item[1].get("last", 0)),
                ),
                reverse=True,
            )[:128]
            self._observed_node_stats = dict(trimmed)

        self._rebuild_observed_candidate_list()

    def _reset_observed_uds_candidate(self, emit_signal: bool = True):
        self._observed_node_stats = {}
        self._observed_candidate_order = []
        self._observed_candidate_values = []
        self._observed_candidate_items = []
        self._observed_candidate_index = -1
        self._observed_frame_seq = 0
        self._observed_uds_text = "Ожидание входящих J1939 RX кадров для автоопределения адреса..."
        if emit_signal:
            self.observedUdsCandidateChanged.emit()
