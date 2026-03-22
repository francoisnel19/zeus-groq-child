#!/bin/bash
# The Zeus Project 2026 — Francois Nel
# Zeus First Boot — GROQ_PLATFORM
# Run ONCE on any new system

set +e
echo ''
echo '⬡  ZEUS MIGRATION — GROQ_PLATFORM'
echo '   The Zeus Project 2026 — Francois Nel'
echo ''

# Install pip base deps
pip install flask requests groq anthropic \
  apscheduler python-dotenv \
  --break-system-packages -q 2>/dev/null || \
pip install flask requests groq anthropic \
  apscheduler python-dotenv --user -q

# Copy .env if template present
[ -f .env.template ] && [ ! -f .env ] && cp .env.template .env

export ZEUS_PARENT_URL=http://localhost:5000
export ZEUS_TARGET_PLATFORM=groq_platform
export ZEUS_STEM_CELL_BOOT=1

# Differentiate
echo 'Running stem cell differentiation...'
python3 zeus_stem_boot.py

# Platform-specific setup
[ -f setup_groq_platform.sh ] && bash setup_groq_platform.sh

echo ''
echo '✔  Zeus GROQ_PLATFORM deployed'
echo '   Check logs/ for status'
echo '   The Zeus Project 2026 — Francois Nel'
