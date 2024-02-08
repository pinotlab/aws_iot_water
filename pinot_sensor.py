import RPi.GPIO as GPIO
import time
from datetime import datetime
from samples.pinot_aws_mqtt import AwsIotPublisher 
import os

# GPIO 핀 번호 설정 모드
GPIO.setmode(GPIO.BCM)

# AWS IoT Core 연결 정보
endpoint = "a1abb207ddrmxk-ats.iot.ap-northeast-2.amazonaws.com"
ca_file = os.path.expanduser("~/root-CA.crt")
cert_file = os.path.expanduser("~/Rasp001.cert.pem")
key_file = os.path.expanduser("~/Rasp001.private.key")
client_id = "rasp001"
topic = "device/1001/data"

# AwsIotPublisher 인스턴스 생성
publisher = AwsIotPublisher(endpoint, ca_file, cert_file, key_file, client_id, topic)

# MQTT 연결 시도
if publisher.connect():
    print("Connected to AWS IoT Core")
else:
    print("Failed to connect to AWS IoT Core")

# LED 핀 설정
pins = {'R': 17, 'G': 27, 'B': 22}
for pin in pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)

# PWM 인스턴스 생성
R = GPIO.PWM(pins['R'], 2000)
G = GPIO.PWM(pins['G'], 2000)
B = GPIO.PWM(pins['B'], 2000)

# 시작
R.start(100)  # 꺼짐
G.start(100)
B.start(100)

# 색상 변경 함수
def set_color(r, g, b):
    R.ChangeDutyCycle(r)
    G.ChangeDutyCycle(g)
    B.ChangeDutyCycle(b)

def get_current_time_str():
    # ISO 8601 형식 (예: 2024-02-07T15:00:00)
    return datetime.now().isoformat()

# 유량 센서 설정
sensor_pin = 18
GPIO.setup(sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pulse_count = 0
calibration_factor = 5.5
total_millilitres = 0

def pulse_counter(channel):
    global pulse_count
    pulse_count += 1

GPIO.add_event_detect(sensor_pin, GPIO.FALLING, callback=pulse_counter)

old_time = time.time()

# 물 흐름이 시작되었는지와 마지막으로 물이 흐른 시간을 추적하는 변수를 추가
flow_started = False
last_flow_time = 0
flow_stop_delay = 3  # 물 흐름이 멈춘 것으로 간주하기 전에 기다릴 시간 (초)

try:
    while True:
        current_time = time.time()
        if current_time - old_time > 1:
            flow_rate = (pulse_count / calibration_factor) / (current_time - old_time) * 60
            flow_millilitres = (flow_rate / 60) * 16.700
            # total_millilitres += flow_millilitres

            if flow_rate > 0:
                if not flow_started:
                    flow_started = True
                    total_millilitres = 0  # 흐름이 시작될 때 총 미리리터를 리셋
                total_millilitres += flow_millilitres
                last_flow_time = current_time
                set_color(100, 0, 100)  # 초록색
            else:
                set_color(0, 100, 100)  # 빨간색

            # 물 흐름이 있었고, 정해진 시간 동안 물 흐름이 없었을 때 MQTT 메시지 전송
            if flow_started and (current_time - last_flow_time >= flow_stop_delay):
                publisher.publish_message({
                    "flowrate": round(total_millilitres, 2),
                    "time": get_current_time_str(),
                    'temperature': -5,
                    'humidity': 30,
                    'barometer': 200
                })
                print(f"Total volume sent: {total_millilitres:.2f} mL")
                flow_started = False  # 메시지 전송 후 흐름 상태 리셋

            print(f"Flow rate: {flow_rate:.2f} mL/min")
            print(f"Current volume: {total_millilitres:.2f} mL")

            pulse_count = 0
            old_time = current_time

except KeyboardInterrupt:
    # 프로그램 종료
    R.stop()
    G.stop()
    B.stop()
    for pin in pins.values():
        GPIO.output(pin, GPIO.HIGH)  # LED 끄기
    GPIO.cleanup()
