import struct
import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

import can


class CANReceiver:
    def __init__(
        self,
        channel: str = "can0",
        bitrate: int = 500000,
        max_data_points: int = 5000,
        bms_id: int = 0x01,
    ):
        self.parser: CANParser = CANParser(bms_id)
        self.bms_id = bms_id
        self.channel: str = channel
        self.bitrate: int = bitrate
        self.max_data_points: int = max_data_points
        self.data_points: Dict[str, List[Tuple[float, Union[int, float]]]] = (
            defaultdict(list)
        )
        self.data_lock: threading.Lock = threading.Lock()
        self.running_lock: threading.Lock = threading.Lock()
        self._is_running: bool = False

    def start_receiving(self) -> None:
        with self.running_lock:
            if not self._is_running:
                self._is_running = True
                self.receive_thread = threading.Thread(
                    target=self.receive_data, daemon=True
                )
                self.receive_thread.start()

    def stop_receiving(self) -> None:
        with self.running_lock:
            self._is_running = False

    def receive_data(self) -> None:
        self.bus = can.interface.Bus(
            bustype="socketcan", channel=self.channel, bitrate=self.bitrate
        )
        while True:
            with self.running_lock:
                if not self._is_running:
                    break

            message: Optional[can.Message] = self.bus.recv(1.0)
            if message:
                timestamp = time.time()
                with self.data_lock:
                    data = self.parser.parse_message(message=message)
                    if data:
                        for key, value in data.items():
                            self.data_points[key].append((timestamp, value))
                            if len(self.data_points[key]) > self.max_data_points:
                                self.data_points[key].pop(0)

    def get_data_points(self) -> Dict[str, List[Tuple[float, Union[int, float]]]]:
        with self.data_lock:
            return {key: points[:] for key, points in self.data_points.items()}

    def notice_full_recharge(self):
        try:
            if self.bus:
                message = can.Message(
                    arbitration_id=0x4600 + self.bms_id, data=[], is_extended_id=True
                )
                self.bus.send(message)
        except can.CanError as e:
            print("Can Send Error")


class CANParser:
    BATTERY_VOLTAGE_CURRENT_ID = 0x4000
    CELL_VOLTAGE_ID = 0x4100
    SOC_DUTY_ID = 0x4200
    TEMP_ID = 0x4300
    EACH_CELL_VOLTAGE_ID = 0x4400
    KEY_BATTERY_VOLTAGE = "battery_voltage"
    KEY_BATTERY_CURRENT = "battery_current"
    KEY_MIN_CELL_VOLTAGE = "min_cell_voltage"
    KEY_MAX_CELL_VOLTAGE = "max_cell_voltage"
    KEY_BATTERY_AVERAGE_TEMP = "battery_average_temp"
    KEY_BATTERY_MAX_TEMP = "battery_max_temp"
    KEY_PCB_AVERAGE_TEMP = "pcb_average_temp"
    KEY_PCB_MAX_TEMP = "pcb_max_temp"
    KEY_REMAIN = "remain"
    KEY_SOC = "soc"
    KEY_DUTY = "duty"
    KEY_CELL = "cell_id_"

    def __init__(self, board_id: int):
        self.board_id = board_id

    def parse_message(self, message) -> Optional[Dict[str, Union[int, float]]]:
        message_id = message.arbitration_id
        if message_id == self.BATTERY_VOLTAGE_CURRENT_ID + self.board_id:
            return self._parse_battery_voltage_current(message.data)
        elif message_id == self.CELL_VOLTAGE_ID + self.board_id:
            return self._parse_cell_voltage(message.data)
        elif message_id == self.SOC_DUTY_ID + self.board_id:
            return self._parse_soc_duty(message.data)
        elif message_id == self.TEMP_ID + self.board_id:
            return self._parse_temp(message.data)
        elif message_id == self.EACH_CELL_VOLTAGE_ID + self.board_id:
            return self._parse_each_cell_voltage(message.data)
        return None

    def _parse_battery_voltage_current(
        self, data: bytes
    ) -> Dict[str, Union[int, float]]:
        # [battery_voltage (uint32_t), battery_current (int32_t)]
        battery_voltage, battery_current = struct.unpack("<I i", data[:8])

        return {
            self.KEY_BATTERY_VOLTAGE: battery_voltage * 100e-6,
            self.KEY_BATTERY_CURRENT: battery_current * 1e-3,
        }

    def _parse_cell_voltage(self, data: bytes) -> Dict[str, Union[int, float]]:
        # [min_cell_voltage (uint32_t), max_cell_voltage (uint32_t)]
        min_cell_voltage, max_cell_voltage = struct.unpack("<I I", data[:8])

        return {
            self.KEY_MIN_CELL_VOLTAGE: min_cell_voltage * 100e-6,
            self.KEY_MAX_CELL_VOLTAGE: max_cell_voltage * 100e-6,
        }

    def _parse_soc_duty(self, data: bytes) -> Dict[str, Union[int, float]]:
        _, remain, soc, _, duty, _ = struct.unpack("<H H B B B B", data[:8])
        return {self.KEY_REMAIN: remain, self.KEY_SOC: soc, self.KEY_DUTY: duty}

    def _parse_temp(self, data: bytes) -> Dict[str, Union[int, float]]:
        battery_average, battery_max, pcb_average, pcb_max = struct.unpack(
            "<h h h h", data[:8]
        )
        return {
            self.KEY_BATTERY_AVERAGE_TEMP: battery_average,
            self.KEY_BATTERY_MAX_TEMP: battery_max,
            self.KEY_PCB_AVERAGE_TEMP: pcb_average,
            self.KEY_PCB_MAX_TEMP: pcb_max,
        }

    def _parse_cell_message(self, data: int) -> Dict[str, Union[int, float]]:
        cell_id = (data & 0xFE00) >> 9
        cell_voltage = data & 0x1FF
        return {f"cell_id_{cell_id}": cell_voltage * 10e-3}

    def _parse_each_cell_voltage(self, data: bytes) -> Dict[str, Union[int, float]]:
        cell1, cell2, cell3, cell4 = struct.unpack("<H H H H", data[:8])
        result = {}
        result.update(self._parse_cell_message(cell1))
        result.update(self._parse_cell_message(cell2))
        result.update(self._parse_cell_message(cell3))
        result.update(self._parse_cell_message(cell4))
        return result
