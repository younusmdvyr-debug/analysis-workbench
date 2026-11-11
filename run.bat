@echo off
REM Offline launcher (Windows): installs deps once (internet only for that), then runs with no network.
cd /d "%~dp0"
if not exist .venv ( python -m venv .venv && call .venv\Scripts\activate && pip install -q -r requirements.txt )
call .venv\Scripts\activate
set ECONLAB_OFFLINE=1
streamlit run app.py --browser.gatherUsageStats false
