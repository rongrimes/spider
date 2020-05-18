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

#---------------------------------------------------------------
def eyes_setup(pin_no):
    GPIO.setup(pin_no, GPIO.OUT)     # activate output
    pwm_eyes = GPIO.PWM(pin_no, 100)  # duty cycle: 100Hz
    pwm_eyes.start(0)
    return pwm_eyes

def eyes_up(pin_no):
    global active_RED

    delay = 0.5
    for eyes_level in eyes_intensity:
        pin_no.ChangeDutyCycle(eyes_level)
        time.sleep(delay)
    active_RED = True    # Start quick flashing

def eyes_down(pin_no):
    global active_RED

    delay = 0.5
    active_RED = False   # Stop quick flashing
    for eyes_level in eyes_intensity[::-1]:
        pin_no.ChangeDutyCycle(eyes_level)
        time.sleep(delay)


#---------------------------------------------------------------
def flash_GB():
    ''' Flash Green/Blue LEDs in the eyes, and the white string of LEDs.'''
    global active_RED

    slow_flash = 5       # seconds between flashes during quiet period
    fast_flash = 0.5     # seconds between flashes when active_RED is True

    print("flash_GB  thread:", thr_flasher.name)

    seconds = slow_flash            # force a flash on initialization
    while True:
        time.sleep(fast_flash)

        if end_request:
            print("flash_GB shutting down")
            break
        if active_RED or seconds >= slow_flash: # Flash every (slow_flash) seconds
            GPIO.output(led_GRN, GPIO.HIGH)
            GPIO.output(led_BLU, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(led_GRN, GPIO.LOW)
            GPIO.output(led_BLU, GPIO.LOW)
            seconds = 0
        else:
            seconds += fast_flash

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

    wait_on = 5      # wait this long (seconds) to see it's a real mamalian critter or zombie (not guaranteed)
    pir_timeout = 100  # ms before wait_for_edge is to timeout.
    max_ticks = wait_on * int(1000 / pir_timeout)  # ticks in (wait_on) seconds.

    print("track_pir thread:", thr_pir.name)
    
    # wait until PIR drops during initialization - may/may not be high
    while GPIO.input(pir_pin):
        time.sleep(1)
#   print("GPIO(PIR): "+ str(bool(GPIO.input(pir_pin)))) # True = HIGH

    green_light.set("off")

    while end_request == False:     # not clear if this will ever be False, but the condition is handled in the loop.
        while True:
            if GPIO.wait_for_edge(pir_pin, GPIO.RISING, timeout=pir_timeout) is None:
                # we get a timeout - let's us handle a ^C
                if end_request:
                    print("track_pir shutting down")
                    return
                continue

#           The PIR lne has risen
            to_ticks = 0                       # timeout_ticks
            while to_ticks < max_ticks:        # now let's wait to see if it drops within wait_on seconds.
                if GPIO.wait_for_edge(pir_pin, GPIO.FALLING, timeout=pir_timeout) is None:   # ie. we timeout
                    if end_request:
                        print("track_pir shutting down")
                        return
                    pass # timeout, & pir line still high, now need to count ticks.
                else:     # line falls within short period, hence ignore and look for next rising signal.
                    break              # and return to while True loop.
#               Line is high - let's see  if it's for long enough.
                to_ticks +=1 
            else:        # line is high, and we have exceeded max_ticks
                break    # out of while True loop

        curr_time = datetime.datetime.now().strftime('%H:%M:%S')
        print(">Rising  edge detected on port", str(pir_pin) + ",", curr_time)

        green_light.set("on")

        # Get spider parms
        get_spider_parms()         # since they can change outside the program.
        if spider_parms["ON"]:
            start_sound()

        eyes_up(pwm_RED)   # slow operation

        while end_request == False:
            if GPIO.wait_for_edge(pir_pin, GPIO.FALLING, timeout=pir_timeout) is None:
                continue       # let's us handle a ^C
            break
        else:
            print("track_pir shutting down")
            return

        GPIO.output(led_BLU, GPIO.LOW)
        curr_time = datetime.datetime.now().strftime('%H:%M:%S')
        print(">Falling edge detected on port", str(pir_pin) + ",", curr_time)
        green_light.set("off")

        eyes_down(pwm_RED)   # slow operation

#---------------------------------------------------------------------------------
# Arm signal to end program.
def handler(signum, frame):
    ''' A sigint interrupt will get caught here, and will in effect be the same as
        getting a ^C at the keyboard.'''
    raise KeyboardInterrupt

#---------------------------------------------------------------------------------
# START HERE (Really!)
print()                     # cosmetic: new line for when started from run_spider.sh

# See if we're already running.
if os.path.isfile(ospid_file):
    print("spider.py is already running.\nIf this message in error,",
            "remove the file:", ospid_file)
    exit()

# We store the process id here - used in 2 places:
# 1. We check in spider to see if we're already running. (code above)
# 2. Used in the kill_spider.sh  script to send a signint to the program.

with open(ospid_file, "w") as f:
    f.write(str(os.getpid()))

# Initialize the Pi
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)     # Turn off warning if we didn't a GPIO cleanup

pwm_RED = eyes_setup(led_RED)   # activate pwm control
GPIO.setup(led_GRN, GPIO.OUT)  # activate output
GPIO.setup(led_BLU, GPIO.OUT)  # activate output

# Initialise board green light 
green_light = Green_Light(Reverse=True)   # "Reverse" required on the Pi zero W
green_light.set("off")

# Init PIR Control
GPIO.setup(pir_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # activate input

active_RED = False
end_request = False   # use to end the threads.

# Init thread events
#pir_on_event = threading.Event()   # event set when pir comes on
#pir_on_event.clear()
#pir_off_event = threading.Event()  # event set when pir goes off
#pir_off_event.clear()


#set up threads and start.
thr_pir = threading.Thread(target=track_pir)   # tracks the PIR
thr_pir.start()

thr_flasher = threading.Thread(target=flash_GB)
thr_flasher.start()

#-----------------------------
# Get spider parms
get_spider_parms()

eyes_steps = 16
max_int = spider_parms["MAX_INT"]
eyes_intensity = [int(((10**(r/eyes_steps)-1)*max_int/9)+0.99) for r in range(0,eyes_steps+1)]
                   # exponential series [0..max_intensity]
print(eyes_intensity)

#-----------------------------
# Arm sigint to cause proceed to graceful end.
signal.signal(signal.SIGINT, handler)

try:
    while True:
        time.sleep(0.1)
                
except KeyboardInterrupt:
    end_request = True

# Wait for threads to clean up.
thr_pir.join()
thr_flasher.join()

# if the msg below appears, then I know the pir and flsher treds have ended.
green_light.init("mmc0")  # restore to showing "disk access" events.
print("\nGreen light default restored.")

GPIO.cleanup()           # clean up GPIO

if os.path.isfile(ospid_file):
    os.remove(ospid_file)
