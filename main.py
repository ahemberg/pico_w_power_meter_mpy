import time
import network
import rp2
import urequests
import secrets
from machine import Pin, ADC
from time import sleep_ms
import ntptime
from collections import deque
import math

### WIFI CODE, BREAK OUT
### Make it retry until it connects. Without wifi and NTP measurements are meaningless

rp2.country('SE')

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)

max_wait = 10

while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print("Waiting for connection")
    time.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])


### SET TIME
ntptime.settime()

### ADC CODE

class Measurement():
    power: int
    timestamp: int

    def __init__(self, power: int, timestamp: int) -> None:
        self.power = power
        self.timestamp = timestamp

    def to_line(self):
        return f"power,host=power_meter_dev value={self.power} {self.timestamp}"

def measure_power(start_time: int) -> Measurement:
    stop_time = time.ticks_us()
    timestamp = time.mktime(time.gmtime())
    delta_us = stop_time - start_time
    imps = 1000000.0 / delta_us
    return Measurement(imps * 3600, timestamp)


# Send code

def to_influx_payload(measurements: list) -> str:
    return '\n'.join([measurement.to_line() for measurement in measurements])



def send_measurements(measurements: list) -> bool:

    url = f"https://{secrets.INFLUX_SERVER}:{secrets.INFLUX_PORT}/write?db={secrets.INFLUX_DATABASE}&precision=s&u={secrets.INFLUX_USER}&p={secrets.INFLUX_PASSWORD}"
    headers = {
        "User-Agent": "curl/8.1.2",
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = to_influx_payload(measurements)


    response = urequests.post(url, headers=headers, data=data)

    print(response.status_code)

    response.close()
    return True

measuring = False
start_time = 0
last_sent = time.mktime(time.gmtime())
    
light_sensor = ADC(Pin(26));

measurements = deque((), 200)

while True:
    adcVal = light_sensor.read_u16();

    if adcVal > 2000:
        if measuring:
            measurements.append(measure_power(start_time))
            sleep_ms(50) # Sleep 50 milliseconds for pulse to die down
        else:
            measuring = True
        start_time = time.ticks_us()

    # Send measurements every 5 minutes or when more than 100 elements are stored
    if len(measurements) > 20 or time.mktime(time.gmtime()) - last_sent > 300:
        measuring = False
        measurements_to_send = [measurements.popleft() for _i in range(min(len(measurements), 20))]
        print("sending: ")
        for m in measurements_to_send:
            print(f"{m.timestamp}:{m.power}")
        
        if send_measurements(measurements_to_send):
            print("Sending success!")
        else:
            ## Todo: The program will stop measuring until send is OK. Handle this with a back off
            print("Failed to send!")
            [measurements.append(m) for m in measurements_to_send]

