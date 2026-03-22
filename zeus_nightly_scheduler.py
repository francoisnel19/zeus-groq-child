# The Zeus Project 2026 — Francois Nel
# Nightly evolution scheduler — runs at 00:05 every day
import subprocess
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

LOG = os.path.expanduser("~/zeus_v4/logs/nightly_evolution.log")
ZEUS_DIR = os.path.expanduser("~/zeus_v4")

def run_evolution():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Starting nightly Zeus evolution...")
    with open(LOG, "a") as log:
        log.write(f"\n{'='*60}\n")
        log.write(f"NIGHTLY EVOLUTION — {ts}\n")
        log.write(f"{'='*60}\n")
        result = subprocess.run(
            ["python3", "zeus_self_evolution.py",
             "--skip-claude", "--force-groq", "--resume"],
            cwd=ZEUS_DIR,
            stdout=log,
            stderr=log
        )
        log.write(f"\nExit code: {result.returncode}\n")
    print(f"[{ts}] Evolution complete. Exit: {result.returncode}")

scheduler = BlockingScheduler()
scheduler.add_job(run_evolution, 'cron', hour=0, minute=5)
print("Zeus nightly scheduler running — evolution fires at 00:05 daily")
print("Press Ctrl+C to stop")
scheduler.start()
