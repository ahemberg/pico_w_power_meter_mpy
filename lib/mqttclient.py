import json
from umqtt.simple import MQTTClient
from lib.powermeter import Measurement
from lib.util import get_unix_timestamp


class MqttClient():
    last_sent: int = 2147483647  # Max timestamp
    _hostname: bytes
    _series_name = str
    _mqtt_server: bytes
    _mqtt_topic: bytes
    _mqtt_port: int
    _mqtt_client: MQTTClient = None
    # Todo enable auth for mqtt. This is disabled for devices on local lan now

    def __init__(self,
                 hostname: str,
                 series_name: str,
                 server: str,
                 topic: str,
                 port: int = 1883) -> None:

        self._hostname = hostname.encode()
        self._series_name = series_name
        self._mqtt_server = server.encode()
        self._mqtt_topic = topic.encode()
        self._mqtt_port = port
        self.connect()

    def _to_mqtt_payload(self, measurement: Measurement) -> bytes:
        return json.dumps(
            {
                'power': measurement.power,
                'timestamp': measurement.timestamp,
                'measurement': self._series_name,
                'host': self._hostname
            }
        ).encode('utf-8')

    def connect(self) -> bool:
        try:
            self._mqtt_client = MQTTClient(
                client_id=self._hostname, server=self._mqtt_server, port=self._mqtt_port, keepalive=7200, ssl=False)
            return self._mqtt_client.connect() == 0
        except OSError as e:
            self._mqtt_client = None
            print("Failed to connect!")
            print(e)
            return False

    def disconnect(self) -> None:

        if self._mqtt_client is None:
            return

        try:
            self._mqtt_client.disconnect()
        except OSError as e:
            print("Disconnect failed")
            print(e)
        self._mqtt_client = None

    def send_using_mqtt(self, measurements: list) -> bool:

        try:
            print("sending")
            [self._mqtt_client.publish(self._mqtt_topic, self._to_mqtt_payload(
                measurement)) for measurement in measurements]
            self.last_sent = get_unix_timestamp()
            return True
        except Exception as e:
            print("Failed to send")
            self.disconnect()
            self.connect()
            return False
