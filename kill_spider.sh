#!/bin/bash

e=`ps aux | grep spider`

if [ "$(grep -c python3 <<< $e)" -gt 0 ]; then
    echo Kill spider.
#   echo $e
#   echo
#   cat /home/pi/python/spider/ospid.txt
    sudo kill -s sigint `cat /home/pi/python/spider/ospid.txt`
    sleep 2
else
    echo spider not found.
fi

if [ -f ~/python/spider/ospid.txt ]; then
    rm ~/python/spider/ospid.txt
fi
