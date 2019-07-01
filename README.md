# spider
The **Spider** project is a fusion of two current interests:
* Art Metal class
* Raspberry PI and related hardware software.

As with the ![Chocolate Box News Reader](https://github.com/rongrimes/paxnews) ("paxnews"), the project grew organically. That is I only had a rough idea how it would all look at the end but progresson was consistent over a number of months. You could say that, he is an organic spider (best kind!).

## Components:
* Raspberry Pi Zero W
* Eyes: 2 clusters of 4 RGB LEDs
* Adafruit I2S 3W Stereo Speaker Bonnet for Raspberry Pi
  * includes 2 speakers 
* PIR sensor
* LED string (white)

## Spider Construction
The spider grew "organically" over two semesters of the **Art Metal** class held at ![Danforth Collegiate](https://www.danforthcti.com/) inthebody shop workshop, under the auspices of the ![TDSB Adult Learner Program](https://www.tdsb.on.ca/Adult-Learners/Learn4Life) (Toronto District School Board). [Thanks to Phil and Toby for their guidance.]

## The Spider
\** (Image to come)

## General Operations
The spider sensor resides in the nose and detects people, animals and ghoulies passing nearby. On detection:
* The eyes transition up to full brightness
* A short sound clip plays

While there is a stranger detected, the eyes stay on, and they and the body flashes every couple of seconds (in "anger").
When the nose sensor no longer detects a nearby presence, the eyes  transition to "off", and the flashing lights flash only every 10 seconds.

## Operations
Start spider with:  
crontab:
```
@reboot rm /home/pi/python/spider/ospid.txt # JOB_ID_1; Remove pid file to prevent mulitiple incursions of spider.
@reboot sleep 2 && ~pi/run_spider.sh # JOB_ID_2; start spider.
```

***
Ron Grimes  
Toronto  
January - June 2019  
