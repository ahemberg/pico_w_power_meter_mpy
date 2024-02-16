import time
from collections import deque

from lib.util import get_unix_timestamp


class Measurement:
    power: float
    timestamp: int
    type: str

    def __init__(self, power: float, timestamp: int, type: str) -> None:
        self.power = power
        self.timestamp = timestamp
        self.type = type

    def to_dict(self) -> dict:
        return self.__dict__


class PowerMeasurement(Measurement):
    def __init__(self, power: float, timestamp: int):
        super(PowerMeasurement, self).__init__(power, timestamp, "power")


class ReactivePowerMeasurement(Measurement):
    def __init__(self, power: float, timestamp: int) -> None:
        super().__init__(power, timestamp, "reactive_power")


class PowerMeter:
    measurements: deque
    start_time_power: int = 0
    start_time_reactive_power = 0
    is_measuring_power: bool = False
    is_measuring_reactive_power: bool = False
    capacity: int

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.measurements = deque((), capacity)

    def make_power_measurement(self, ticks_us: int):
        if self.is_measuring_power:
            self.stop_power_measurement()
        self.start_time_power = ticks_us
        self.is_measuring_power = True

    def make_reactive_power_measurement(self, ticks_us: int):
        if self.is_measuring_power:
            self.stop_reactive_power_measurement()
        self.start_time_reactive_power = ticks_us
        self.is_measuring_reactive_power = True

    def start_power_measurement(self) -> None:
        self.start_time_power = time.ticks_us()
        self.is_measuring_power = True

    def stop_power_measurement(self) -> None:
        if not self.is_measuring_power:
            return
        delta_us = time.ticks_diff(time.ticks_us(), self.start_time_power)
        timestamp = get_unix_timestamp()
        imps = 1000000.0 / delta_us
        self.measurements.append(PowerMeasurement(imps * 3600, timestamp))
        self.is_measuring_power = False

    def start_reactive_power_measurement(self) -> None:
        self.start_time_reactive_power = time.ticks_us()
        self.is_measuring_reactive_power = True

    def stop_reactive_power_measurement(self) -> None:
        if not self.is_measuring_reactive_power:
            return
        delta_us = time.ticks_diff(time.ticks_us(), self.start_time_reactive_power)
        timestamp = get_unix_timestamp()
        imps = 1000000.0 / delta_us
        self.measurements.append(ReactivePowerMeasurement(imps * 3600, timestamp))
        self.is_measuring_reactive_power = False

    def cancel_power_measurement(self) -> None:
        self.is_measuring_power = False

    def cancel_reactive_power_measurement(self) -> None:
        self.is_measuring_reactive_power = False

    def pop_n_measurements(self, n: int):
        return [self.measurements.popleft() for _i in range(min(n, len(self.measurements)))]

    def push_measurements(self, measurements: list) -> None:
        [self.measurements.append(m) for m in measurements]

    def queue_used_space(self) -> float:
        return float(len(self.measurements)) / float(self.capacity)
