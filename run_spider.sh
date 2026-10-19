#!/bin/bash

echo ---------------- >> ~ron/spider.log
date >> ~ron/spider.log

cd ~ron/python/spider
#sudo --user=ron ./key_parms.py >> ~ron/spider.log 2>&1 &
#sleep 1

sudo --user=ron ./spider.py >> ~ron/spider.log &
