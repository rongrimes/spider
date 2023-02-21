#!/usr/bin/python3
##!env python3

import json
import os
import RPi.GPIO as GPIO
import sys
import signal
import subprocess
from time import sleep

# Set RPi ports
key_A = 22
key_B = 27
key_C = 17
key_D = 4
 
spider_parmfile = "/home/pi/python/spider/spiderparms.json"
speech_loc      = "/home/pi/python/spider/speech/"
voices_file     = speech_loc + "speech_legend.json"

voice_volume = 40000      # range: 0 - max  (1000000?)
max_volume   = 1000000    # range: 0 - max  (1000000?)

max_eye_intensity = 80    # max is 100, but may draw too much power.
min_eye_intensity = 40

#default values
spider_parms = {"SOUND_ON": False, "VOLUME":10000, "MAX_INT":25,
                "END_REQUEST": False} # 0 <= VOLUME  <= 100000+

#---------------------------------------------------------------
def get_spider_parms():
    global spider_parms
    try:
        with open(spider_parmfile, "r") as f:
            spider_parms = json.load(f)
    except FileNotFoundError:
        print(spider_parmfile + ": not found. Using defaults.")
        # use defaults defined above
        pass

#---------------------------------------------------------------
def put_spider_parms():
    global spider_parms
    with open(spider_parmfile, "w") as f:
        json.dump(spider_parms, f)

#---------------------------------------------------------------------------------
# load voices structure
def get_voices_file():
    global voices
    try:
        with open(voices_file, "r") as f:
            voices = json.load(f)
    except FileNotFoundError:
        print(voices_file + ": not found. key_parms.py is now terminating.")
        sys.exit()

#---------------------------------------------------------------------------------
# set sound: T/F
def set_sound():
    global spider_parms

    changed = False
    speak("08-Press-A-Sound")
    speak("11-Press-D-Exit")

    while True:
        if spider_parms["SOUND_ON"]:
            speak("09-Sound-On")
        else:
            speak("10-Sound-Off")

        while True:
            letter = get_letter()
            if letter == "A":
                spider_parms["SOUND_ON"] = not spider_parms["SOUND_ON"] 
                changed = True
                break

            if letter == "D":
                return changed

#---------------------------------------------------------------------------------
def volume_increase(volume):
    if volume == 0:
        return 1000
    volume += max(int(volume * 0.25), 10000)
    return round(min(volume, max_volume), -3)

def volume_decrease(volume):
    volume -= max(int(volume * 0.25), 10000)
    return round(max(0, volume), -3)

def set_volume():
    global spider_parms

    changed = False

    if spider_parms["VOLUME"] == 0:
        speak("10-Sound-Off")
    elif spider_parms["VOLUME"] == max_volume:
        speak("15-Sound-Max")

#   Read menu
    speak("18-Press-AC-IncrDecr")
    speak("19-Press-B-Play")
    speak("11-Press-D-Exit")

    while True:
        letter = get_letter()
        if letter == "A":
            spider_parms["VOLUME"] = volume_increase(spider_parms["VOLUME"])
            if spider_parms["VOLUME"] == max_volume:
                speak("15-Sound-Max")
            else:
                speak("16-Volume-Up", volume=spider_parms["VOLUME"])
            changed = True
            continue

        if letter == "C":
            spider_parms["VOLUME"] = volume_decrease(spider_parms["VOLUME"])
            if spider_parms["VOLUME"] == 0:
                speak("10-Sound-Off")
            else:
                speak("17-Volume-Down", volume=spider_parms["VOLUME"])
            changed = True
            continue

        if letter == "B":
            speak("01-Hello-Spider", volume=spider_parms["VOLUME"])
            continue

        if letter == "D":
            return changed


#---------------------------------------------------------------------------------
# set eye intensity values.
def eye_increase(intensity):
    intensity += 10
    return min(intensity, max_eye_intensity)

def eye_decrease(intensity):
    intensity -= 10
    return max(min_eye_intensity, intensity)

def set_eyepower():
    global spider_parms

    changed = False
