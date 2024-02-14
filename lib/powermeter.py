import time
from collections import deque

from lib.util import get_unix_timestamp
import _thread

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
    send_queue: deque
    start_time: int = 0
    is_measuring: bool = False
    capacity: int
    _send_queue_capacity: int = 10

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.measurements = deque((), capacity)
        self.send_queue = deque((), 10)

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

    def pop(self) -> Measurement:
        return self.send_queue.popleft()

    def pop_n_measurements(self, n: int) -> list:
        return [self.pop() for _i in range(min(n, len(self.send_queue)))]
    
    def push(self, measurement: Measurement) -> None:
        self.send_queue.append(measurement)

    def push_measurements(self, measurements: list) -> None:
        [self.push(m) for m in measurements]

    def put_on_send_queue(self) -> None:

        if len(self.measurements) is 0:
            #Nothing to move
            return

        free_slots = self._send_queue_capacity - len(self.send_queue)
        if free_slots <= 0:
            # No space on send queue. Will not move
            return
        
        # Fill the send queue
        measurements = [self.measurements.popleft() for _i in range(min(free_slots, len(self.measurements)))]
        self.push_measurements(measurements)
    
    def has_measurements_to_send(self) -> bool:
        return len(self.send_queue) > 0
