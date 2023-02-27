#!/usr/bin/python3
##!env python3

import asyncio
import json
import os
import RPi.GPIO as GPIO
import sys
import signal
import subprocess
from time import sleep

speech_loc      = "/home/pi/python/spider/speech/"
voices_file     = speech_loc + "speech_legend.json"
sound_dir       = "/home/pi/python/spider/clips/"
sound_parmfile  = sound_dir + "soundparms.json"

voice_volume = 40000      # range: 0 - max  (1000000?)
max_volume   = 40000    # range: 0 - max
max_volume_limit = 60000 # can scale up the volume but limit it to this.

#---------------------------------------------------------------
def get_sound_parms():
    try:
        with open(sound_parmfile, "r") as f:
            sound_clips = json.load(f)
    except FileNotFoundError:
        print(sound_parmfile + ": not found. Reloading.")
        sound_clips = load_clips()
    return sound_clips

#---------------------------------------------------------------
def put_sound_parms(sound_clips):
    with open(sound_parmfile, "w") as f:
        json.dump(sound_clips, f, indent=2)

#---------------------------------------------------------------------------------
# load voices structure
def get_voices_file():
    global voices
    try:
        with open(voices_file, "r") as f:
            voices = json.load(f)
    except FileNotFoundError:
        print(voices_file + ": not found. play_sound.py is now terminating.")
        sys.exit()

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
def print_clips(sound_clips):
    for i, f in enumerate(sound_clips):
        print(f"{i}\t{f}")
    print()
        
def load_clips():
    sound_clips = []
    if not os.path.isdir(sound_dir):
        print(sound_dir + ": Sound dir does not exist.")
        return sound_clips # dir doesn't exist,
                          #    return empty list = no sound files
    for file in os.listdir(sound_dir):
        _, file_extension = os.path.splitext(file)     # discard filename part
        if  file_extension[1:] in {"mp3"}:    # set of allowed sound files
            entry = [sound_dir + file, 1.0]   # it would be nicer as a tuple, but we can't store
                                              #     it in a json file.
            sound_clips.append(entry)

    print_clips(sound_clips)
    return sound_clips

#---------------------------------------------------------------------------------
def play_sound(clip, volume):
    print(f"volume = {int(volume)}")
    mpg123 = "exec sudo -u pi mpg123 -q -f " + str(volume) + " " + clip

    popen = subprocess.Popen(mpg123, stdout=subprocess.PIPE, shell=True,
        preexec_fn=os.setsid)
    popen.wait()
#---------------------------------------------------------------------------------
# Arm signal to end program.
def sig_handler(signum, frame):
    ''' A sigint interrupt will get caught here, and will in effect be the same as
        getting a ^C at the keyboard.'''
    raise KeyboardInterrupt

#---------------------------------------------------------------
# Arm sigint to cause proceed to graceful end.
signal.signal(signal.SIGINT, sig_handler)

# Get the sound files
sound_clips =  get_sound_parms()
#put_sound_parms(sound_clips)

# Get voice file
get_voices_file()
speak("01-Hello-Spider")

try:
    while True:
        try:
            istr = input("Get sound # (empty reprints the lists): ")
            if istr == "":
                print_clips(sound_clips)
                continue
            indx = int(istr)

            # test indx value & trap if bad.
#           _ = sound_clips[indx]
            clip = sound_clips[indx][0]

            istr = input("Volume Level (0-40000, def=10000): ")
            if istr == "":
                volume = 10000
            else:
                volume = int(istr)
        except (ValueError, IndexError):
            print()
            continue

        if volume > max_volume:
            print()
            continue
        volume *= sound_clips[indx][1]   # scale up volume as needed.
        volume = min(volume,  max_volume_limit)
        play_sound(clip, volume)
        print()

except KeyboardInterrupt:
    print()

#GPIO.cleanup()           # clean up GPIO
