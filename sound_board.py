#!/usr/bin/python3
import json
import os
import subprocess
from random import randint
from time import sleep

class My_globals:
    spider_parmfile = "spiderparms.json"
    spider_parms = {"ON": False,
            "VOLUME":10000,     # 0 <= VOLUME  <= 32768
            "MAX_INT":25 }      # 0 <= MAX_INT <= 100

    def __init__(self):
        self.animation_active = False
        self.end_request      = False
        self.get_spider_parms() 

    def get_spider_parms(self):
        try:
            with open(self.spider_parmfile, "r") as f:
                self.spider_parms = json.load(f)
        except FileNotFoundError:
            # instead, use the defaults defined above
            self.spider_parms = self.spider_parms
            print(spider_parmfile, ": file not found.")

#----------------------------------------------------------------------------------------
class Sound_board:
    sound_dir = "clips"                               # don't use ~pi form - fails!

    def __init__(self):
        self.sound_list = []
        if not os.path.isdir(self.sound_dir):
            print(self.sound_dir + ": Sound dir does not exist.")
            return self.sound_list # dir doesn't exist,
                              #    return empty list = no sound files
        for file in os.listdir(self.sound_dir):
            _, file_extension = os.path.splitext(file)     # discard filename part
            if  file_extension[1:] in {"mp3"}:    # set of allowed sound files
                self.sound_list.append(self.sound_dir + "/" + file)
        print("Sound list: ", self.sound_list)
        self.last_clip = randint(1, len(self.sound_list)) - 2   # (index of a random clip) - 2

    def _get_sound_index(self):
        self.last_clip += 1
        if self.last_clip >= len(self.sound_list):
            self.last_clip = 0
        return self.last_clip

    def play_sound(self, my_globals):
        limit = 2     # Play no more than 2x.
        play  = 0

        sound_file = self.sound_list[self._get_sound_index()]
        print(" {}".format(sound_file))

        mpg123 = "exec sudo -u pi mpg123 -q -f " + str(my_globals.spider_parms["VOLUME"]) \
                + " " + sound_file

        while my_globals.animation_active:
            if play >= limit or my_globals.end_request:
                break   # OK, we're gone!
            play += 1

            popen = subprocess.Popen(mpg123, stdout=subprocess.PIPE, shell=True,
                preexec_fn=os.setsid)
            popen.wait()
            sleep(1)
