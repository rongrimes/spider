#!/bin/bash

e=`ps aux | grep spider`

if [ "$(grep -c python3 <<< $e)" -gt 0 ]; then
    echo Kill spider.

    sudo kill -s sigint `cat /home/pi/python/spider/ospid.txt`
    sleep 4
else
    echo spider not found.
fi

rm -f ~/python/spider/ospid.txt                  # if it's not there we don't care.
