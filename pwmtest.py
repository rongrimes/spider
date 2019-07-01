#!/usr/bin/python3

import os
import RPi.GPIO as GPIO
import time
from sys import exit


# Set RPi ports
led_RED = 26

#---------------------------------------------------------------
def led_setup(pin_no):
    GPIO.setup(pin_no, GPIO.OUT)     # activate output
    pwm_led = GPIO.PWM(pin_no, 100) # duty cycle: 100Hz
    pwm_led.start(0)
    return pwm_led

def led_set(pin_no, value):
    pin_no.ChangeDutyCycle(value)

#---------------------------------------------------------------
def track_pir():
    while True:
            led_up(pwm_RED)   # slowest operation

#---------------------------------------------------------------------------------
# START HERE (Really!)
# Initialize the Pi
GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)     # Turn off warning if we didn't a GPIO cleanup

pwm_RED = led_setup(led_RED)   # activate pwm control

try:
    while True:
        value = input("LED Intensity (0-100): ")
        if len(value) == 0:
            continue
        try:
            value = float(value)
        except ValueError:
            continue

        if 0.0 <= value <= 100.0: 
            led_set(pwm_RED, value)
        print()

except KeyboardInterrupt:
    print()

GPIO.cleanup()           # clean up GPIO
