# aws_iot_publisher.py
import json
import socket
import time
from awscrt import mqtt
from awsiot import mqtt_connection_builder
import logging

from datetime import datetime

# 현재 시간을 문자열로 변환하는 함수
def get_current_time_str():
    # ISO 8601 형식 (예: 2024-02-07T15:00:00)
    return datetime.now().isoformat()

class AwsIotPublisher:
    def __init__(self, endpoint, ca_file, cert_file, key_file, client_id, topic):
        self.endpoint = endpoint
        self.ca_file = ca_file
        self.cert_file = cert_file
        self.key_file = key_file
        self.client_id = client_id
        self.topic = topic
        self.mqtt_connection = self.create_mqtt_connection()
    
    def create_mqtt_connection(self):
        return mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=self.cert_file,
            pri_key_filepath=self.key_file,
            ca_filepath=self.ca_file,
            client_id=self.client_id,
            clean_session=False,
            keep_alive_secs=30)

    def is_wifi_connected(self, hostname="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((hostname, port))
            return True
        except socket.error as ex:
            logging.error(f"Wi-Fi 연결 실패: {ex}")
            return False

    def publish_message(self, message):
        logging.info(f"Publishing message to topic '{self.topic}': {message}")
        message_json = json.dumps(message)
        self.mqtt_connection.publish(
            topic=self.topic,
            payload=message_json,
            qos=mqtt.QoS.AT_LEAST_ONCE)
        
    def connect(self):
        if self.is_wifi_connected():
            logging.info("Wi-Fi connected, connecting to MQTT...")
            connect_future = self.mqtt_connection.connect()
            connect_future.result()  # wait for connection to be established
            logging.info("MQTT connection established")
            return True
        else:
            logging.error("Wi-Fi is not connected")
            return False

    def disconnect(self):
        logging.info("Disconnecting from MQTT...")
        disconnect_future = self.mqtt_connection.disconnect()
        disconnect_future.result()
        logging.info("Disconnected from MQTT")

# # MQTT 메시지 전송을 위한 파라미터 설정
# endpoint = "a1abb207ddrmxk-ats.iot.ap-northeast-2.amazonaws.com"
# ca_file = "~/root-CA.crt"
# cert_file = "~/Rasp001.cert.pem"
# key_file = "~/Rasp001.private.key"
# client_id = "rasp001"
# topic = "device/1001/data"

# # AwsIotPublisher 인스턴스 생성 및 사용
# publisher = AwsIotPublisher(endpoint, ca_file, cert_file, key_file, client_id, topic)
# if publisher.connect():
#     # 여기서 물이 흐르다가 멈추는 로직을 감지하고 그때의 양을 보내는 코드를 구현하면 됩니다.
#     publisher.publish_message({"time":get_current_time_str(), "flowrate": 1000, "temperature": -5,})  # 여기서 1000은 예시 값입니다.
#     publisher.disconnect()
