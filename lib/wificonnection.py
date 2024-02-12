import network
from time import sleep


def block_until_wifi_connected(wlan: network.WLAN,
                               ssid: str,
                               key: str) -> None:
    backoff_s = 10
    while not wlan.isconnected():
        print("tryin to connect")
        disconnect(wlan)
        connect(wlan=wlan, ssid=ssid, key=key, wait_time=backoff_s)
        backoff_s += backoff_s


def connect(wlan: network.WLAN, ssid: str,
            key: str, wait_time=1) -> bool:
    print(f"connect(self, wait_time={wait_time})")
    _connect(wlan=wlan, ssid=ssid, key=key)
    max_wait = wait_time
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            return True
        max_wait -= 1
        print("Waiting for connection")
        sleep(1)
    return False


def _connect(wlan: network.WLAN, ssid: str,
             key: str) -> None:
    try:
        wlan.active(True)
        wlan.connect(ssid=ssid, key=key)
    except OSError as error:
        print(f'error is {error}')


def disconnect(wlan: network.WLAN) -> None:
    wlan.disconnect()
    wlan.active(False)
