#!/bin/bash

e=`ps aux | grep spider`

if [ "$(grep -c python3 <<< $e)" -gt 0 ]; then
    echo Kill spider.
    ospid=`cat /home/pi/python/spider/ospid.txt`
    sudo kill -s sigint $ospid

    tail --pid=$ospid -f /dev/null              # runs until $ospid goes away
else
    echo spider not found.
fi

rm -f ~/python/spider/ospid.txt                  # if it's not there we don't care.
