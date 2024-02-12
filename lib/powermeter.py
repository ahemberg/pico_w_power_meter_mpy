import time
from collections import deque

from lib.util import get_unix_timestamp

class Measurement():
    power: int
    timestamp: int

    def __init__(self, power: int, timestamp: int) -> None:
        self.power = power
        self.timestamp = timestamp

    def to_line(self, host: str="power_meter", series: str="power", value_col: str="value") -> str:
        return f"{series},host={host} value={self.power} {self.timestamp}"


class PowerMeter():
    measurements: deque
    start_time: int = 0
    is_measuring: bool = False
    capacity: int

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.measurements = deque((), capacity)

    def start_measurement(self) -> None:
        self.start_time = time.ticks_us()
        self.is_measuring = True

    def stop_measurement(self) -> None:
        if not self.is_measuring:
            print("Not recording measurement as no measurement was started")
            return
        delta_us = time.ticks_us() - self.start_time
        timestamp = get_unix_timestamp()
        imps = 1000000.0 / delta_us
        self.measurements.append(Measurement(imps * 3600, timestamp))
        self.is_measuring = False

    def cancel_measurement(self) -> None:
        self.is_measuring = False

    def pop_n_measurements(self, n: int):
        return [self.measurements.popleft() for _i in range(min(n, len(self.measurements)))]
    
    def push_measurements(self, measurements: list) -> None:
        [self.measurements.append(m) for m in measurements]

    def queue_used_space(self) -> float:
        return float(len(self.measurements))/float(self.capacity)