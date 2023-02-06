#!/usr/bin/python3
##!env python3

# Installation Notes:
# ------------------
#
# The speakers are: Adafruit Speaker Bonnet for Raspberry Pi, see:
#    https://learn.adafruit.com/adafruit-speaker-bonnet-for-raspberry-pi
#
# Driver load instructions are at:
#    https://learn.adafruit.com/adafruit-speaker-bonnet-for-raspberry-pi/raspberry-pi-usage
#
# Sound player: mpg123
#    sudo apt install mpg123

import asyncio
import datetime
import os
import RPi.GPIO as GPIO
import signal
from sys import exit

# Local imports
#from green_light import *
#from sound_board import *
from sound_board import My_globals, Sound_board

# Set RPi ports
pir_pin = 12
#pir_pin = 19
led_RED = 13
led_GRN = 6
led_BLU = 26

wait_change = 0.1    # time to wait for pir to change before looking again.

ospid_file = "/home/pi/python/spider/ospid.txt"

#---------------------------------------------------------------
#   functions that do things - non async
def eyes_setup(pin_no):
    GPIO.setup(pin_no, GPIO.OUT)     # activate output
    pwm_eyes = GPIO.PWM(pin_no, 100)  # duty cycle: 100Hz
    pwm_eyes.start(0)
    return pwm_eyes

def make_eye_intensities(max_int):
    global eyes_intensity
    eyes_steps = 40
    eyes_intensity = {int(((10**(r/eyes_steps)-1)*max_int/9)+0.99) for r in range(0,eyes_steps+1)}
                       # exponential series {0..max_intensity} - created as a set to remove duplicates
    eyes_intensity = sorted(list(eyes_intensity))     # convert set to list to ensure sequencing.
                                                      # sort: since the set returns in undetermined order.
    print(eyes_intensity)
    return eyes_intensity 

# Arm signal to end program.
def handler(signum, frame):
    ''' A sigint interrupt will get caught here, and will in effect be the same as
        getting a ^C at the keyboard.'''
    raise KeyboardInterrupt

#---------------------------------------------------------------
#   async functions
async def eyes_change(pin_no, UP=True):
    eye_change_transition = 4 # seconds
    delay =  eye_change_transition / len(eyes_intensity)   # seconds
    direction = 1 if UP else -1

    for eyes_level in eyes_intensity[::direction]:
        pin_no.ChangeDutyCycle(eyes_level)
        await asyncio.sleep(delay)

async def flash_GB():
    ''' Flash Green/Blue LEDs in the eyes, and the white string of LEDs.'''
    slow_flash = 5       # seconds between flashes during quiet period
    fast_flash = 0.5     # seconds between flashes when animation_active is True

    print("flash_GB  co-routine")

    seconds = slow_flash            # force a flash on initialization
    while True:
        await asyncio.sleep(fast_flash)

        if my_globals.end_request:
            print("flash_GB shutting down")
            break
        if my_globals.animation_active or seconds >= slow_flash: # Flash every (slow_flash) seconds
            GPIO.output(led_GRN, GPIO.HIGH)
            GPIO.output(led_BLU, GPIO.HIGH)
            await asyncio.sleep(0.1)
            GPIO.output(led_GRN, GPIO.LOW)
            GPIO.output(led_BLU, GPIO.LOW)
            seconds = 0
        else:
            seconds += fast_flash

#---------------------------------------------------------------
async def track_pir():
    def tick_str(ticks):
        ticks = "{}".format(ticks)
        return ticks + len(ticks) * "\b"          # add equiv # of backspaces to back space over the number.

    wait_on = 7        # wait this long (seconds) to see it's a real mamalian critter or zombie (not guaranteed)
    max_ticks = int(wait_on * 1 / wait_change)  # ticks in (wait_on) seconds.

    print("track_pir co-routine")
    
    # wait until PIR drops during initialization - may/may not be high
    while GPIO.input(pir_pin):
        await asyncio.sleep(wait_change)

#   green_light.set("off")
    max_eye_intensity = my_globals.spider_parms["MAX_INT"]  # get MAX-INT so we can check for changes

    while True:     # main loop - only exited with a "return" statement.
        while True:
            if my_globals.end_request:
                print("track_pir shutting down")
                return

            # Wait for pir line to go high
            if GPIO.input(pir_pin) == False:
                await asyncio.sleep(wait_change)     # still quiet
                continue

