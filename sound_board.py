#!/usr/bin/python3
import os
import subprocess
from random import randint

sound_dir = "clips"                               # don't use ~pi form - fails!

def sound_board(spider_parms):
    def make_sound_list(sound_dir):
        sound_list = []
        if not os.path.isdir(sound_dir):
            print(sound_dir + ": Sound dir does not exist.")
            return sound_list # dir doesn't exist,
                              #    return empty list = no sound files
        for file in os.listdir(sound_dir):
            _, file_extension = os.path.splitext(file)     # discard filename part
            if  file_extension[1:] in {"mp3"}:    # set of allowed sound files
                sound_list.append(sound_dir + "/" + file)
        print("Sound list: ", sound_list)
        return sound_list

    def get_sound_file(sound_list):
        return sound_list[randint(0, len(sound_list) - 1)]   # randomises the list

#----------------------------------------------------------------------------------------
#   print("sound     thread:", sound.name)
    sound_list = make_sound_list(sound_dir)
    sound_file = get_sound_file(sound_list)

    mpg123 = "exec sudo -u pi mpg123 -f " + str(spider_parms["VOLUME"]) \
            + " " + sound_file

    pid = subprocess.Popen(mpg123, stdout=subprocess.PIPE, shell=True,
            preexec_fn=os.setsid)
