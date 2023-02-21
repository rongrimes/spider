#!/usr/bin/python3
import json

class My_globals:
    spider_parmfile = "spiderparms.json"
    spider_def_parms = {"SOUND_ON": False,
            "VOLUME":10000,     # 0 <= VOLUME  <= 32768
            "MAX_INT":800,       # 0 <= MAX_INT <= 1000
            "EYES_ON:": True,       # to inhibit the eyes while we're using the IR board
            "END_REQUEST": False }      # to inhibit the eyes while we're using the IR board

    def __init__(self):
        self.animation_active = False
        self.get_spider_parms() 
        self.spider_parms["END_REQUEST"] = False

    def get_spider_parms(self):
        try:
            with open(self.spider_parmfile, "r") as f:
                self.spider_parms = json.load(f)
        except FileNotFoundError:
            # instead, use the defaults defined above
            self.spider_parms = self.spider_def_parms
            print(self.spider_parmfile, ": file not found.")

