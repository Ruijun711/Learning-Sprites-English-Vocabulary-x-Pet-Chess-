@echo off
cd /d "%~dp0"
python -c "import PySide6" 2>nul || pip install -r desktop\requirements.txt
start "" pythonw desktop\main.py
