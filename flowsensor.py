import RPi.GPIO as GPIO
import time

# GPIO 핀 번호 설정
flow_sensor_pin = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(flow_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

global count
count = 0

# 펄스 카운트 콜백 함수
def count_pulse(channel):
    global count
    count += 1

# 인터럽트 설정
GPIO.add_event_detect(flow_sensor_pin, GPIO.FALLING, callback=count_pulse)

try:
    while True:
        time.sleep(1)
        print("펄스 수: ", count)
        # 여기서 유량 계산을 수행할 수 있습니다.
        # 예: 유량센서가 450 펄스/리터를 가진다고 가정하면,
        # flow_rate = count / 450
        # count 초기화
        count = 0

except KeyboardInterrupt:
    GPIO.cleanup()
