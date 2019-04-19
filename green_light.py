#!/usr/bin/python3
import time

class Green_Light(object):
    green_light_led_dir = "/sys/class/leds/led0/"
    on = "255"
    off = "0"

    def __init__(self, Reverse):
        if Reverse:
            self.on, self.off = self.off, self.on
        return self.init("none")   # Turn off current driver for the led.
    
    def init(self, led_source):
        try:
            led_file = "trigger"
            with open(self.green_light_led_dir + led_file, "w") as f:
                f.write(led_source)
        except PermissionError:
            print("PermissionError with write led. Run with sudo.")
            quit()
    
    def set(self, cmd):
        if cmd == "on": 
            self.set_green_led(self.on)
        elif cmd == "off": 
            self.set_green_led(self.off)
        else:
            assert(cmd in ["on", "off"])

    def set_green_led(self, led_value):
        led_file = "brightness"
        with open(self.green_light_led_dir + led_file, "w") as f:
            f.write(led_value)
        
if __name__ == "__main__":
    print("Taking control of the green light.")
    green_light = Green_Light(Reverse=True)
    for i in range(0,3):
        print("greenlight on")
        green_light.set("on")
        time.sleep(3)
        print("greenlight off")
        green_light.set("off")
        time.sleep(3)
    print("Giving up control of the green light.")
    green_light.init("mmc0")   # Return to showing "disk access" events.
