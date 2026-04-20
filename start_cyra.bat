@echo off
title Cyra AI Assistant
cd /d "%~dp0"
echo Starting Cyra...
call venv\Scripts\activate
python main.py
