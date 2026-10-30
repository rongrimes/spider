#!/bin/bash

source ~ron/.local/bin/env   # loads venv (env ironment for uv)

echo ---------------- >> ~ron/spider.log
date >> ~ron/spider.log

cd ~ron/python/spider
uv run key_parms.py >> ~ron/spider.log 2>&1 &
sleep 1

rm -f ~ron/python/spider/ospid.txt

uv run spider.py >> ~ron/spider.log 2>&1 &
