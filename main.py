import time
import network
import rp2
import lib.secrets as secrets
from machine import Pin, ADC, Timer
from time import sleep_ms
import ntptime
import gc
import micropython

import lib.wificonnection as wifi
from lib.powermeter import PowerMeter
from lib.influxclient import InfluxClient
from lib.util import get_unix_timestamp

led = Pin("LED", Pin.OUT)
timer = Timer()


def blink(timer):
    led.toggle()


# Blink LED while init
timer.init(freq=20, mode=Timer.PERIODIC, callback=blink)

rp2.country('SE')

wlan = network.WLAN(network.STA_IF)
wifi.block_until_wifi_connected(wlan, secrets.WIFI_SSID, secrets.WIFI_PASS)

# SET TIME
ntptime.settime()

timer.deinit()
led.off()

last_sent = get_unix_timestamp()

light_sensor = ADC(Pin(26))
power_meter = PowerMeter(100)
influxClientPower = InfluxClient(
    hostname="power_meter",
    series_name="power",
    server=secrets.INFLUX_SERVER,
    database=secrets.INFLUX_DATABASE,
    user=secrets.INFLUX_USER,
    password=secrets.INFLUX_PASSWORD)

while True:
    adcVal = light_sensor.read_u16()

    if adcVal > 1500:
        start_time_new = time.ticks_us()
        if power_meter.is_measuring:
            power_meter.stop_measurement()
        power_meter.start_measurement()
        led.on()
        sleep_ms(50)  # Sleep 50 milliseconds for pulse to die down
        led.off()

    # Send measurements every 5 minutes or when more than 20 of the available queue is used elements are stored
    if power_meter.queue_used_space() > .2 or get_unix_timestamp() - influxClientPower.last_sent > 300:

        """
        Assure wifi connection. If connection fails (for instance router down), then we will wait retry
        every loop. This essentially stops measurements during internet outages. Fix this.
        """
        if not wlan.isconnected():
            connected = wifi.connect(
                wlan, secrets.WIFI_SSID, secrets.WIFI_PASS, wait_time=10)
        else:
            connected = True

        if connected:
            print(power_meter.queue_used_space())
            led.on()
            power_meter.cancel_measurement()

            measurements_to_send = power_meter.pop_n_measurements(25)
            for m in measurements_to_send:
                print(f"{m.timestamp}:{m.power}")

            if not influxClientPower.send_measurements(measurements_to_send):
                # Todo: The program will stop measuring until send is OK. Handle this with a back off
                print("Failed to send!")
                power_meter.push_measurements(measurements_to_send)

            print(len(power_meter.measurements))
            led.off()
        else:
            print("Failed to send measurements. No wifi connection")
