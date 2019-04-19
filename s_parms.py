#!/usr/bin/python3
##!env python3

import json
import os
import signal
import subprocess

sound_parmfile = "soundparms.json"

#default values
sound_parms = {"ON": False, "VOLUME":10000} # 0 <= VOLUME  <= 32768

#---------------------------------------------------------------
def get_sound_parms():
    global sound_parms
    try:
        with open(sound_parmfile, "r") as f:
            sound_parms = json.load(f)
    except FileNotFoundError:
        # use defaults defind above
        pass

#---------------------------------------------------------------
def put_sound_parms():
    global sound_parms
    with open(sound_parmfile, "w") as f:
        json.dump(sound_parms, f)

#---------------------------------------------------------------
# Get sound parms
get_sound_parms()

try:
    while True:
        value = input("Sound T/F [" + str(sound_parms["ON"]) + "]: ")
        if len(value) == 0:
            break
        if value.lower() == "true"[:len(value)]: 
            sound_parms["ON"] = True
            break
        if value.lower() == "false"[:len(value)]: 
            sound_parms["ON"] = False
            break

    while True:
        value = input("Volume (0-32768) [" + str(sound_parms["VOLUME"])\
                + "]: ")
        if len(value) == 0:
            break
        if value.isdigit(): 
            value = int(value)
        else:
            continue
        if 0 <= value <= 32768: 
            sound_parms["VOLUME"] = value
            break

except KeyboardInterrupt:
    print()

put_sound_parms()

print("\n", sound_parms)
