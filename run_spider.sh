#!/bin/bash
LOGFILE="spider_log.txt"

cd ~pi/python/spider
echo >> $LOGFILE
echo "-------------------------" >> $LOGFILE
date >> $LOGFILE
echo >> $LOGFILE
sudo ./spider.py & >> $LOGFILE
