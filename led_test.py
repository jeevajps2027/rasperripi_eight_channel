import RPi.GPIO as GPIO
import time

led_pin = 4  # GPIO 4 (physical pin 7)

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin, GPIO.OUT)

try:
    # Continuous blinking
    while True:
        GPIO.output(led_pin, GPIO.HIGH)
        print("LED ON")
        time.sleep(0.1)
        GPIO.output(led_pin, GPIO.LOW)
        print("LED OFF")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Program stopped by user")

finally:
    GPIO.output(led_pin, GPIO.LOW)  # Ensure LED is OFF
    GPIO.cleanup()
    print("GPIO cleaned up, LED off")
