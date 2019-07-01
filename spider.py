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

# Set RPi ports
pir_pin = 12
led_RED = 26
led_GRN = 6
led_BLU = 13

spider_parmfile = "spiderparms.json"
spider_parms = {"ON": False,
        "VOLUME":10000,     # 0 <= VOLUME  <= 32768
        "MAX_INT":25 }      # 0 <= MAX_INT <= 100

sound_dir = "/home/pi/python/spider"        # don't use ~pi form - fails!
sound_time = 8    # play sound for * seconds

ospid_file = "/home/pi/python/spider/ospid.txt"
log_file = "/home/pi/python/spider/logfile.txt"

#---------------------------------------------------------------
def led_setup(pin_no):
    GPIO.setup(pin_no, GPIO.OUT)     # activate output
    pwm_led = GPIO.PWM(pin_no, 100)  # duty cycle: 100Hz
    pwm_led.start(0)
    return pwm_led

def led_up(pin_no):
    global active_RED

    for led_level in led_intensity:
        pin_no.ChangeDutyCycle(led_level)
        time.sleep(0.2)
    active_RED = True    # Start single flashing

def led_down(pin_no):
    global active_RED

    active_RED = False   # Stop single flashing
    for led_level in led_intensity[::-1]:
        pin_no.ChangeDutyCycle(led_level)
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
        # use defaults defined above
        print("spider_parms file not found.")
        pass

#---------------------------------------------------------------
def sound_board():
    global spider_parms
    global sound_index

    def make_sound_list(sound_dir):
        sound_list = []
        if os.path.isdir(sound_dir):
            os.chdir(sound_dir)
        else:
            print(sound_dir + ": Sound dir does not exist.")
            return sound_list # dir doesn't exist,
                              #    return empty list = no sound files
        for file in os.listdir("."):
            _, file_extension = os.path.splitext(file)     # discard filename part
            if  file_extension[1:] in {"mp3"}:    # set of allowed sound files
                sound_list.append(sound_dir + "/" + file)
        print("Sound list: ", sound_list)
        return sound_list

    def get_sound_file(sound_list):
        global sound_index
#       return sound_list[randint(0, len(sound_list) - 1)]   # randomises the list
        sound_index -= 1
        if sound_index < 0:
            sound_index = len(sound_list) - 1
        print(sound_list[sound_index])
        return sound_list[sound_index]

    def kill_sound():
        try:
            os.killpg(os.getpgid(pid.pid), signal.SIGTERM)
                                # Send the signal to all the process groups
        except NameError:       # pid hasn't been defined yet - that's OK.
            pass

    def exit_or_sound_ev(): # True = exit request, False = edge
        while True:
            if end_request or \
                    play_sound.wait(timeout=0.25): # False means we timeout
                return end_request

    print("sound     thread:", sound.name)

    sound_list = make_sound_list(sound_dir)
    sound_index = len(sound_list)

    while len(sound_list) > 0:    # invariant in loop, but proc will exit if empty.
        if exit_or_sound_ev(): 
            kill_sound()
            break

        play_sound.clear()
        sound_file = get_sound_file(sound_list)

        mpg123 = "exec sudo -u pi mpg123 -f " + str(spider_parms["VOLUME"]) \
                + " " + sound_file

        pid = subprocess.Popen(mpg123, stdout=subprocess.PIPE, shell=True,
                preexec_fn=os.setsid)
#       print("pid=", pid.pid)
        time.sleep(sound_time)

        kill_sound()

        if end_request:
            break

    print("sound shutting down")

#---------------------------------------------------------------
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
            led_down(pwm_RED)   # slowest operation
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
                play_sound.set()

            led_up(pwm_RED)   # slowest operation


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

pwm_RED = led_setup(led_RED)   # activate pwm control
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
play_sound = threading.Event()  # event to cause sound to fire
play_sound.clear()


#set up threads and start.
thr_pir = threading.Thread(target=track_pir)   # tracks the PIR
thr_pir.start()

thr_flasher = threading.Thread(target=flash_GB)
thr_flasher.start()

sound = threading.Thread(target=sound_board)
sound.start()

#-----------------------------
# Get spider parms
get_spider_parms()

led_steps = 20
max_int = spider_parms["MAX_INT"]
led_intensity = [int((10**(r/led_steps)-1)*max_int/9) for r in range(0,led_steps+1)]
                   # exponential series [0..100]
print(led_intensity)

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
sound.join()

GPIO.cleanup()           # clean up GPIO

if os.path.isfile(ospid_file):
    os.remove(ospid_file)
if os.path.isfile(log_file):
    os.remove(log_file)
