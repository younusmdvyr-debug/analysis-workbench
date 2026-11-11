#!/usr/bin/env bash
# Offline launcher (Linux/macOS): installs deps once (needs internet only for that), then runs with no network.
cd "$(dirname "$0")"
[ -d .venv ] || { python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements.txt; }
. .venv/bin/activate
export ECONLAB_OFFLINE=1
streamlit run app.py --server.headless false --browser.gatherUsageStats false
