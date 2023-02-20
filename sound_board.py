#!/usr/bin/python3
import asyncio
import os
from random import randint

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

        self.last_clip = randint(0, len(self.sound_list) - 1)   # index of a random clip

        for f in self.sound_list:
            print(f"\t{f}")
        print(f"start: {self.last_clip}")

    def _get_sound_index(self):
        self.last_clip += 1
        if self.last_clip >= len(self.sound_list):
            self.last_clip = 0
        return self.last_clip

    async def play_sound(self, my_globals):
        limit = 2     # Play no more than 2x.

        sound_file = self.sound_list[self._get_sound_index()]
#       print(f" {sound_file}")

        for i in range(limit):
            if my_globals.end_request:
                break   # OK, we're gone!

            t_sound = await asyncio.create_subprocess_exec("mpg123", "-q",
                    "-f " + str(my_globals.spider_parms["VOLUME"]),
                    sound_file, stdout=asyncio.subprocess.PIPE)
            await t_sound.wait()   # wait for the mpg123 process to finish
            if i == limit - 1:
                return   # don't wait after the last iteration completed
            await asyncio.sleep(1)

if __name__ == "__main__":
    s = Sound_board()
