#!/usr/bin/python3
##!env python3

import datetime
import json
import os
import RPi.GPIO as GPIO
import signal
import subprocess
import threading
import time
from sys import exit
#from random import randint

# Local imports
from green_light import *
from sound_board import *

# Set RPi ports
pir_pin = 12
led_RED = 26
led_GRN = 6
led_BLU = 13

spider_parmfile = "spiderparms.json"
spider_parms = {"ON": False,
        "VOLUME":10000,     # 0 <= VOLUME  <= 32768
        "MAX_INT":25 }      # 0 <= MAX_INT <= 100

ospid_file = "/home/pi/python/spider/ospid.txt"
log_file = "/home/pi/python/spider/logfile.txt"

#---------------------------------------------------------------
def eyes_setup(pin_no):
    GPIO.setup(pin_no, GPIO.OUT)     # activate output
    pwm_eyes = GPIO.PWM(pin_no, 100)  # duty cycle: 100Hz
    pwm_eyes.start(0)
    return pwm_eyes

def eyes_up(pin_no):
    global active_RED

    for eyes_level in eyes_intensity:
        pin_no.ChangeDutyCycle(eyes_level)
        time.sleep(0.2)
    active_RED = True    # Start single flashing

def eyes_down(pin_no):
    global active_RED

    active_RED = False   # Stop single flashing
    for eyes_level in eyes_intensity[::-1]:
        pin_no.ChangeDutyCycle(eyes_level)
        time.sleep(0.2)


#---------------------------------------------------------------
def flash_GB():
    global active_RED
    period = 10   # count of seconds during quiet period

    print("flash_GB  thread:", thr_flasher.name)

    seconds = 0
    while True:
        time.sleep(2)

        if end_request:
            print("flash_GB shutting down")
            break
        if active_RED or seconds >= period: # Flash every 10 seconds
            GPIO.output(led_GRN, GPIO.HIGH)
            GPIO.output(led_BLU, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(led_GRN, GPIO.LOW)
            GPIO.output(led_BLU, GPIO.LOW)
            seconds = 0
        else:
            seconds += 2

#---------------------------------------------------------------
def get_spider_parms():
    global spider_parms

    try:
        with open(spider_parmfile, "r") as f:
            spider_parms = json.load(f)
    except FileNotFoundError:
        # instead, use the defaults defined above
        print(spider_parmfile, "file not found.")

#---------------------------------------------------------------
def start_sound():
    sound = threading.Thread(target=sound_board, args=(spider_parms, ) )
    sound.start()

def track_pir():
    global spider_parms
    def exit_or_edge(edge): # True = exit request, False = edge
        while True:
            if end_request or \
                    GPIO.wait_for_edge(pir_pin, edge, timeout=250) \
                            is not None: # we timeout
                return end_request

    print("track_pir thread:", thr_pir.name)
    
    # wait until PIR drops
    while GPIO.input(pir_pin):
        time.sleep(1)
#   print("GPIO(PIR): "+ str(bool(GPIO.input(pir_pin)))) # True = HIGH

    green_light.set("off")
    while True:
#       print(GPIO.input(pir_pin)) # True = HIGH
        if GPIO.input(pir_pin): # True = HIGH
            if exit_or_edge(GPIO.FALLING):
                break
            pir_off_event.set()

            curr_time = datetime.datetime.now().strftime('%H:%M:%S')
            print(">Falling edge detected on port", str(pir_pin) + ",", curr_time)

            green_light.set("off")
            eyes_down(pwm_RED)   # slowest operation
        else:
            if exit_or_edge(GPIO.RISING):
                break
            pir_on_event.set()

            curr_time = datetime.datetime.now().strftime('%H:%M:%S')
            print(">Rising  edge detected on port", str(pir_pin) + ",", curr_time)

            green_light.set("on")

            # Get spider parms
            get_spider_parms()         # since they can change outide the program.
            if spider_parms["ON"]:
                start_sound()

            eyes_up(pwm_RED)   # slowest operation


    print("track_pir shutting down")

#---------------------------------------------------------------------------------
# START HERE (Really!)
# See if we're already running.
if os.path.isfile(ospid_file):
    print("spider.py is already running.\nIf this message in error,",
            "remove the file:", ospid_file)
    with open(log_file, "w") as f:
        f.write("spider.py is already running.\nIf this message in error," \
                "remove the file:" + ospid_file + "\n") 
    exit()

with open(ospid_file, "w") as f:
    f.write(str(os.getpid()))

# Initialize the Pi
GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)     # Turn off warning Cif we didn't a GPIO cleanup

pwm_RED = eyes_setup(led_RED)   # activate pwm control
GPIO.setup(led_GRN, GPIO.OUT)  # activate output
GPIO.setup(led_BLU, GPIO.OUT)  # activate output

# Initialise board green light 
green_light = Green_Light(Reverse=True)   # required on the Pi zero W
green_light.set("off")

# Init PIR Control
GPIO.setup(pir_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # activate input

active_RED = False
end_request = False   # use to end the threads.

# Init thread events
pir_on_event = threading.Event()   # event set when pir comes on
pir_on_event.clear()
pir_off_event = threading.Event()  # event set when pir goes off
pir_off_event.clear()


#set up threads and start.
thr_pir = threading.Thread(target=track_pir)   # tracks the PIR
thr_pir.start()

thr_flasher = threading.Thread(target=flash_GB)
thr_flasher.start()

#-----------------------------
# Get spider parms
get_spider_parms()

eyes_steps = 20
max_int = spider_parms["MAX_INT"]
eyes_intensity = [((10**(r/eyes_steps)-1)*max_int/9) for r in range(0,eyes_steps+1)]
                   # exponential series [0..100]
print(eyes_intensity)

#-----------------------------

try:
    while True:
        time.sleep(1)
                
except KeyboardInterrupt:
    end_request = True

green_light.init("mmc0")  # restore to showing "disk access" events.
print("\nGreen light default restored.")

# Wait for threads to clean up.
thr_pir.join()
thr_flasher.join()

GPIO.cleanup()           # clean up GPIO

if os.path.isfile(ospid_file):
    os.remove(ospid_file)
if os.path.isfile(log_file):
    os.remove(log_file)
