import asyncio
import math
import queue
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
        self._is_running: bool = False
        self.message_queue = queue.Queue()
        self._bus_lock: threading.Lock = threading.Lock()
        self._bus: Optional[can.interface.Bus] = None

    def _get_bus(self) -> can.interface.Bus:
        """Get or initialize the shared bus instance."""
        if self._bus is None:
            with self._bus_lock:
                self._bus = can.interface.Bus(
                    bustype="socketcan", channel=self.channel, bitrate=self.bitrate
                )
        return self._bus

    def start_receiving(self) -> None:
        if not self._is_running:
            self._is_running = True
            self.receiver_thread = threading.Thread(target=self._receive_data)
            self.receiver_thread.start()

    def stop_receiving(self) -> None:
        if self._is_running:
            self._is_running = False
            self.receiver_thread.join()
            self._close_bus()

    def _close_bus(self) -> None:
        if self._bus:
            with self._bus_lock:
                self._bus.shutdown()
                self._bus = None

    def _receive_data(self) -> None:
        while self._is_running:
            try:
                bus = self._get_bus()
                message: Optional[can.Message] = bus.recv(1.0)  # 1-second timeout
                if message:
                    timestamp = int(time.time())
                    data = self.parser.parse_message(message)
                    if data:
                        for key, value in data.items():
                            self.message_queue.put((timestamp, key, value))
            except can.CanError as e:
                print(f"CAN receive error: {e}")

    async def process_messages(self) -> None:
        while True:
            timestamp, key, value = await self._get_message_from_queue()
            if timestamp is not None:
                with self.data_lock:
                    self.data_points[key].append((timestamp, value))
                    if len(self.data_points[key]) > self.max_data_points:
                        self.data_points[key].pop(0)

    async def _get_message_from_queue(self):
        if not self.message_queue.empty():
            return self.message_queue.get(1)
        else:
            return None, None, None

    async def get_data_points(self) -> Dict[str, List[Tuple[float, Union[int, float]]]]:
        with self.data_lock:
            return {key: points[:] for key, points in self.data_points.items()}

    async def notice_full_recharge(self):
        if self._is_running:
            try:
                bus = self._get_bus()
                message = can.Message(
                    arbitration_id=0x4600 + self.bms_id,
                    data=[],
                    is_extended_id=True,
                )
                await asyncio.to_thread(bus.send, message)
            except can.CanError as e:
                print(f"CAN send error: {e}")


class CANParser:
    BATTERY_VOLTAGE_CURRENT_ID = 0x4000
    CELL_VOLTAGE_ID = 0x4100
    SOC_DUTY_ID = 0x4200
    TEMP_ID = 0x4300
    EACH_CELL_VOLTAGE_ID = 0x4400
    EACH_TEMPERATURE_ID = 0x4500
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
    KEY_TEMP = "thrm_id_"

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
        elif message_id == self.EACH_TEMPERATURE_ID + self.board_id:
            return self._parse_each_temperature(message.data)
        return None

    def _parse_battery_voltage_current(
        self, data: bytes
    ) -> Dict[str, Union[int, float]]:
        battery_voltage, battery_current = struct.unpack("<I i", data[:8])
        return {
            self.KEY_BATTERY_VOLTAGE: round(battery_voltage * 100e-6, 2),
            self.KEY_BATTERY_CURRENT: round(battery_current * 1e-3, 2),
        }

    def _parse_cell_voltage(self, data: bytes) -> Dict[str, Union[int, float]]:
        min_cell_voltage, max_cell_voltage = struct.unpack("<I I", data[:8])
        return {
            self.KEY_MIN_CELL_VOLTAGE: round(min_cell_voltage * 100e-6, 2),
            self.KEY_MAX_CELL_VOLTAGE: round(max_cell_voltage * 100e-6, 2),
        }

    def _parse_soc_duty(self, data: bytes) -> Dict[str, Union[int, float]]:
        _, remain, soc, _, duty, _ = struct.unpack("<H H B B B B", data[:8])
        return {self.KEY_REMAIN: remain, self.KEY_SOC: soc, self.KEY_DUTY: duty}

    def _parse_temp(self, data: bytes) -> Dict[str, Union[int, float]]:
        battery_average, battery_max, pcb_average, pcb_max = struct.unpack(
            "<h h h h", data[:8]
        )
        return {
            self.KEY_BATTERY_AVERAGE_TEMP: round(battery_average, 2),
            self.KEY_BATTERY_MAX_TEMP: round(battery_max, 2),
            self.KEY_PCB_AVERAGE_TEMP: round(pcb_average, 2),
            self.KEY_PCB_MAX_TEMP: round(pcb_max, 2),
        }

    def _parse_cell_message(self, data: int) -> Dict[str, Union[int, float]]:
        cell_id = (data & 0xFE00) >> 9
        cell_voltage = data & 0x1FF
        return {f"cell_id_{cell_id}": round(cell_voltage * 10e-3, 2)}

    def _parse_each_cell_voltage(self, data: bytes) -> Dict[str, Union[int, float]]:
        cell1, cell2, cell3, cell4 = struct.unpack("<H H H H", data[:8])
        result = {}
        result.update(self._parse_cell_message(cell1))
        result.update(self._parse_cell_message(cell2))
        result.update(self._parse_cell_message(cell3))
        result.update(self._parse_cell_message(cell4))
        return result

    def _parse_thrm_message(self, data: int) -> Dict[str, Union[int, float]]:
        thrm_id = (data & 0xFC00) >> 10
        compressed_temp = data & 0x03FF
        sign_bit = (compressed_temp & 0x0200) >> 9
        abs_temperature = compressed_temp & 0x01FF
        temperature = -abs_temperature if sign_bit == 1 else abs_temperature
        return {f"thrm_id_{thrm_id}": round(temperature, 2)}

    def _parse_each_temperature(self, data: bytes) -> Dict[str, Union[int, float]]:
        result = {}
        if len(data) % 2 != 0:
            return result

        for i in range(0, len(data), 2):
            (thrm,) = struct.unpack("<H", data[i : i + 2])
            result.update(self._parse_thrm_message(thrm))

        return result
