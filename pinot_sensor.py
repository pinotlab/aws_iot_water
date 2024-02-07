import RPi.GPIO as GPIO
import time

# GPIO 핀 번호 설정 모드
GPIO.setmode(GPIO.BCM)

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

try:
    while True:
        if time.time() - old_time > 1:
            flow_rate = (pulse_count / calibration_factor) / (time.time() - old_time) * 60
            flow_millilitres = (flow_rate / 60) * 16700
            total_millilitres += flow_millilitres

            # 유량 변화에 따른 LED 색상 변경
            if flow_rate > 0:
                set_color(100, 0, 100)  # 초록색
            else:
                set_color(0, 100, 100)  # 빨간색

            print(f"Flow rate: {flow_rate:.2f} mL/min")
            print(f"Total volume: {total_millilitres/1000:.2f} mL")

            pulse_count = 0
            old_time = time.time()

except KeyboardInterrupt:
    # 프로그램 종료
    R.stop()
    G.stop()
    B.stop()
    for pin in pins.values():
        GPIO.output(pin, GPIO.HIGH)  # LED 끄기
    GPIO.cleanup()
