import time
import network
import rp2
import lib.secrets as secrets
from machine import Pin, ADC, Timer
from time import sleep_ms
import ntptime

import lib.wificonnection as wifi
from lib.powermeter import PowerMeter
from lib.mqttclient import MqttClient
from lib.util import get_unix_timestamp

led = Pin("LED", Pin.OUT)
timer_led = Timer()
timer_ntp = Timer()


def blink(timer):
    led.toggle()


def update_ntp(timer):
    print("Updating NTP")
    ntptime.settime()


# Blink LED while init
timer_led.init(freq=20, mode=Timer.PERIODIC, callback=blink)

rp2.country('SE')

wlan = network.WLAN(network.STA_IF)
wifi.block_until_wifi_connected(wlan, secrets.WIFI_SSID, secrets.WIFI_PASS)

# SET TIME
print("Updating NTP and setting timer")
ntptime.settime()
timer_ntp.init(period=86400000, mode=Timer.PERIODIC, callback=update_ntp)
print(f"Updating ntp done. Time is now {time.gmtime()}")

timer_led.deinit()
led.off()

last_sent = get_unix_timestamp()

light_sensor = ADC(Pin(26))
power_meter = PowerMeter(200)

mqttclient = MqttClient(
    hostname=secrets.HOSTNAME,
    series_name=secrets.SERIESNAME,
    server=secrets.MQTT_SERVER,
    topic=secrets.MQTT_TOPIC)

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

    # Dump messages once we have built up 20 or 5 minutes has passed
    if power_meter.queue_used_space() > .1 or get_unix_timestamp() - mqttclient.last_sent > 300:

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
            measurements_to_send = power_meter.pop_n_measurements(100)
            if not mqttclient.send_using_mqtt(measurements_to_send):
                # Todo: The program will stop measuring until send is OK. Handle this with a back off
                print("Failed to send measurements!")
                power_meter.push_measurements(measurements_to_send)
            led.off()
        else:
            print("Failed to send measurements. No wifi connection")
