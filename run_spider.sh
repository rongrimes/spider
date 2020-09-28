#!/bin/bash

echo ---------------- >> ~pi/spider.log
date >> ~pi/spider.log

cd ~pi/python/spider
sudo ./spider.py >> ~pi/spider.log &
