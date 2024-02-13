import socket

from lib.powermeter import Measurement
from lib.util import get_unix_timestamp


class InfluxClient():
    last_sent: int = 2147483647  # Max timestamp
    _hostname: str
    _series_name = str
    _influx_server: str
    _influx_database: str
    _influx_user: str
    _influx_password: str
    _influx_port: int

    _influx_headers: dict = {
        "User-Agent": "curl/8.1.2",
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    def __init__(self,
                 hostname: str,
                 series_name: str,
                 server: str,
                 database: str,
                 user: str,
                 password: str,
                 port: int = 8086) -> None:

        self._hostname = hostname
        self._series_name = series_name
        self._influx_server = server
        self._influx_database = database
        self._influx_user = user
        self._influx_password = password
        self._influx_port = port

    def _to_influx_payload(self, measurements: list) -> str:
        return '\n'.join([measurement.to_line(host=self._hostname, series=self._series_name).strip() for measurement in measurements])

    def send_using_socket(self, measurements: list) -> bool:
        ai = socket.getaddrinfo("alehem.eu", 8086)
        addr = ai[0][-1]

        measurements_payload = self._to_influx_payload(measurements)

        payload = f"POST /write?db=pico_dev&precision=s&u={self._influx_user}&p={self._influx_password} HTTP/1.1\n"
        payload += f"Host: alehem.eu:8086\n"
        payload += f"User-Agent: curl/8.1.2\n"
        payload += f"Accept: */*\r\n"
        payload += f"Content-Length: {len(measurements_payload)}\n"
        payload += f"Content-Type: application/x-www-form-urlencoded\n"
        payload += "\n"
        payload += measurements_payload

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(addr)
        s.write(payload.encode('utf-8'))

        response = s.recv(64).decode()
        s.close()

        if 'HTTP/1.1 204 No Content' in response:
            return True
        return False
