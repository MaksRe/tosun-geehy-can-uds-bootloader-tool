import enum

from PySide6.QtCore import Slot, Signal, QObject

from app_can.BaseTranslator import BaseTranslator
from app_can.CanDevice import CanDevice
from colors import RowColor
from uds.data_identifiers import UdsData
from uds.services.ecu_reset import ServiceEcuReset
from uds.services.read_data_by_id import ServiceReadDataById
from uds.services.request_download import ServiceRequestDownload
from uds.services.request_transfer_exit import ServiceRequestTransferExit
from uds.services.routine_control import ServiceRoutineControl
from uds.services.security_access import ServiceSecurityAccess
from uds.services.session import ServiceSession, Session
from uds.services.transfer_data import ServiceTransferData
from uds.services.write_data_by_id import ServiceWriteDataById
from uds.uds_identifiers import UdsIdentifiers


class BootloaderState(enum.IntEnum):
    ERROR = -1,
    READY = 0,

    SET_PROGRAMMING_SESSION = 1,

    REQUEST_SEED = 2,
    SEED_VERIFICATION = 3,

    WRITE_FINGERPRINT = 4,

    ERASE_FIRMWARE = 5,

    REQUEST_DOWNLOAD = 6,
    REQUEST_DOWNLOAD_CONSECUTIVE = 7

    TRANSFER_DATA_FF = 8,
    TRANSFER_DATA_FC = 9,
    TRANSFER_DATA_CF = 10,

    REQUEST_TRANSFER_EXIT = 11,

    ECU_UDS_RESET = 12,
    ECU_SOFTWARE_RESET = 13,

    READ_FINGERPRINT = 14,

    VERIFICATION = 15,
    DONE = 16


