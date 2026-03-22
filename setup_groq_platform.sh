#!/bin/bash
# The Zeus Project 2026 — Francois Nel
# Zeus GROQ_PLATFORM Bootstrap

set +e
mkdir -p logs

echo 'Installing groq_platform packages...'
pip install groq --break-system-packages -q

nohup python3 app.py > logs/zeus.log 2>&1 &
sleep 3
# Start learner
[ -f zeus_recursive_learner.py ] && \
  nohup python3 zeus_recursive_learner.py >> logs/learner.log 2>&1 &
# Start evolution scheduler
[ -f zeus_nightly_scheduler.py ] && \
  nohup python3 zeus_nightly_scheduler.py >> logs/evolution.log 2>&1 &
echo 'Zeus GROQ_PLATFORM active'
