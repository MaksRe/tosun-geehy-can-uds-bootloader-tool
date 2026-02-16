from app_can.CanDevice import CanDevice
from uds.data_identifiers import UdsData, UdsVar
from uds.uds_identifiers import UdsIdentifiers


class ServiceWriteDataById:
    def __init__(self):
        self._sid = 0x2e
        self._saved_pid = 0

    def write_data(self, var: UdsVar, value) -> bool:

        if var.size > 4:
            return False

        self._saved_pid = var.pid

        pid_l = var.pid & 0x00ff
        pid_h = var.pid >> 8

        # sid + pid = 3 bytes
        frame = [3 + var.size,  # Single Frame, data length
                 self._sid,  # WriteDataById
                 pid_h, pid_l]  # Service Fingerprint

        for _ in range(var.size):
            frame.append(value & 0xff)
            value = value >> 8

        if var.size < 4:
            rem = 4 - var.size
            for _ in range(rem):
                frame.append(0xff)

        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            frame)

        return True

    def verify_answer_write_data(self, response_data) -> bool:
        data_length = response_data[0]
        sid = response_data[1]
        positive_sid = self._sid + 0x40
        # 0-ой байт - младший
        pid = (response_data[2] << 8) | response_data[3]
        if sid == positive_sid and pid == self._saved_pid:
            return True
        return False

    def write_fingerprint(self, value: int):
        pid_l = UdsData.fingerprint.pid & 0x00ff
        pid_h = UdsData.fingerprint.pid >> 8
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x04,  # Single Frame, data length
             self._sid,  # WriteDataById
             pid_h, pid_l,  # Service Fingerprint
             value,  # Data fingerprint
             0xff, 0xff, 0xff])

    def verify_answer_write_fingerprint(self, response_data) -> bool:
        data_length = response_data[0]
        sid = response_data[1]
        # 0-ой байт - младший
        pid = (response_data[2] << 8) | response_data[3]
        if sid == (self._sid + 0x40):
            if pid == UdsData.fingerprint.pid:
                return True
        return False

    def parse_pid_field(self, data):
        return (data[2] << 8) | data[3]
