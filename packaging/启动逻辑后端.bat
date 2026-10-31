@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PORT=8765"
if not "%~1"=="" set "PORT=%~1"

set "BUSY="
for /f "tokens=*" %%L in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do set "BUSY=1"
if defined BUSY (
    echo [warn] port %PORT% is already listening -- a sidecar may already be running.
    echo        close that other sidecar window first, then run this again.
    echo.
    pause
    exit /b 1
)

set "PY="
python -c "import sys;sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul && set "PY=python"
if not defined PY (
    py -3 -c "import sys;sys.exit(0)" >nul 2>nul && set "PY=py -3"
)
if not defined PY (
    echo [fail] Python 3 not found.
    echo        install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

echo [ok] starting the sidecar with: %PY%
echo      keep this window open while you play.
echo.
%PY% "%~dp0sidecar\logicd.py" --port %PORT%
echo.
echo sidecar exited -- press any key to close.
pause >nul
endlocal
