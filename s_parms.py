#!/usr/bin/python3
##!env python3

import json
import os
import signal
import subprocess

spider_parmfile = "spiderparms.json"

#default values
spider_parms = {"ON": False, "VOLUME":10000, "MAX_INT":25} # 0 <= VOLUME  <= 32768

#---------------------------------------------------------------
def get_spider_parms():
    global spider_parms
    try:
        with open(spider_parmfile, "r") as f:
            spider_parms = json.load(f)
    except FileNotFoundError:
        print(spider_parmfile + ": not found. Using defaults.")
        # use defaults defind above
        pass

#---------------------------------------------------------------
def put_spider_parms():
    global spider_parms
    with open(spider_parmfile, "w") as f:
        json.dump(spider_parms, f)

#---------------------------------------------------------------
# Get spider parms
get_spider_parms()
changed = False

try:
    while True:
        value = input("Sound T/F [" + str(spider_parms["ON"]) + "]: ")
        if len(value) == 0:
            break
        if value.lower() == "true"[:len(value)]: 
            spider_parms["ON"] = True
            changed = True
            break
        if value.lower() == "false"[:len(value)]: 
            spider_parms["ON"] = False
            changed = True
            break

    while True:
        value = input("Volume (0-32768) [" + str(spider_parms["VOLUME"])\
                + "]: ")
        if len(value) == 0:
            break
        if value.isdigit(): 
            value = int(value)
        else:
            continue
        if 0 <= value <= 32768: 
            spider_parms["VOLUME"] = value
            changed = True
            break

    while True:
        value = input("Eye Power (0-100) [" + str(spider_parms["MAX_INT"])\
                + "]: ")
        if len(value) == 0:
            break
        if value.isdigit(): 
            value = int(value)
        else:
            continue
        if 0 <= value <= 100: 
            spider_parms["MAX_INT"] = value
            changed = True
            break

except KeyboardInterrupt:
    print()

if changed:
    put_spider_parms()

print("\n", spider_parms)
