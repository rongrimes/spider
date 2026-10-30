#!/usr/bin/python3
import asyncio
import json
import os
from random import randint

#----------------------------------------------------------------------------------------
class Sound_board:
    SP_DIR          = "/home/ron/python/spider/"
    sound_dir       = SP_DIR + "clips/"
    sound_parmfile  = sound_dir + "soundparms.json"
#   voice_volume    = 40000    # range: 0 - max  (1000000?)
#   max_volume      = 40000    # range: 0 - max
    max_volume_limit = 500000  # can scale up the volume but limit it to this.
    voice_values    = 20       # matched len(voice_ints)

#   Number of times to play a clip    
    play_limit = 2     # Play no more than 2x.


    def __init__(self):
        try:
            with open(self.sound_parmfile, "r") as f:
                self.sound_clips = json.load(f)
#           print(self.sound_clips)
        except FileNotFoundError:
            print(self.sound_parmfile + ": not found. Reloading.")
            self._load_clips()

        self.last_clip = None if len(self.sound_clips) == 0 else randint(0, len(self.sound_clips)-1)

#       Build voice intensity chart: maps volume index to mpg123 scalefactor
        self.voice_intensities()


#---------------------------------------------------------------------------------
    def voice_intensities(self):
        self.voice_ints = [0, 512]
        for i in range(10, 19):
            value = 1 << i
            half_value = value + (value >> 1)
            self.voice_ints.append(value)
            self.voice_ints.append(half_value)
#       makes sure voice_ints matches voice_values when we come to use it.
        assert len(self.voice_ints) == self.voice_values

    def print_clips(self, sound_clips):
        for i, f in enumerate(sound_clips):
            print(f"{i}\t{f}")
        print()
        
    def _load_clips(self):
        '''WARNING: Make SURE THESE FILENAMES ARE OF THE FORM:: clips/file.mp3
        '''
        self.sound_clips = []
        if not os.path.isdir(self.sound_dir):
            print(self.sound_dir + ": Sound dir does not exist.")
            return            # dir doesn't exist,
                              #    return empty list = no sound files
        for file in os.listdir(self.sound_dir):
            _, file_extension = os.path.splitext(file)     # discard filename part
            if file_extension[1:] in {"mp3"}:    # set of allowed sound files
                entry = [self.sound_dir + file, 1.0]   # it would be nicer as a tuple, but we can't store
                                                  #     it in a json file.
                self.sound_clips.append(entry)

#---------------------------------------------------------------------------------
    def _get_sound_index(self):
        self.last_clip += 1
        if self.last_clip >= len(self.sound_clips):
            self.last_clip = 0
        return self.last_clip

#---------------------------------------------------------------------------------
    async def _play_sound2(self, sound_file, volume, playsound_onoff):
        mpg123 = ["mpg123", "-q", "-f", str(volume), sound_file]
        print(mpg123)
        if playsound_onoff:
            t_sound = await asyncio.create_subprocess_exec("mpg123", "-q", "-f", str(volume),
                                                           sound_file)
            await t_sound.wait()   # wait for the mpg123 process to finish

    async def play_sound(self, my_globals, playsound_onoff, indx=None):
        if self.last_clip is None: # no sound files
            return

        sound_entry = self.sound_clips[self._get_sound_index()] if indx is None else self.sound_clips[indx]

        sound_file = self.SP_DIR + sound_entry[0]
        scale      = sound_entry[1]

        volume_ndx = my_globals.spider_parms["VOLUME"] 
        volume = int(self.voice_ints[volume_ndx] * scale)       # scale up volume as needed.
        volume = min(volume, self.max_volume_limit)

#       print(f"{sound_file}, {volume}")
        if not os.path.isfile(sound_file):
            return                              # file does not exist.

        for i in range(self.play_limit):
            if not my_globals.spider_parms["RUNNING"]:
                break   # OK, we're gone!
            await self._play_sound2(sound_file, volume, playsound_onoff)

            if i == self.play_limit - 1:
                return   # don't wait after the last iteration completed
            await asyncio.sleep(1)

if __name__ == "__main__":
    s = Sound_board()
