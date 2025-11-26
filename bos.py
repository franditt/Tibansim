#!/usr/bin/env python3
import os
import time
import subprocess
from pathlib import Path
import psutil

AUDIO_DIR = Path("/var/radionet/audio")
AUTHORIZED_NUMBER = "+233XXXXXXXXX"
INTERVAL = 1800

SEND_SMS = "/usr/bin/gammu-smsd-inject"
READ_SMS = "/usr/bin/gammu-smsd-monitor"

def send_sms(number, text):
    if len(text) > 150:
        text = text[:147] + "..."
    subprocess.run([SEND_SMS, "TEXT", number, "-text", text],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_cpu_temp():
    try:
        out = Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
        return round(int(out) / 1000, 1)
    except:
        return "N/A"

def get_cpu_io():
    usage = psutil.cpu_times_percent(interval=1)
    return usage.iowait

def get_process_count():
    return len(psutil.pids())

def get_uptime():
    return int(time.time() - psutil.boot_time())

def get_audio_list():
    files = [f.name for f in AUDIO_DIR.glob("*") if f.is_file()]
    return ", ".join(files) if files else "NONE"

def get_stats_message():
    cpu_temp = get_cpu_temp()
    cpu_load = psutil.cpu_percent()
    io_wait = get_cpu_io()
    proc_count = get_process_count()
    uptime = get_uptime()
    audio = get_audio_list()

    return (
        f"TibaNsim Status:\n"
        f"Temp: {cpu_temp}C\n"
        f"CPU Load: {cpu_load}%\n"
        f"IO Wait: {io_wait}%\n"
        f"Processes: {proc_count}\n"
        f"Uptime: {uptime}s\n"
        f"Audio: {audio}"
    )

def read_sms():
    try:
        out = subprocess.check_output([READ_SMS, "1"], stderr=subprocess.DEVNULL)
        return out.decode(errors="ignore")
    except:
        return ""

def extract_command(raw):
    text = ""
    sender = ""
    for line in raw.splitlines():
        line = line.strip()
        if "Number:" in line:
            sender = line.split("Number:", 1)[1].strip()
        if "Text:" in line:
            text = line.split("Text:", 1)[1].strip()
    return sender, text.strip()

def execute_command(cmd):
    if not cmd:
        return "No command"
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True,
                              text=True, timeout=60)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if out:
            return out
        if err:
            return err
        return f"Exit code: {proc.returncode}"
    except Exception as e:
        return f"ERR: {e}"

def main():
    last_sent = 0
    while True:
        now = time.time()
        if now - last_sent >= INTERVAL:
            msg = get_stats_message()
            send_sms(AUTHORIZED_NUMBER, msg)
            last_sent = now
        raw = read_sms()
        sender, cmd = extract_command(raw)
        if sender == AUTHORIZED_NUMBER and cmd:
            response = execute_command(cmd)
            send_sms(AUTHORIZED_NUMBER, response)
        time.sleep(5)

if __name__ == "__main__":
    main()