class Bootloader(QObject):
    signal_new_state = Signal(str, RowColor)
    signal_data_sent = Signal(int)
    signal_finished = Signal(bool)

    def __init__(self):
        super().__init__()

        self._state: BootloaderState = BootloaderState.READY

        self._binary_content = None
        self._transfer_byte_order = "big"

        self._service_session = ServiceSession()
        self._service_security_access = ServiceSecurityAccess()
        self._service_write_data_by_id = ServiceWriteDataById()
        self._service_routine_control = ServiceRoutineControl()
        self._service_request_download = ServiceRequestDownload()
        self._service_transfer_data = ServiceTransferData()
        self._service_request_transfer_exit = ServiceRequestTransferExit()
        self._service_ecu_reset = ServiceEcuReset()
        self._service_read_data_by_id = ServiceReadDataById()
        self._service_request_download.set_byte_order(self._transfer_byte_order)

        self._service_transfer_data.signal_data_sent.connect(self._handle_data_sent)

        CanDevice.instance().signal_new_message.connect(self.on_new_message)

    @Slot(int)
    def _handle_data_sent(self, total_bytes):
        self.signal_data_sent.emit(total_bytes)

    def set_firmware(self, binary_content: bytes):
        self._binary_content = binary_content
        if self._service_request_download is not None:
            self._service_request_download.set_memory_length(len(self._binary_content))

    def set_transfer_byte_order(self, byte_order: str):
        order = str(byte_order).strip().lower()
        self._transfer_byte_order = order if order in ("big", "little") else "big"
        if self._service_request_download is not None:
            self._service_request_download.set_byte_order(self._transfer_byte_order)

    def ecu_uds_reset(self):
        self._service_ecu_reset.ecu_uds_reset()

        self._state = BootloaderState.ECU_UDS_RESET
        self.signal_new_state.emit("Р—Р°РїСЂРѕСЃ РЅР° СЃР±СЂРѕСЃ РњРљ РґР»СЏ РїРµСЂРµС…РѕРґР° РІ Р·Р°РіСЂСѓР·С‡РёРє", RowColor.blue)

    def ecu_software_reset(self):
        self._service_ecu_reset.ecu_software_reset()

        self._state = BootloaderState.ECU_SOFTWARE_RESET
        self.signal_new_state.emit("Р—Р°РїСЂРѕСЃ РЅР° СЃР±СЂРѕСЃ РњРљ РґР»СЏ РїРµСЂРµС…РѕРґР° РІ РѕСЃРЅРѕРІРЅСѓСЋ РїСЂРѕРіСЂР°РјРјСѓ", RowColor.blue)

    def check_state(self):
        self._service_read_data_by_id.read_data(UdsData.fingerprint)

        self._state = BootloaderState.READ_FINGERPRINT
        self.signal_new_state.emit("Р§С‚РµРЅРёРµ СЃС‚Р°С‚СѓСЃР°", RowColor.blue)

    def start(self) -> bool:
        if self._state == BootloaderState.READY:

            if self._binary_content is None:
                self.signal_new_state.emit("РќРµ Р·Р°РіСЂСѓР¶РµРЅР° РѕСЃРЅРѕРІРЅР°СЏ РїСЂРѕРіСЂР°РјРјР°", RowColor.red)
                return False

            self._service_transfer_data.set_firmware(self._binary_content)

            self._state = BootloaderState.SET_PROGRAMMING_SESSION
            self._service_session.set(Session.PROGRAMMING)

            self.signal_new_state.emit("Р—Р°РїСЂРѕСЃ РЅР° СѓСЃС‚Р°РЅРѕРІРєСѓ СЃРµСЃСЃРёРё 'programming'", RowColor.blue)

            return True
        else:
            self.signal_new_state.emit("Р—Р°РіСЂСѓР·С‡РёРє РЅРµ РіРѕС‚РѕРІ Рє СЂР°Р±РѕС‚Рµ", RowColor.red)

            return False

    @Slot(str, str, str, str, list)
    def on_new_message(self, _time, _id, _dir, _data_len_code, _data):

        identifier = BaseTranslator.to_int(_id)
        if identifier != UdsIdentifiers.rx.identifier:
            return

        if self._state == BootloaderState.SET_PROGRAMMING_SESSION:
            if self._service_session.verify_answer(_data):

                self.signal_new_state.emit("РЎРµСЃСЃРёСЏ 'programming' СѓСЃС‚Р°РЅРѕРІР»РµРЅР°", RowColor.green)

                self._state = BootloaderState.REQUEST_SEED
                self._service_security_access.request_seed()

                self.signal_new_state.emit("Р—Р°РїСЂРѕСЃ seed-С„СЂР°Р·С‹", RowColor.blue)

            else:
                self.signal_new_state.emit("РћС€РёР±РєР° РїРµСЂРµС…РѕРґР° РІ СЃРµСЃСЃРёСЋ 'programming'", RowColor.red)

        elif self._state == BootloaderState.REQUEST_SEED:
            if self._service_security_access.verify_answer_request_seed(_data):

                self.signal_new_state.emit("РЈСЃРїРµС€РЅРѕ РїРѕР»СѓС‡РµРЅР° seed-С„СЂР°Р·Р°", RowColor.green)

                self._state = BootloaderState.SEED_VERIFICATION
                self._service_security_access.request_check_key()

                self.signal_new_state.emit("Р—Р°РїСЂРѕСЃ РЅР° РїСЂРѕРІРµСЂРєСѓ РєР»СЋС‡Р° РґРѕСЃС‚СѓРїР°", RowColor.blue)

            else:
                self.signal_new_state.emit("РћС€РёР±РѕС‡РЅС‹Р№ РѕС‚РІРµС‚", RowColor.red)

        elif self._state == BootloaderState.SEED_VERIFICATION:
            if self._service_security_access.verify_answer_request_check_key(_data):
                self.signal_new_state.emit("Р”РѕСЃС‚СѓРї СѓСЃРїРµС€РЅРѕ РїРѕР»СѓС‡РµРЅ", RowColor.green)

                self._state = BootloaderState.WRITE_FINGERPRINT
                self._service_write_data_by_id.write_fingerprint(0xAA)

                self.signal_new_state.emit("Р—Р°РїРёСЃСЊ fingerprint", RowColor.blue)

            else:
                self.signal_new_state.emit("РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РґРѕСЃС‚СѓРїР°", RowColor.red)

        elif self._state == BootloaderState.WRITE_FINGERPRINT:
            if self._service_write_data_by_id.verify_answer_write_fingerprint(_data):
                self.signal_new_state.emit("РЈСЃРїРµС€РЅР°СЏ Р·Р°РїРёСЃСЊ fingerprint", RowColor.green)

                self._state = BootloaderState.ERASE_FIRMWARE
                self._service_routine_control.request_erase_firmware()

                self.signal_new_state.emit("Р—Р°РїСЂРѕСЃ РЅР° РѕС‡РёСЃС‚РєСѓ РѕР±Р»Р°СЃС‚Рё РїР°РјСЏС‚Рё РѕСЃРЅРѕРІРЅРѕР№ РїСЂРѕРіСЂР°РјРјС‹", RowColor.blue)

            else:
                self.signal_new_state.emit("РћС€РёР±РєР° Р·Р°РїРёСЃРё fingerprint", RowColor.red)

        elif self._state == BootloaderState.ERASE_FIRMWARE:
            if self._service_routine_control.verify_answer_erase_firmware(_data):
                self.signal_new_state.emit("РџР°РјСЏС‚СЊ СѓСЃРїРµС€РЅРѕ РѕС‡РёС‰РµРЅР°", RowColor.green)

                self._state = BootloaderState.REQUEST_DOWNLOAD
                self._service_request_download.request_download_first()

                self.signal_new_state.emit("Р—Р°РїСЂРѕСЃ РЅР° РїСЂРѕРіСЂР°РјРјРёСЂРѕРІР°РЅРёРµ РѕР±Р»Р°СЃС‚Рё РїР°РјСЏС‚Рё", RowColor.blue)

            else:
                self.signal_new_state.emit("РћС€РёР±РєР° РІ РїСЂРѕС†РµСЃСЃРµ РѕС‡РёСЃС‚РєРё РїР°РјСЏС‚Рё", RowColor.red)

        elif self._state == BootloaderState.REQUEST_DOWNLOAD:
            # РїСЂРёС…РѕРґРёС‚ FlowControl
            if self._service_request_download.verify_flow_control(_data):

                self._state = BootloaderState.REQUEST_DOWNLOAD_CONSECUTIVE
                self._service_request_download.request_download_consecutive()

        elif self._state == BootloaderState.REQUEST_DOWNLOAD_CONSECUTIVE:
            if self._service_request_download.verify_request_download(_data):
                self.signal_new_state.emit("РЈСЃРїРµС€РЅС‹Р№ Р·Р°РїСЂРѕСЃ РЅР° РїРµСЂРµРґР°С‡Сѓ РґР°РЅРЅС‹С…", RowColor.green)

                self._state = BootloaderState.TRANSFER_DATA_FF
                block_size = self._service_transfer_data.send_first_frame()
                self.signal_new_state.emit(f"РџРµСЂРµРґР°С‡Р° Р±Р»РѕРєР° ({block_size} Р±Р°Р№С‚)", RowColor.blue)

        elif self._state == BootloaderState.TRANSFER_DATA_FF:
            if self._service_transfer_data.verify_flow_control(_data):
                self._state = BootloaderState.TRANSFER_DATA_CF
                self._service_transfer_data.send_consecutive_frames()
            else:
                self.signal_new_state.emit("РћС€РёР±РєР° РѕР±СЂР°Р±РѕС‚РєРё flow control", RowColor.red)
                self._state = BootloaderState.ERROR

        elif self._state == BootloaderState.TRANSFER_DATA_CF:
            if self._service_transfer_data.data_transferred():
                self.signal_new_state.emit("Р’СЃРµ РґР°РЅРЅС‹Рµ РїРµСЂРµРґР°РЅС‹", RowColor.green)

                self._state = BootloaderState.REQUEST_TRANSFER_EXIT
                self._service_request_transfer_exit.request_transfer_exit()
                self.signal_new_state.emit("Р—Р°РІРµСЂС€РµРЅРёРµ РїРµСЂРµРґР°С‡Рё", RowColor.blue)

            else:
                # РџРѕСЃР»Рµ РїРµСЂРµРґР°С‡Рё РїРѕР»РЅРѕРіРѕ Р±Р»РѕРєР° (2048 Р±Р°Р№С‚)
                # С„РѕСЂРјРёСЂСѓРµРј РґСЂСѓРіРѕР№ Р±Р»РѕРє, РЅР°С‡РёРЅР°СЏ СЃ first frame
                if self._service_transfer_data.block_transferred():
                    if self._service_transfer_data.verify_answer_after_sent_block(_data):
                        self._state = BootloaderState.TRANSFER_DATA_FF
                        block_size = self._service_transfer_data.send_first_frame()
                        self.signal_new_state.emit(f"РџРµСЂРµРґР°С‡Р° Р±Р»РѕРєР° ({block_size} Р±Р°Р№С‚)", RowColor.blue)
                else:
                    # РџРѕСЃР»Рµ РїРµСЂРµРґР°С‡Рё РјР°РєСЃРёРјР°Р»СЊРЅРѕРіРѕ РєРѕР»РёС‡РµСЃС‚РІР° С„СЂРµР№РјРѕРІ РІ РѕРґРЅРѕРј Р±Р»РѕРєРµ,
                    # РїСЂРёРЅРёРјР°РµРј РѕС‡РµСЂРµРґРЅРѕР№ flow_control Рё РёР· РЅРµРіРѕ Р±РµСЂРµРј РѕС‡РµСЂРµРґРЅРѕРµ РєРѕР»РёС‡РµСЃС‚РІРѕ
                    # С„СЂРµР№РјРѕРІ (block_size) РґР»СЏ РїРѕСЃР»РµРґСѓС‰РµР№ РїРµСЂРµРґР°С‡Рё
                    if self._service_transfer_data.verify_flow_control(_data):
                        self._service_transfer_data.send_consecutive_frames()
                    else:
                        self.signal_new_state.emit("РћС€РёР±РєР° РѕР±СЂР°Р±РѕС‚РєРё flow control", RowColor.red)
                        self._state = BootloaderState.ERROR

        elif self._state == BootloaderState.REQUEST_TRANSFER_EXIT:
            if self._service_request_transfer_exit.verify_answer_request_transfer_exit(_data):
                self.signal_new_state.emit("РЈСЃРїРµС€РЅРѕРµ Р·Р°РІРµСЂС€РµРЅРёРµ РїРµСЂРµРґР°С‡Рё РґР°РЅРЅС‹С…", RowColor.green)

                self.signal_finished.emit(True)
                self._state = BootloaderState.READY

            else:
                self.signal_new_state.emit("РћС€РёР±РєР° Р·Р°РІРµСЂС€РµРЅРёСЏ РїРµСЂРµРґР°С‡Рё РґР°РЅРЅС‹С…", RowColor.red)
                self._state = BootloaderState.ERROR

        elif self._state == BootloaderState.ECU_UDS_RESET:
            if self._service_ecu_reset.verify_ecu_uds_reset(_data):

                self.signal_new_state.emit("РЈСЃРїРµС€РЅС‹Р№ СЃР±СЂРѕСЃ", RowColor.green)
                self._state = BootloaderState.READY
            else:
                self.signal_new_state.emit("РћС€РёР±РєР° СЃР±СЂРѕСЃР°", RowColor.red)
                self._state = BootloaderState.READY

        elif self._state == BootloaderState.ECU_SOFTWARE_RESET:
            if self._service_ecu_reset.verify_ecu_software_reset(_data):

                self.signal_new_state.emit("РЈСЃРїРµС€РЅС‹Р№ СЃР±СЂРѕСЃ", RowColor.green)
                self._state = BootloaderState.READY
            else:
                self.signal_new_state.emit("РћС€РёР±РєР° СЃР±СЂРѕСЃР°", RowColor.red)
                self._state = BootloaderState.READY

        elif self._state == BootloaderState.READ_FINGERPRINT:
            if self._service_read_data_by_id.verify_answer_read_data(_data):

                self.signal_new_state.emit("Р—Р°РіСЂСѓР·С‡РёРє Р°РєС‚РёРІРµРЅ", RowColor.green)
                self._state = BootloaderState.READY
            else:
                self.signal_new_state.emit("Р—Р°РіСЂСѓР·С‡РёРє РЅРµ Р°РєС‚РёРІРµРЅ", RowColor.red)
                self._state = BootloaderState.READY

        if self._state == BootloaderState.ERROR:
            pass
            # CanDevice.instance().signal_new_message.disconnect(self.on_new_message)



