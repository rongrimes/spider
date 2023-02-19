# Heavy Metal Hollywood Spider
<img src="./media/Spider_with_eyes.png" height="50%" width="50%">

**Heavy Metal Hollywood Spider** is an _*animatronics*_ project and is the fusion of two interests:
* Art Metal class
* Raspberry Pi and related hardware software.

As with the ![Chocolate Box News Reader](https://github.com/rongrimes/paxnews) ("paxnews"), the project grew organically. That is I had a rough idea how it would all look at the end but progress was consistent over a number of months. You could say that, he is an organic spider (best kind!).

Ultimately, HMHS became a successful Halloween prop.

## Components:
* [Raspberry Pi Zero W](https://www.buyapi.ca/product/raspberry-pi-zero-w/)
* Eyes: 2 clusters of 4 RGB LEDs
* [Adafruit I2S 3W Stereo Speaker Bonnet for Raspberry Pi](https://www.buyapi.ca/product/adafruit-i2s-3w-stereo-speaker-bonnet-for-raspberry-pi-mini-kit/)
  * includes 2 speakers 
* [PIR sensor](https://www.buyapi.ca/product/hc-sr501-pyroelectric-infrared-pir-motion-sensor-detector-module/)
* [LED string (white) or similar](https://www.staples.com/5ft-15-Soft-White-String-Lights-with-Timer-74445/product_2724775)
* [Simple RF M4 Receiver - 315MHz Momentary Type](https://www.buyapi.ca/product/simple-rf-m4-receiver-315mhz-momentary-type/)
* [Keyfob 4-Button RF Remote Control - 315MHz](https://www.buyapi.ca/product/keyfob-4-button-rf-remote-control-315mhz/)

## Spider Construction
The spider grew "organically" over two semesters of the **Art Metal** class held at <a href="https://www.danforthcti.com/">Danforth Collegiate</a> in the body shop workshop, under the auspices of the <a href="https://www.tdsb.on.ca/Adult-Learners/Learn4Life">TDSB Adult Learner Program</a> (Toronto District School Board). [Thanks to Phil and Toby for their guidance.]

## General Operations
The spider sensor resides in the nose and detects motion from pets/humanoids/zombie  up to 5 metres away (<a href="https://www.adafruit.com/product/189" target="_blank">possibly works on zombies, not guaranteed</a>).

On pet/humanoid/zombie detection:
* Spider is dozing: The cyan eyes and body lights twitch every few seconds. Until someone/thing comes by.
* Spider goes on alert: The cyan eyes and body lights start flashing rapidly.
* Spider gets angry: The red eyes then transition up to full brightness.
* Spider emits warning noises: A short sound clip plays twice (or other count) or until the pet/humanoid/zombie goes out of range.
* All clear, Spider goes back to sleep: The red eyes then transition down.
* Spider goes back to dozing.

### Spider video
![Spider video](media/Spider2.mp4).

(Click and view the ![raw file](https://github.com/rongrimes/spider/blob/master/media/Spider2.mp4?raw=true) in a separate window.).

### Spider Control Subsystem
A 4-Button 315Mhz Keyfob RF Remote Control controls parameters of the spider: Sound On/Off, Sound Volume, Eye Intensity.

The keyfob controls a Simple RF M4 Receiver> with results fed through to four GPIO pins via separate simple voltage splitters to translate 5V to 3.3V (2.8V actually).

The program *key_parms.py* watches the remote control and updates a shared json file used by _spider.py_.

### Schematic
See ![schematic](fritzing/spider_schematic.pdf).  
(Remote control content is not shown.)

## Operations
Start spider with _crontab_:
```
@reboot rm -f /home/pi/python/spider/ospid.txt # JOB_ID_1; Remove pid file to prevent mulitiple incursions of spider.
@reboot sleep 1 && ~pi/run_spider.sh           # JOB_ID_2; start spider.
@reboot sleep 2 && stdbuf -oL ~pi/python/spider/key_parms.py >> /tmp/spider.txt  # JOB_ID_3; start key controller.
```

## Fob Commands
The key Fob/RF receiver controls parameters for operation: A Voice prompt guides the operator for the steps.
 ready for power off.  
1: Press D to get attention.  
2. Press D for the menu.  
   A > Sound On/Off  
   B > Sound Volume  
   C > Maximum eye intensity  
   D > Play the menu (and a seong press will Return to the outer shell ("1")).  
3. Three consecutive presses of D cause spider to shutdown and be ready for power off.  


## Voice Prompt
For the prommt voice clips, I used the text-to-voice service from [IBM Watson](https://text-to-speech-demo.ng.bluemix.net/). Most of the voices are slowed a little from their original speeds to add gravitas. A json file holds the key of voice clips to files, but also holds the markeed up text sent to Watson  in case the text needs editing.

## FAQ
Q: Why _Hollywood_?  
A: Well, we... the spider and me... live on Hollywood Cres.

***
Ron Grimes  
Toronto  
Started:     January 2019  
Last Update: November 2020
