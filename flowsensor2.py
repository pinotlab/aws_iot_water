import RPi.GPIO as GPIO
import time

sensor_pin = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pulse_count = 0
calibration_factor = 5.5
flow_rate = 0.0
flow_millilitres = 0
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
            
            print(f"Flow rate: {flow_rate:.2f} mL/min")
            # print(f"Output Liquid Quantity: {total_millilitres:.2f} mL")
            print(f"{total_millilitres/1000:.2f} mL")
            
            pulse_count = 0
            old_time = time.time()

except KeyboardInterrupt:
    GPIO.cleanup()
