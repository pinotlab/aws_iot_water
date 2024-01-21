# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
import json
from utils.command_line_utils import CommandLineUtils
import netifaces as ni
import os
import socket
import logging

# This sample uses the Message Broker for AWS IoT to send and receive messages
# through an MQTT connection. On startup, the device connects to the server,
# subscribes to a topic, and begins publishing messages to that topic.
# The device should receive those same messages back from the message broker,
# since it is subscribed to that same topic.

# cmdData is the arguments/input from the command line placed into a single struct for
# use in this sample. This handles all of the command line parsing, validating, etc.
# See the Utils/CommandLineUtils for more information.
cmdData = CommandLineUtils.parse_sample_input_pubsub()

received_count = 0
received_all_event = threading.Event()

logging.basicConfig(
    level=logging.DEBUG,  # 로그 레벨 설정
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 로그 포맷
    filename='app.log',  # 로그를 기록할 파일 이름
    filemode='a'  # 파일 모드, 'a'는 추가 모드, 'w'는 덮어쓰기 모드
)

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    if received_count == cmdData.input_count:
        received_all_event.set()

# Callback when the connection successfully connects
def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print("Connection Successful with return code: {} session present: {}".format(callback_data.return_code, callback_data.session_present))

# Callback when a connection attempt fails
def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print("Connection failed with error code: {}".format(callback_data.error))

# Callback when a connection has been disconnected or shutdown successfully
def on_connection_closed(connection, callback_data):
    print("Connection closed")

# Wi-Fi 연결 상태를 확인하는 함수
def is_wifi_connected(hostname="8.8.8.8", port=53, timeout=3):
    """
    DNS 서버에 소켓 연결을 시도하여 인터넷 연결 상태를 확인합니다.
    기본적으로 Google의 DNS 서버(8.8.8.8)를 대상으로 합니다.
    """
    try:
        # 소켓 연결을 통해 외부 서버와의 연결을 시도합니다.
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((hostname, port))
        return True
    except socket.error as ex:
        print(f"Wi-Fi 연결 실패: {ex}")
        return False

def get_wlan0_ip_address():
    try:
        ip_info = ni.ifaddresses('wlan0')[ni.AF_INET][0]
        return ip_info['addr']
    except:
        return "Unable to get IP Address"

if __name__ == '__main__':
    # Create the proxy options if the data is present in cmdData
    logging.info("Start Pinot!")

    # Wi-Fi가 연결될 때까지 기다리는 반복문
    while not is_wifi_connected():
        logging.info("Trying to connect Wi-Fi...")
        time.sleep(3)  # 5초 대기
    
    logging.info("Wifi-connected")

    proxy_options = None
    if cmdData.input_proxy_host is not None and cmdData.input_proxy_port != 0:
        proxy_options = http.HttpProxyOptions(
            host_name=cmdData.input_proxy_host,
            port=cmdData.input_proxy_port)

    # Create a MQTT connection from the command line data
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=cmdData.input_endpoint,
        port=cmdData.input_port,
        cert_filepath=cmdData.input_cert,
        pri_key_filepath=cmdData.input_key,
        ca_filepath=cmdData.input_ca,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=cmdData.input_clientId,
        clean_session=False,
        keep_alive_secs=30,
        http_proxy_options=proxy_options,
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_closed=on_connection_closed)

    if not cmdData.input_is_ci:
        print(f"Connecting to {cmdData.input_endpoint} with client ID '{cmdData.input_clientId}'...")
    else:
        print("Connecting to endpoint with client ID")
    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    message_count = cmdData.input_count
    message_topic = cmdData.input_topic
    message_string = cmdData.input_message

    # Subscribe
    print("Subscribing to topic '{}'...".format(message_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=message_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

    # Start Message
    ip_address = get_wlan0_ip_address()
    message = "{} [{}]".format("boot complete", ip_address)
    print("Publishing message to topic '{}': {}".format(message_topic, message))
    message_json = json.dumps(message)
    mqtt_connection.publish(
        topic=message_topic,
        payload=message_json,
        qos=mqtt.QoS.AT_LEAST_ONCE)
    
    while True:
        print("Press '1' to send 'hello', '2' to send 'PinotLab.', or 'q' to quit:")
        if sys.platform == 'win32':
            import msvcrt
            key = msvcrt.getch()
        else:
            key = sys.stdin.read(1)

        # 키에 따라 메시지 결정
        if key == '1':
            message_json = json.dumps({"message": "hello"})
        elif key == '2':
            message_json = json.dumps({"message": "PinotLab."})
        elif key == 'q':
            break
        else:
            continue

        # 메시지 발행
        print(f"Publishing message to topic '{message_topic}': {message_json}")
        mqtt_connection.publish(
            topic=message_topic,
            payload=message_json,
            qos=mqtt.QoS.AT_LEAST_ONCE)
   

    # Wait for all messages to be received.
    # This waits forever if count was set to 0.
    if message_count != 0 and not received_all_event.is_set():
        print("Waiting for all messages to be received...")

    received_all_event.wait()
    print("{} message(s) received.".format(received_count))

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")



     # Publish message to server desired number of times.
    # This step is skipped if message is blank.
    # This step loops forever if count was set to 0.
    # if message_string:
    #     if message_count == 0:
    #         print("Sending messages until program killed")
    #     else:
    #         print("Sending {} message(s)".format(message_count))

    #     publish_count = 1
    #     while (publish_count <= message_count) or (message_count == 0):
    #         message = "{} [{}]".format(message_string, publish_count)
    #         print("Publishing message to topic '{}': {}".format(message_topic, message))
    #         message_json = json.dumps(message)
    #         mqtt_connection.publish(
    #             topic=message_topic,
    #             payload=message_json,
    #             qos=mqtt.QoS.AT_LEAST_ONCE)
    #         time.sleep(1)
    #         publish_count += 1
