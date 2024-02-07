import RPi.GPIO as GPIO
import time

# GPIO 핀 번호 설정 모드
GPIO.setmode(GPIO.BCM)

# RGB LED 핀 할당
pins = {'R': 17, 'G': 27, 'B': 22}

# RGB 핀을 출력으로 설정
for pin in pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)  # LED를 끄기 위해 일단 모든 핀을 HIGH로 설정

# PWM 인스턴스 생성
R = GPIO.PWM(pins['R'], 2000)  # 2kHz
G = GPIO.PWM(pins['G'], 2000)  # 2kHz
B = GPIO.PWM(pins['B'], 2000)  # 2kHz

# PWM 시작. Duty Cycle = 100 (LED OFF), 0(LED ON)
R.start(100)
G.start(100)
B.start(100)

# 색상 변경 함수
def set_color(r, g, b):
    R.ChangeDutyCycle(r)
    G.ChangeDutyCycle(g)
    B.ChangeDutyCycle(b)

try:
    while True:
        # 색상 예제
        set_color(98, 100, 100)  # 빨간색
        time.sleep(1)
        set_color(100, 98, 100)  # 초록색
        time.sleep(1)
        set_color(100, 100, 98)  # 파란색
        time.sleep(1)
        #set_color(99, 99, 99)  # 흰색
        # time.sleep(1)
        set_color(100,100, 100)  # 끄기
        time.sleep(1)

except KeyboardInterrupt:
    # 프로그램 종료
    R.stop()
    G.stop()
    B.stop()
    for pin in pins.values():
        GPIO.output(pin, GPIO.HIGH)  # LED 끄기
    GPIO.cleanup()