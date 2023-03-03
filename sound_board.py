#!/usr/bin/python3
import asyncio
import json
import os
from random import randint

#----------------------------------------------------------------------------------------
class Sound_board:
    sound_dir       = "/home/pi/python/spider/clips/"
    sound_parmfile  = sound_dir + "soundparms.json"
    voice_volume    = 40000      # range: 0 - max  (1000000?)
    max_volume      = 40000    # range: 0 - max
    max_volume_limit = 60000 # can scale up the volume but limit it to this.

    def __init__(self):
        try:
            with open(self.sound_parmfile, "r") as f:
                self.sound_clips = json.load(f)
        except FileNotFoundError:
            print(self.sound_parmfile + ": not found. Reloading.")
            self._load_clips()
#       print(self.sound_clips)
        self.last_clip = None if len(self.sound_clips) == 0 else randint(0, len(self.sound_clips)-1)
#       self.clips_init = True     # lets us spin up through the clips if we use an async iterator

#---------------------------------------------------------------------------------
    def print_clips(self, sound_clips):
        for i, f in enumerate(sound_clips):
            print(f"{i}\t{f}")
        print()
        
    def _load_clips(self):
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
    async def _play_sound2(self, sound_file, volume):
        t_sound = await asyncio.create_subprocess_exec("mpg123", "-q",
                "-f " + str(volume),
                sound_file, stdout=asyncio.subprocess.PIPE)
        await t_sound.wait()   # wait for the mpg123 process to finish

    async def play_sound(self, my_globals, indx=None):
        if self.last_clip is None: # no sound files
            return

        limit = 2     # Play no more than 2x.

        sound_entry = self.sound_clips[self._get_sound_index()] if indx is None else self.sound_clips[indx]

        sound_file = sound_entry[0]
        scale      = sound_entry[1]
        volume = int(my_globals.spider_parms["VOLUME"] * scale)       # scale up volume as needed.
        volume = min(volume, self.max_volume_limit)

#       print(f"{sound_file}, {volume}")
        if not os.path.isfile(sound_file):
            return                              # file does not exist.

        for i in range(limit):
            if my_globals.spider_parms["END_REQUEST"]:
                break   # OK, we're gone!
            await self._play_sound2(sound_file, volume)

            if i == limit - 1:
                return   # don't wait after the last iteration completed
            await asyncio.sleep(1)

if __name__ == "__main__":
    s = Sound_board()
