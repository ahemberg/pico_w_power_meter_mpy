import time
import network
import rp2
import lib.secrets as secrets
from machine import Pin, ADC, Timer
from time import sleep_ms
import ntptime
import _thread
import gc

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
powermeter = PowerMeter(200)

# Responsible for measuring data
def thread_0(power_meter: PowerMeter) -> None:
    global lock
    light_sensor = ADC(Pin(26))
    print("starting thread 0")
    while True:
        adcVal = light_sensor.read_u16()

        if adcVal > 2000:
            if power_meter.is_measuring:
                power_meter.stop_measurement()
            power_meter.start_measurement()
            led.on()
            print("got measurement")
            sleep_ms(50)  # Sleep 50 milliseconds for pulse to die down
            led.off()
        
        if lock.acquire(0):
            #Not waiting for the lock. If its locked we continue measuring and send at another time
            #print("Putting on send queue")
            power_meter.put_on_send_queue()
            lock.release()
        else:
            print("currently sending, will wait to push")
        gc.collect()
    


# Responsible for sending the data 
def thread_1(power_meter: PowerMeter) -> None:
    mqttclient = MqttClient(
        hostname=secrets.HOSTNAME,
        series_name=secrets.SERIESNAME,
        server=secrets.MQTT_SERVER,
        topic=secrets.MQTT_TOPIC)
    
    print("Starting thred 1")

    global lock
    while True:

        while not power_meter.has_measurements_to_send():
            #Idle here until there is something in the measurement queue
            pass

        if not wlan.isconnected():
                connected = wifi.connect(
                    wlan, secrets.WIFI_SSID, secrets.WIFI_PASS, wait_time=10)
        else:
            connected = True

        if connected:
            lock.acquire()
            try:
                print("Sent")
                measurements = power_meter.pop_n_measurements(10)
                if measurement and not mqttclient.send_using_mqtt([measurement]):
                    print("Sending failed")
                    power_meter.push(measurement)
                lock.release()
            except IndexError:
                # IndexError is thrown if there are no measurements. 
                # Release the lock and wait a second. This case should
                # never happen, but multithreading is scary
                print("Got index error")
                lock.release()
                time.sleep_ms(1000)
        else:
            print("Failed to send measurements. Not connected to wifi")
            #time.sleep_ms(5000) # wait five seconds before trying again
        
        time.sleep()
        gc.collect()

lock = _thread.allocate_lock()
second_thread = _thread.start_new_thread(thread_0, (powermeter,))
thread_1(powermeter)