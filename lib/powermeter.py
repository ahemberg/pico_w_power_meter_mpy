import time
from collections import deque

from lib.util import get_unix_timestamp


class Measurement():
    power: float
    timestamp: int

    def __init__(self, power: float, timestamp: int) -> None:
        self.power = power
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return self.__dict__


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
            return
        delta_us = time.ticks_diff(time.ticks_us(), self.start_time)
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
