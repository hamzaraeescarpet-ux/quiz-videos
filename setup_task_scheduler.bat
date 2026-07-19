@echo off
:: ============================================================
:: Blog Auto Scheduler - Windows Task Scheduler Setup
:: SIRF EK BAAR CHALAO - ye task register ho jayega
:: Phir har baar PC on hone par automatically chalega
::
:: Administrator rights zaruri hain!
:: Right-click > "Run as Administrator" karke chalao
:: ============================================================

title Task Scheduler Setup - Blog Auto Scheduler

echo.
echo ============================================================
echo   Blog Auto Scheduler - Windows Task Scheduler Setup
echo ============================================================
echo.

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [ERROR] Administrator rights nahi hain!
    echo.
    echo Is file par Right-click karo aur
    echo "Run as Administrator" select karo.
    echo.
    pause
    exit /b 1
)

echo [OK] Administrator rights confirm ho gaye.
echo.

:: Variables
set TASK_NAME=BlogAutoScheduler
set BAT_FILE=C:\Users\hamza\OneDrive\Desktop\QuizBot\start_blog_scheduler.bat
set WORKING_DIR=C:\Users\hamza\OneDrive\Desktop\QuizBot

echo Task Name  : %TASK_NAME%
echo Bat File   : %BAT_FILE%
echo Trigger    : PC startup pe + Login pe
echo.

:: Pehle purana task delete karo (agar tha)
echo Purana task (agar tha) hata raha hoon...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Naya task create karo
:: - ONLOGON: har baar user login kare
:: - DELAY: login k 2 minute baad start (system stable hone de)
:: - RUN IN BACKGROUND (minimized CMD window)
echo Naya scheduled task register kar raha hoon...

schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "cmd.exe /c \"%BAT_FILE%\"" ^
  /sc ONLOGON ^
  /delay 0002:00 ^
  /rl HIGHEST ^
  /f

if %errorLevel% EQU 0 (
    echo.
    echo ============================================================
    echo   [SUCCESS] Task successfully register ho gaya!
    echo ============================================================
    echo.
    echo Ab har baar PC on karke login karne k 2 minute baad
    echo blog scheduler automatically start ho jayega.
    echo.
    echo Task Manager > Task Scheduler mein "%TASK_NAME%" naam se
    echo is task ko dekh sakte ho.
    echo.
    echo Log file yahan save hoti hai:
    echo   %WORKING_DIR%\blog_automation_worker.log
    echo.
) else (
    echo.
    echo [ERROR] Task register nahi hua. Upar ki error dekho.
    echo.
)

pause
