#!/usr/bin/env python3
"""Tiny Flask app: phone web page -> settings JSON file in the home directory.

Run:   python3 app.py
Phone: http://raspberrypiz1.local:5000   (or http://<pi-ip>:5000)
"""

#RG
# Remember:
# 1. sudo apt install mpg123


import json
import os
import tempfile
import threading
from pathlib import Path

from flask import Flask, jsonify, request, abort

#RG
import sys
import signal
import subprocess
from time import sleep

#SETTINGS_FILE = Path(os.environ.get("SETTINGS_FILE", Path.home() / "spiderparms.json"))
SETTINGS_FILE = Path(os.environ.get("SETTINGS_FILE", "./spiderparms.json"))
API_TOKEN = os.environ.get("API_TOKEN")  # optional: set to require ?token=... / X-Token header

#RG
#speech_loc      = "/home/pi/python/spider/speech/"
speech_loc      = Path(os.environ.get("speech_loc", "./speech/")
voices_file     = speech_loc + "speech_legend.json"

# key -> (min, max, step) for integers
INT_FIELDS = {
    "VOLUME":  (0, 200000, 5000),
    "MAX_INT": (0, 100, 1),
}
BOOL_FIELDS = ["EYES_ON", "SOUND_ON", "END_REQUEST"]

DEFAULTS = {
    "VOLUME": 100000, "EYES_ON": True, "MAX_INT": 70,
    "SOUND_ON": False, "END_REQUEST": False,
}

#RG from orig key_parms.py
#---------------------------------------------------------------------------------
# load voices structure
def get_voices_file():
    global voices
    try:
        with open(voices_file, "r") as f:
            voices = json.load(f)
    except FileNotFoundError:
        print(voices_file + ": not found. key_parms.py is now terminating.")
        sys.exit()

#---------------------------------------------------------------------------------
def speak(voice_key, volume=voice_volume):
    if voice_key not in voices["files"]:
        print("speak: voice_key not found:" , voice_key)
        return

    sound_file = speech_loc + voices["files"][voice_key]["filename"]
    mpg123 = "exec sudo -u pi mpg123 -q -f " + str(volume) + " " + sound_file

    popen = subprocess.Popen(mpg123, stdout=subprocess.PIPE, shell=True,
        preexec_fn=os.setsid)
    popen.wait()

#---------------------------------------------------------------------------------
#end RG from orig key_parms.py

app = Flask(__name__)
lock = threading.Lock()


def load():
    try:
        data = json.loads(SETTINGS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    return {**DEFAULTS, **data}


def save(data):
    # atomic write so a power cut can't leave a half-written file
    fd, tmp = tempfile.mkstemp(dir=SETTINGS_FILE.parent, prefix=".settings-")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, SETTINGS_FILE)


def check_auth():
    if API_TOKEN and (request.headers.get("X-Token") or request.args.get("token")) != API_TOKEN:
        abort(401)


@app.get("/api/settings")
def get_settings():
    check_auth()
    with lock:
        return jsonify(load())


@app.post("/api/settings")
def update_settings():
    check_auth()
    incoming = request.get_json(silent=True)
    if not isinstance(incoming, dict):
        abort(400, "JSON object expected")
    with lock:
        data = load()
        for key, value in incoming.items():
            if key in INT_FIELDS:
                lo, hi, _ = INT_FIELDS[key]
                if isinstance(value, bool) or not isinstance(value, int):
                    abort(400, f"{key} must be an integer")
                data[key] = max(lo, min(hi, value))
            elif key in BOOL_FIELDS:
                if not isinstance(value, bool):
                    abort(400, f"{key} must be true or false")
                data[key] = value
            else:
                abort(400, f"Unknown key: {key}")
        save(data)
        return jsonify(data)


PAGE = """<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pi Settings</title>
<style>
  body{font-family:system-ui,sans-serif;margin:0;padding:16px;background:#111;color:#eee}
  h1{font-size:1.2rem;margin:0 0 12px}
  .row{display:flex;align-items:center;justify-content:space-between;background:#222;
       border-radius:12px;padding:12px 14px;margin-bottom:12px}
  .name{font-weight:600}
  .val{min-width:90px;text-align:center;font-size:1.3rem;font-variant-numeric:tabular-nums}
  button{font-size:1.4rem;border:0;border-radius:10px;padding:12px 18px;background:#3a3a3a;color:#eee}
  button:active{background:#555}
  .tog{min-width:110px;font-size:1.1rem}
  .tog.on{background:#1f7a3a}.tog.off{background:#8a2a2a}
  #msg{height:1.2em;color:#f88;font-size:.9rem}
</style></head><body>
<h1>raspberrypiZ1</h1>
<div id="ui"></div><div id="msg"></div>
<script>
const INTS = __INTS__;
const BOOLS = __BOOLS__;
const token = new URLSearchParams(location.search).get("token");
const headers = {"Content-Type":"application/json", ...(token?{"X-Token":token}:{})};
let state = {};

async function post(change){
  try{
    const r = await fetch("/api/settings",{method:"POST",headers,body:JSON.stringify(change)});
    if(!r.ok) throw new Error(r.status);
    state = await r.json(); msg.textContent=""; render();
  }catch(e){ msg.textContent="Save failed: "+e.message; }
}
function render(){
  ui.innerHTML="";
  for(const [k,[lo,hi,step]] of Object.entries(INTS)){
    const d=document.createElement("div"); d.className="row";
    d.innerHTML=`<span class="name">${k}</span><span><button>−</button>
      <span class="val">${state[k]}</span><button>+</button></span>`;
    const [dn,up]=d.querySelectorAll("button");
    dn.onclick=()=>post({[k]:state[k]-step});
    up.onclick=()=>post({[k]:state[k]+step});
    ui.appendChild(d);
  }
  for(const k of BOOLS){
    const d=document.createElement("div"); d.className="row";
    d.innerHTML=`<span class="name">${k}</span>
      <button class="tog ${state[k]?"on":"off"}">${state[k]?"true":"false"}</button>`;
    d.querySelector("button").onclick=()=>post({[k]:!state[k]});
    ui.appendChild(d);
  }
}
fetch("/api/settings",{headers}).then(r=>r.json()).then(s=>{state=s;render();})
  .catch(()=>msg.textContent="Could not load settings");
</script></body></html>"""


@app.get("/")
def index():
    check_auth()
    return (PAGE.replace("__INTS__", json.dumps(INT_FIELDS))
                .replace("__BOOLS__", json.dumps(BOOL_FIELDS)))


# Get voice file
get_voices_file()
speak("01-Hello-Spider")

# Get spider parms
get_spider_parms()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
