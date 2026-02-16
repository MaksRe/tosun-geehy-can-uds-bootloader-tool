import enum
from typing import Optional

from app_can.CanDevice import CanDevice
from uds.data_identifiers import UdsData, UdsVar
from uds.uds_identifiers import UdsIdentifiers


class ServiceReadDataById:
    def __init__(self):
        self._sid = 0x22
        self._pid_request: int = 0

    @property
    def sid(self) -> int:
        return self._sid

    @property
    def success_sid(self) -> int:
        return self._sid + 0x40

    def verify_answer_read_data(self, data) -> bool:
        data_length = data[0]
        sid = data[1]
        # 0-ой байт - младший
        pid = self.parse_pid_field(data)
        if sid == self.success_sid and pid == self._pid_request:
            return True
        return False

    def read_data(self, var: UdsVar):
        self._pid_request = var.pid
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x03,
             self._sid,
             var.pid >> 8, var.pid & 0x00ff,
             0xff, 0xff, 0xff, 0xff])

    def read_data_by_identifier(self, tx_identifier: Optional[int], var: UdsVar):
        self._pid_request = var.pid
        CanDevice.instance().send_async(
            tx_identifier,
            8,
            [0x03,
             self._sid,
             var.pid >> 8, var.pid & 0x00ff,
             0xff, 0xff, 0xff, 0xff])

    @staticmethod
    def parse_pid_field(data):
        return (data[2] << 8) | data[3]

    @staticmethod
    def parse_did_field(data):
        """
        Data identifier
        :param data: Сырые данные
        :return: DID
        """
        return (data[2] << 8) | data[3]

    @staticmethod
    def parse_data_field(data) -> int:
        data_length = data[0]
        if data_length <= 3:
            return 0
        # sid + pid = 3 bytes
        data_length -= 3
        result = 0
        shift = 0
        for i in range(data_length):
            index = 4 + i
            result = result | (data[index] << shift)
            shift += 8
        return result
