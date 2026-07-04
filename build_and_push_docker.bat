@echo off
chcp 65001 > nul
cd /d "%~dp0"
python build_and_push_docker.py
pause
