#!/usr/bin/env python3
"""
radionet_broadcast.py
Tibaŋsim / RadioNet FM broadcast loop for Raspberry Pi using Pi-FM-RDS.

Run this script with root privileges (e.g. via sudo or as a systemd service).
"""

import os
import sys
import time
import subprocess
from pathlib import Path

AUDIO_DIR = Path("/var/radionet/audio")
PI_FM_RDS = Path("/home/pi/PiFmRds/pi_fm_rds")
FREQ = "107.9"
RDS_PI = "F1A5"
RDS_PS = "TIBANSIM"
RDS_RT = "OUR KNOWLEDGE"
SOX_BIN = Path("/usr/bin/sox")
RDS_SAMPLE_RATE = "228k"
SUPPORTED_EXT = {".wav", ".ogg", ".oga", ".mp3"}

def log(msg: str) -> None:
    sys.stderr.write(f"[radionet] {msg}\n")
    sys.stderr.flush()

def check_prereqs() -> None:
    if not PI_FM_RDS.exists() or not os.access(PI_FM_RDS, os.X_OK):
        log(f"Pi-FM-RDS binary not found or not executable at: {PI_FM_RDS}")
        sys.exit(1)
    if not AUDIO_DIR.exists() or not AUDIO_DIR.is_dir():
        log(f"Audio directory does not exist: {AUDIO_DIR}")
        sys.exit(1)
    if not SOX_BIN.exists() or not os.access(SOX_BIN, os.X_OK):
        log(f"SoX not found at {SOX_BIN} (install with: sudo apt-get install sox)")
        sys.exit(1)

def play_file(path: Path) -> None:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXT:
        log(f"Skipping unsupported file type: {path}")
        return
    log(f"Now playing: {path}")
    sox_cmd = [str(SOX_BIN), str(path), "-r", RDS_SAMPLE_RATE, "-c", "2", "-b", "16", "-t", "wav", "-"]
    pifm_cmd = [str(PI_FM_RDS), "-freq", FREQ, "-pi", RDS_PI, "-ps", RDS_PS, "-rt", RDS_RT, "-audio", "-"]
    sox_proc = subprocess.Popen(sox_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        pifm_proc = subprocess.Popen(pifm_cmd, stdin=sox_proc.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sox_proc.stdout.close()
        pifm_proc.wait()
        sox_proc.wait()
    finally:
        if sox_proc.poll() is None:
            sox_proc.terminate()
        try:
            if pifm_proc.poll() is None:
                pifm_proc.terminate()
        except NameError:
            pass

def main_loop() -> None:
    log(f"Starting RadioNet / Tibaŋsim FM loop on {FREQ} MHz from {AUDIO_DIR}")
    while True:
        files = sorted(f for f in AUDIO_DIR.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXT)
        if not files:
            log(f"No audio files found in {AUDIO_DIR}; sleeping 10s")
            time.sleep(10)
            continue
        for f in files:
            try:
                play_file(f)
            except KeyboardInterrupt:
                log("Interrupted by user, exiting.")
                sys.exit(0)
            except Exception as e:
                log(f"Error playing {f}: {e}")
                time.sleep(1)
        time.sleep(0.5)

if __name__ == "__main__":
    check_prereqs()
    main_loop()
