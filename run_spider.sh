#!/bin/bash

echo ---------------- >> ~pi/spider.log
date >> ~pi/spider.log

cd ~pi/python/spider
sudo --user=pi ./key_parms.py >> ~pi/spider.log 2>&1 &
sleep 1

sudo --user=pi sudo ./spider.py >> ~pi/spider.log &
