@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PYTHONW_EXE=%VENV_DIR%\Scripts\pythonw.exe"
set "LAUNCHER=launcher.pyw"

echo [OCRTranslator] Checking runtime environment...

if not exist "%PYTHON_EXE%" (
    echo [OCRTranslator] Virtual environment not found. Creating .venv ...
    where python >nul 2>nul
    if errorlevel 1 goto :no_python
    python -m venv "%VENV_DIR%"
    if errorlevel 1 goto :venv_failed
)

echo [OCRTranslator] Checking required packages...
"%PYTHON_EXE%" -c "import requests, PIL, pynput, PySide6" >nul 2>nul
if errorlevel 1 (
    echo [OCRTranslator] Installing packages from requirements.txt ...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 goto :install_failed
)

if not exist "%PYTHONW_EXE%" goto :venv_failed
if not exist "%LAUNCHER%" goto :launcher_missing

echo [OCRTranslator] Launching application...
start "" "%PYTHONW_EXE%" "%LAUNCHER%"
exit /b 0

:no_python
echo.
echo [ERROR] Python was not found on PATH.
echo Please install Python 3.11+ and enable "Add Python to PATH", then run this file again.
pause
exit /b 1

:venv_failed
echo.
echo [ERROR] Failed to create or access .venv.
echo You can try these commands manually:
echo   python -m venv .venv
echo   .venv\Scripts\python -m pip install -r requirements.txt
pause
exit /b 1

:install_failed
echo.
echo [ERROR] Failed to install required packages.
echo You can try this command manually:
echo   .venv\Scripts\python -m pip install -r requirements.txt
pause
exit /b 1

:launcher_missing
echo.
echo [ERROR] launcher.pyw was not found.
pause
exit /b 1
