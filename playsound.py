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

from sound_board import Sound_board

class Globals:
    spider_parms = {}

# Arm signal to end program.
def sig_handler(signum, frame):
    ''' A sigint interrupt will get caught here, and will in effect be the same as
        getting a ^C at the keyboard.'''
    raise KeyboardInterrupt

async def main(indx):
    await sound.play_sound(my_globals, indx)

#---------------------------------------------------------------
# Arm sigint to cause proceed to graceful end.
signal.signal(signal.SIGINT, sig_handler)

# Get the sound files
sound = Sound_board()
my_globals = Globals()
my_globals.spider_parms = {"END_REQUEST": False, "VOLUME":10000}

try:
    while True:
        try:
            istr = input("Get sound # (-1 reprints the lists): ")
            if istr == "":
                indx = None
            else:
                indx = int(istr)
                if indx == -1:
                    sound.print_clips(sound.sound_clips)
                    continue
                # test indx value & trap if bad.
                _ = sound.sound_clips[indx]

            istr = input("Volume Level (0-40000, def=5000): ")
            my_globals.spider_parms["VOLUME"] = 5000 if istr == "" else int(istr)

        except (ValueError, IndexError):
            print()
            continue

        asyncio.run(main(indx))
        print()

except KeyboardInterrupt:
    print()
