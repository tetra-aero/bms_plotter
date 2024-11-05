import can
import flet as ft
from flet.plot import LineChart, LineSeries
import threading
import time
from typing import Optional, Dict, Union
import struct

class CANReceiver:
    def __init__(self, channel: str = 'can0', bitrate: int = 500000, max_data_points: int = 50):
        self.channel: str = channel
        self.bitrate: int = bitrate
        self.max_data_points: int = max_data_points
        self.data_points: List[int] = []
        self.data_lock: threading.Lock = threading.Lock()
        self.running_lock: threading.Lock = threading.Lock()
        self._is_running: bool = False

    def start_receiving(self) -> None:
        with self.running_lock:
            if not self._is_running:
                self._is_running = True
                self.receive_thread = threading.Thread(target=self._receive_data, daemon=True)
                self.receive_thread.start()

    def stop_receiving(self) -> None:
        with self.running_lock:
            self._is_running = False

    def receive_data(self) -> None:
        bus = can.interface.Bus(bustype='socketcan', channel=self.channel, bitrate=self.bitrate)
        while True:
            with self.running_lock:
                if not self._is_running:
                    break
            
            message: Optional[can.Message] = bus.recv(1.0)
            if message:
                data_value: int = message.data[0]
                with self.data_lock:
                    self.data_points.append(data_value)
                    if len(self.data_points) > self.max_data_points:
                        self.data_points.pop(0)
            time.sleep(0.1)

    def get_data_points(self) -> List[int]:
        with self.data_lock:
            return self.data_points.copy()

class CANParser:

    BATTERY_VOLTAGE_CURRENT_ID= 0x4000
    CELL_VOLTAGE_ID= 0x4100
    SOC_DUTY_ID = 0x4200
    TEMP_ID = 0x4300
    EACH_CELL_VOLTAGE_ID = 0x4400
    

    def __init__(self, board_id: int):
        self.board_id = board_id

    def parse_message(self, message: can.Message) -> Optional[Dict[str, Union[int, float]]]:

        message_id = message.arbitration_id

        if message_id == self.BATTERY_VOLTAGE_CURRENT_ID + self.board_id:
            return self._parse_battery_voltage_current(message.data)

        elif message_id == self.CELL_VOLTAGE_ID + self.board_id:
            return self._parse_cell_voltage(message.data)
        elif message_id = self.

        return None

    def _parse_battery_voltage_current(self, data: bytes) -> Dict[str, Union[int, float]]:
        # [battery_voltage (uint32_t), battery_current (int32_t)]
        battery_voltage, battery_current = struct.unpack("<I i", data[:8])
        
        return {
            "battery_voltage": battery_voltage * 100e-6,  
            "battery_current": battery_current * 1e-3,         
        }

    def _parse_cell_voltage(self, data: bytes) -> Dict[str, Union[int, float]]:
        # [min_cell_voltage (uint32_t), max_cell_voltage (uint32_t)]
        min_cell_voltage, max_cell_voltage = struct.unpack("<I I", data[:8])
        
        return {
            "min_cell_voltage": min_cell_voltage * 100e-6,
            "max_cell_voltage": max_cell_voltage * 100e-6,
        }

    def _parse_temp (self,data:bytes) -> Dict[str,Union[int,float]]:
        battery_average, battery_max, pcb_average, pcb_max =struct.unpack("<h h h h",data[:8])

    def _parse_each_cell_voltage (self,data:bytes) -> Dict[str,Union[int,float]]:
        cell1, cell2, cell3, cell4 = struct.unpack("<H H H H",data[:8])
