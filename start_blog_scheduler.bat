@echo off
:: ============================================================
:: Blog Automation Scheduler - Startup Runner
:: PC on hone par ye automatically chalti hai
:: Windows Task Scheduler is file ko run karta hai
:: ============================================================

title Blog Auto Scheduler - Running...
cd /d "C:\Users\hamza\OneDrive\Desktop\QuizBot"

echo [%date% %time%] Blog Automation Scheduler starting...

:: Python executable dhundho
set PYTHON_EXE=python

:: Worker script chalao (ye khud hi loop mein chalega)
%PYTHON_EXE% blog_automation_worker.py

echo [%date% %time%] Blog Automation Scheduler ended.
pause
