#!/usr/bin/python3
##!env python3

import datetime
import os
import RPi.GPIO as GPIO
import signal
import threading
import time
from sys import exit

# Local imports
from green_light import *
from sound_board import *

# Set RPi ports
pir_pin = 12
led_RED = 26
led_GRN = 6
led_BLU = 13

ospid_file = "/home/pi/python/spider/ospid.txt"

#---------------------------------------------------------------
def eyes_setup(pin_no):
    GPIO.setup(pin_no, GPIO.OUT)     # activate output
    pwm_eyes = GPIO.PWM(pin_no, 100)  # duty cycle: 100Hz
    pwm_eyes.start(0)
    return pwm_eyes

def eyes_up(pin_no):
    delay = 0.5   # seconds
    for eyes_level in eyes_intensity:
        pin_no.ChangeDutyCycle(eyes_level)
        time.sleep(delay)

def eyes_down(pin_no):
    delay = 0.5   # seconds
    for eyes_level in eyes_intensity[::-1]:
        pin_no.ChangeDutyCycle(eyes_level)
        time.sleep(delay)


#---------------------------------------------------------------
def flash_GB():
    ''' Flash Green/Blue LEDs in the eyes, and the white string of LEDs.'''
    slow_flash = 5       # seconds between flashes during quiet period
    fast_flash = 0.5     # seconds between flashes when animation_active is True

    print("flash_GB  thread:", thr_flasher.name)

    seconds = slow_flash            # force a flash on initialization
    while True:
        time.sleep(fast_flash)

        if my_globals.end_request:
            print("flash_GB shutting down")
            break
        if my_globals.animation_active or seconds >= slow_flash: # Flash every (slow_flash) seconds
            GPIO.output(led_GRN, GPIO.HIGH)
            GPIO.output(led_BLU, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(led_GRN, GPIO.LOW)
            GPIO.output(led_BLU, GPIO.LOW)
            seconds = 0
        else:
            seconds += fast_flash

#---------------------------------------------------------------
def track_pir():
    def tick_str(ticks):
        ticks = "{}".format(ticks)
        return ticks + len(ticks) * "\b"          # add equiv # of backspaces to back space over the number.

    wait_on = 6.5      # wait this long (seconds) to see it's a real mamalian critter or zombie (not guaranteed)
    pir_timeout = 100  # ms before wait_for_edge is to timeout.
    max_ticks = int(wait_on * 1000 / pir_timeout)  # ticks in (wait_on) seconds.

    print("track_pir thread:", thr_pir.name)
    
    # wait until PIR drops during initialization - may/may not be high
    while GPIO.input(pir_pin):
        time.sleep(1)
#   print("GPIO(PIR): "+ str(bool(GPIO.input(pir_pin)))) # True = HIGH

    green_light.set("off")

    while my_globals.end_request == False:     # not clear if this will ever be False, but the condition is handled in the loop.
        while True:
            if GPIO.wait_for_edge(pir_pin, GPIO.RISING, timeout=pir_timeout) is None:
                # we get a timeout - let's us handle a ^C
                if my_globals.end_request:
                    print("track_pir shutting down")
                    return
                continue

#           The PIR line has risen
            green_light.set("on")
            print("/ \b", end="", flush=True)

            to_ticks = 0                       # timeout_ticks
            while to_ticks < max_ticks:        # now let's wait to see if it drops within wait_on seconds.
                if GPIO.wait_for_edge(pir_pin, GPIO.FALLING, timeout=pir_timeout) is None:   # ie. we timeout
                    if my_globals.end_request:
                        print("track_pir shutting down")
                        return
                    pass # timeout, & pir line still high, now need to count ticks.
                else:     # line falls within short period, hence ignore and look for next rising signal.
                    break              # print report and and return to while True loop.
#               Line is high - let's see  if it's for long enough.
                to_ticks +=1 
            else:        # line is high, and we have exceeded max_ticks
                break    # out of while True loop

#           Line is down, but we are less than the ticks timeout period - hence don't activate the spider.
            green_light.set("off")
            report = "\\" + tick_str(to_ticks)
            print(report, end="", flush=True)

        curr_time = datetime.datetime.now().strftime('%H:%M:%S')
        print("\n>Rising  edge detected on port", str(pir_pin) + ",", curr_time)

        green_light.set("on")

        # Get spider parms
        my_globals.get_spider_parms()         # since they can change by s_parms.py outside the program.
        my_globals.animation_active = True    # Enable sound and start quick flashing

        if my_globals.spider_parms["ON"]:
            sound = threading.Thread(target=sound_board.play_sound, args=(my_globals, ))
            sound.start()

        eyes_up(pwm_RED)   # slow operation

        while my_globals.end_request == False:
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

        my_globals.animation_active = False   # Disable sound and stop quick flashing
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

# Set up globals and get spider_parms
my_globals = My_globals()
my_globals.animation_active = False   # (also) initialized in My_globals.__init__
my_globals.end_request      = False   # use to end the threads.

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

# Initialize sound board files
sound_board = Sound_board()

#set up threads and start.
thr_pir = threading.Thread(target=track_pir)   # tracks the PIR
thr_pir.start()

thr_flasher = threading.Thread(target=flash_GB)
thr_flasher.start()

#Generate eye intensities
eyes_steps = 16
max_int = my_globals.spider_parms["MAX_INT"]
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
    my_globals.end_request = True

# Wait for threads to clean up.
thr_pir.join()
thr_flasher.join()

# if the msg below appears, then I know the pir and flasher threads have ended.
green_light.init("mmc0")  # restore to showing "disk access" events.
print("\nGreen light default restored.")

GPIO.cleanup()           # clean up GPIO

if os.path.isfile(ospid_file):
    os.remove(ospid_file)
