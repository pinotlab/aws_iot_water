# aws_iot_publisher.py
import json
import socket
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
        self.is_connected_flag = False
    
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
            self.is_connected_flag = True  # 연결 성공 시 플래그 업데이트
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

    def is_connected(self):
        # 연결 상태 플래그 반환
        return self.is_connected_flag
