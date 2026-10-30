#!/usr/bin/env python3
"""Tiny Flask app: phone web page -> settings JSON file in the home directory.

Run:   uv run key_parms.py
Phone: http://raspberrypiz1.local:5000   (or http://<pi-ip>:5000)
"""

import json
import os
import tempfile
import threading
from pathlib import Path

from flask import Flask, jsonify, request, abort

import sys
import signal
import subprocess
from time import sleep

# required by flask 
#SETTINGS_FILE = Path(os.environ.get("SETTINGS_FILE", Path.home() / "spiderparms.json"))
SETTINGS_FILE = Path(os.environ.get("SETTINGS_FILE", "./spiderparms.json"))
API_TOKEN = os.environ.get("API_TOKEN")  # optional: set to require ?token=... / X-Token header

SP_DIR = "/home/ron/python/spider/"
#SETTINGS_FILE = SP_DIR + "spiderparms.json"

speech_loc      = SP_DIR + "speech/"
voices_file     = speech_loc + "speech_legend.json"

'''
Values from orig key_parms.py

max_eye_intensity = 80    # max is 100, but may draw too much power.
min_eye_intensity = 40

'''
# Global constants
Sound_on = None
voice_volume_ndx = None
voice_values     = 20    # must match no. of entries in voice_ints

# key -> (min, max, step) for integers
INT_FIELDS = {
    "VOLUME":  (0, 19, 1),     # index into voice_ints
    "MAX_INT": (0, 100, 5),
}
BOOL_FIELDS = ["SOUND_ON", "RUNNING"]

DEFAULTS = {
    "VOLUME": 10, "MAX_INT": 70,
    "SOUND_ON": False, "RUNNING": False,
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
def speak(voice_key):
    if voice_key not in voices["files"]:
        print("speak: voice_key not found:" , voice_key)
        return

    volume = voice_ints[voice_volume_ndx]
    sound_file = speech_loc + voices["files"][voice_key]["filename"]
    mpg123 = ["mpg123", "-q", "-f", str(volume), sound_file]

    if Sound_on:
        subprocess.run(mpg123)

#---------------------------------------------------------------------------------
#end RG from orig key_parms.py

app = Flask(__name__)
lock = threading.Lock()

def voice_intensities():
    voice_ints = [0, 512]
    for i in range(10, 19):
        value = 1 << i
        half_value = value + (value >> 1)
        voice_ints.append(value)
        voice_ints.append(half_value)
#   print(voice_ints)
    assert len(voice_ints) == voice_values
    return voice_ints


def load():
    global Sound_on, voice_volume_ndx
    try:
#       data = json.loads(SETTINGS_FILE.read_text())
#       data = json.load(SETTINGS_FILE)
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    Sound_on = data["SOUND_ON"]
    voice_volume_ndx = data["VOLUME"]
#   print("SOUND_ON", Sound_on, "\n", "Volume", voice_volume_ndx)
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
    global voice_volume_ndx, Sound_on
    check_auth()
    incoming = request.get_json(silent=True)
    if not isinstance(incoming, dict):
        abort(400, "JSON object expected")
    with lock:
        data = load()
        for key, value in incoming.items():
#           print(key, type(key), value)    # <<<<<<<<<<<<<<<<<<<<<<<<<
            if key in INT_FIELDS:
                lo, hi, _ = INT_FIELDS[key]
                if isinstance(value, bool) or not isinstance(value, int):
                    abort(400, f"{key} must be an integer")
                data[key] = max(lo, min(hi, value))
                if key == "VOLUME":
                    voice_volume_ndx = data[key]
                    speak("01-Hello-Spider")
            elif key in BOOL_FIELDS:
                if not isinstance(value, bool):
                    abort(400, f"{key} must be true or false")
                data[key] = value
                if key == "SOUND_ON":
#                   print("SOUND_ON", value)
                    if Sound_on := data[key]:
                        speak("01-Hello-Spider")
                if key == "RUNNING":
                    if value:  # (is True) => restarting spider.py
                        # force remove of ospid.txt
                        file_path = Path("ospid.txt")
                        # Safely delete the file (ignores error if file is already missing)
                        file_path.unlink(missing_ok=True)

                        # Start spider; this does not wait for it to finish
                        # NOTE: assumes we are in/home/ron/python/spider.
                        proc = subprocess.Popen(["uv", "run", "spider.py"])
                        sleep(1)    # prob. not needed
                    else:      # asking spider py to stop
                        save(data) # save the RUNNING value for spider to shutdown.
                        sleep(2)   # asks spider to stop
                        data["RUNNING"] = False
                        # .... and resave at the end
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
      <button class="tog ${state[k]?"on":"off"}">${state[k]?"on":"off"}</button>`;
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

# Get spider parms. Also loads globals: Sound_on, voice_volume_ndx
load()

# Load globals
voice_ints = voice_intensities()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
