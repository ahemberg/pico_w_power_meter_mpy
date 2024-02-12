import urequests

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
        return '\n'.join([measurement.to_line(host=self._hostname, series=self._series_name) for measurement in measurements])

    def send_measurements(self, measurements: list) -> bool:
        url = f"{self._influx_server}:{self._influx_port}/write?db={self._influx_database}&precision=s&u={self._influx_user}&p={self._influx_password}"
        data = self._to_influx_payload(measurements)
        print("sending")
        response = urequests.post(url, headers=self._influx_headers, data=data)
        print("sent")
        response.close()
        self.last_sent = get_unix_timestamp()
        return response.status_code == 204
