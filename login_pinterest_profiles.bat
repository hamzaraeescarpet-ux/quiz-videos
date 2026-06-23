@echo off
cd /d "%~dp0"
:menu
cls
echo =======================================================
echo Pinterest Accounts Login Helper (QuizViral AI)
echo =======================================================
echo.
echo Select the profile number to open for manual login:
echo [1] Profile 1: hamzaraeescarpet
echo [2] Profile 2: hamzarais2023
echo [3] Profile 3: hamzarais354
echo [4] Profile 4: deshkikhabar79
echo [5] Exit
echo.
set /p choice="Enter profile number (1-5): "
echo.
if "%choice%"=="1" (
    echo Opening Profile 1 (hamzaraeescarpet)...
    python pinterest_auto_pin.py --login 1
    goto menu
)
if "%choice%"=="2" (
    echo Opening Profile 2 (hamzarais2023)...
    python pinterest_auto_pin.py --login 2
    goto menu
)
if "%choice%"=="3" (
    echo Opening Profile 3 (hamzarais354)...
    python pinterest_auto_pin.py --login 3
    goto menu
)
if "%choice%"=="4" (
    echo Opening Profile 4 (deshkikhabar79)...
    python pinterest_auto_pin.py --login 4
    goto menu
)
if "%choice%"=="5" exit
echo Invalid choice, try again.
pause
goto menu
