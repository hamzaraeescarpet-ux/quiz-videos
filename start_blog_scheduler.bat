@echo off
:: ============================================================
:: Blog Automation Scheduler - Startup Runner (1 Blog / Day)
:: PC on hone par ya scheduled task se automatically chalti hai
:: Kaam poora hote hi browser aur terminal window khud band ho jati hai
:: ============================================================

title Blog Auto Scheduler - 1 Blog/Day
cd /d "C:\Users\hamza\OneDrive\Desktop\QuizBot"

echo [%date% %time%] Blog Automation Scheduler starting (1 Blog/Day)...

:: Python executable dhundho
set PYTHON_EXE=python

:: Worker script chalao (1 blog publish karega aur exit karega)
%PYTHON_EXE% blog_automation_worker.py

echo.
echo [%date% %time%] Blog Automation finished! Closing terminal window in 5 seconds...
timeout /t 5 >nul
exit