#           The PIR line is now high: check for a false positive
#           green_light.set("on")
            print("/ \b", end="", flush=True)

            # Get spider parms
            my_globals.get_spider_parms()   # since they can change by
            if my_globals.spider_parms["MAX_INT"] != max_eye_intensity:
                max_eye_intensity = my_globals.spider_parms["MAX_INT"]
                eyes_intensity = make_eye_intensities(max_eye_intensity ) 

            my_globals.animation_active = True    # Enable sound and start quick flashing

            to_ticks = 0                       # timeout_ticks
            while to_ticks < max_ticks:        # now let's wait to see if it drops within wait_on seconds.
                if my_globals.end_request:
                    print("track_pir shutting down")
                    return

                await asyncio.sleep(wait_change)
                if GPIO.input(pir_pin):
                    to_ticks +=1  # pir line still high, increment ticks.
                else:     # line falls within short period... it's a false positive
                    break              # print report and and return to while True loop.

            else:        # line is high, and we have exceeded max_ticks - there is a critter out there.
                break    # out of while True loop

#           pir line is down, but we are less than the ticks timeout period - hence don't activate the spider.
#           green_light.set("off")
            report = "\\" + tick_str(to_ticks)
            print(report, end="", flush=True)
            my_globals.animation_active = False    # disable quick flashing

        curr_time = datetime.datetime.now().strftime('%H:%M:%S')
        print("\n>Rising  edge detected on port", str(pir_pin) + ",", curr_time)

        # Get spider parms
        my_globals.get_spider_parms()   # since they can change by
                                        # key_parms.py or s_parms.py outside the program.
        if my_globals.spider_parms["ON"]:
            sound = threading.Thread(target=sound_board.play_sound, args=(my_globals, ))
            sound.start()

        eyes_up(pwm_RED)   # slow operation

        while my_globals.end_request == False:
            if GPIO.input(pir_pin):
                await asyncio.sleep(wait_change)    # still high, continue animation
            else:
                break                      # pir dropped. Shutdown animation.
        else:
            print("track_pir shutting down")
            return

#       green_light.set("off")
        curr_time = datetime.datetime.now().strftime('%H:%M:%S')
        print(">Falling edge detected on port", str(pir_pin) + ",", curr_time)

        my_globals.animation_active = False   # Disable sound and stop quick flashing
        eyes_down(pwm_RED)   # slow operation

#---------------------------------------------------------------------------------
async def main():
    #  start flash routine
    co_flashgb = asyncio.create_task(flash_GB())
#   coros = [flash_GB(), eyes_change(), track_pir(), sound_board()]

    for _ in range(3):
        ta_eyes_ch = asyncio.create_task(eyes_change(pwm_RED, True))
        await ta_eyes_ch
        await asyncio.sleep(1)
        ta_eyes_ch = asyncio.create_task(eyes_change(pwm_RED, False))
        await ta_eyes_ch
        await asyncio.sleep(1)

    results = await co_flashgb

#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------
# START HERE (Really!)
print()                     # cosmetic: new line for when started from run_spider.sh

# See if we're already running.
if os.path.isfile(ospid_file):
    print("spider.py is already running.\nIf this message in error,",
            "remove the file:", ospid_file)
    exit()

# Set up globals and get spider_parms
my_globals = My_globals()
my_globals.animation_active = False   # (also) initialized in My_globals.__init__
my_globals.end_request      = False   # use to end the threads.

# Arm sigint to cause proceed to graceful end.
signal.signal(signal.SIGINT, handler)

# Initialize the Pi
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)     # Turn off warning if we didn't a GPIO cleanup

# Initialise board green light 
#green_light = Green_Light(Reverse=True)   # "Reverse" required on the Pi zero W
#green_light.set("off")

#Generate eye intensities
eyes_intensity = make_eye_intensities(my_globals.spider_parms["MAX_INT"])

pwm_RED = eyes_setup(led_RED)   # activate pwm control
GPIO.setup(led_GRN, GPIO.OUT)  # activate output
GPIO.setup(led_BLU, GPIO.OUT)  # activate output

# Init PIR Control
GPIO.setup(pir_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # activate input

# Initialize sound board files
sound_board = Sound_board()

# Set a beacon to show we're running
# We store the process id here - used in 2 places:
# 1. We check in spider to see if we're already running. (code above)
# 2. Used in the kill_spider.sh  script to send a SIGINT to the program.

# Needs to appear after Green light initialization since Green light
# can kill the startup.
#with open(ospid_file, "w") as f:
#   f.write(str(os.getpid()))

#-----------------------------
#set up coroutines/tasks and start.
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nKeyboardInterrupt received")

#-----------------------------
# Cleanup our stuff

# restore greenlight to showing "disk access" events.
#green_light.init("mmc0")
#print("\nGreen light default restored.")

GPIO.cleanup()           # clean up GPIO

if os.path.isfile(ospid_file):
    os.remove(ospid_file)
