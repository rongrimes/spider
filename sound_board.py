#!/usr/bin/python3
import os
import subprocess
import time

sound_dir = "clips"                               # don't use ~pi form - fails!
sound_time = 8    # play sound for * seconds

def sound_board(spider_parms, play_sound, end_request):
    global sound_index

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

#   print("sound     thread:", sound.name)

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