#   Read menu
    speak("25-Press-AC-IncrDecr-Eye")
    speak("11-Press-D-Exit")

    while True:
        letter = get_letter()
        if letter == "A":
            spider_parms["MAX_INT"] = eye_increase(spider_parms["MAX_INT"])
            if spider_parms["MAX_INT"] >= max_eye_intensity:
                speak("21-Eye-Max")
            else:
                speak("23-Eye-Up")
            changed = True
            continue

        if letter == "C":
            spider_parms["MAX_INT"] = eye_decrease(spider_parms["MAX_INT"])
            if spider_parms["MAX_INT"] <= min_eye_intensity:
                speak("22-Eye-Min")
            else:
                speak("24-Eye-Down")
            changed = True
            continue

        if letter == "D":
            return changed

#---------------------------------------------------------------------------------
# get input
def get_letter():
    while True:
        for key, letter in [(key_A, "A"), (key_B, "B"), (key_C, "C"), (key_D, "D")]:
            if GPIO.input(key):  # check key
                return letter
        sleep(0.1)      # 100ms

#---------------------------------------------------------------------------------
# Wait for D key
def wait_for_D():
    only_D = True
    while get_letter() != "D":
        only_D = False
    return only_D

#---------------------------------------------------------------------------------
def speak(voice_key, volume=voice_volume):
    if voice_key not in voices["files"]:
        print("speak: voice_key not found:" , voice_key)
        return

    sound_file = speech_loc + voices["files"][voice_key]["filename"]
    mpg123 = "exec sudo -u pi mpg123 -q -f " + str(volume) + " " + sound_file

    popen = subprocess.Popen(mpg123, stdout=subprocess.PIPE, shell=True,
        preexec_fn=os.setsid)
    popen.wait()

#---------------------------------------------------------------------------------
def shutdown_spider():
    speak("07-Goodbye")

    spider_parms["END_REQUEST"] = True
    put_spider_parms()
    sleep(3)         # sleep to endure spider comes down.
    # and rest to false for next startup
    spider_parms["END_REQUEST"] = False
    put_spider_parms()

    command = "/usr/bin/sudo /sbin/shutdown now"
    popen = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = popen.communicate()[0]
    print(output)
    popen.wait()
    sleep(100)

#---------------------------------------------------------------------------------
# Arm signal to end program.
def sig_handler(signum, frame):
    ''' A sigint interrupt will get caught here, and will in effect be the same as
        getting a ^C at the keyboard.'''
    raise KeyboardInterrupt

#---------------------------------------------------------------
# Initialize the Pi
GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)     # Turn off warning if we didn't a GPIO cleanup

# Arm sigint to cause proceed to graceful end.
signal.signal(signal.SIGINT, sig_handler)

# Init key lines
for key in [key_A, key_B, key_C, key_D]:
    GPIO.setup(key, GPIO.IN)  # activate input - don't use pull_up_down

sleep(5)     #  Need this sleep to have the sound card stabilize after a reboot. Not necessary 
             #     after just a simple reboot.

# Get voice file
get_voices_file()
speak("01-Hello-Spider")

# Get spider parms
get_spider_parms()
d_count = 0

try:
    while True:
        speak("02-Press-D-Attention")
        only_D = wait_for_D()
        if only_D and d_count >= 2 :
            shutdown_spider()

        d_count = 0
        speak("12-Press-D-Menu")

        while True:
            key = get_letter()
            if key == "A":
                changed = set_sound()
                break
            elif key == "B":
                changed = set_volume()
                break
            elif key == "C":
                changed = set_eyepower()
                break
            elif key == "D":
                d_count += 1 
                if d_count >= 2:
                    break
                changed = False
                speak("08-Press-A-Sound")
                speak("13-Press-B-Volume")
                speak("14-Press-C-Eye")
                speak("11-Press-D-Exit")

        if changed:
            speak("20-Values-Changed")
            put_spider_parms()
            sleep(0.5)         # cosmetic pause before next sound message.

except KeyboardInterrupt:
    print()

GPIO.cleanup()           # clean up GPIO
