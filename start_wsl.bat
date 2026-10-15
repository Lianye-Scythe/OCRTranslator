@echo off
setlocal EnableExtensions DisableDelayedExpansion

if not defined LOCALAPPDATA goto :no_local_app_data
set "VENV_DIR=%LOCALAPPDATA%\OCRTranslator\venv-win315"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

pushd "%~dp0"
if errorlevel 1 goto :source_unavailable
set "SOURCE_PUSHED=1"
if not exist "app\main.py" goto :source_unavailable
if not exist "requirements.txt" goto :source_unavailable

if exist "%PYTHON_EXE%" goto :check_python
echo [OCRTranslator] Creating a Windows Python 3.15 environment...
py -3.15 -m venv "%VENV_DIR%"
if errorlevel 1 goto :venv_failed

:check_python
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.platform == 'win32' and sys.version_info[:2] == (3, 15) else 1)"
if errorlevel 1 goto :venv_failed

echo [OCRTranslator] Checking Windows dependencies...
"%PYTHON_EXE%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :install_failed

if /i "%~1"=="--check" goto :check_only
echo [OCRTranslator] Running WSL source with Windows Python...
echo [OCRTranslator] Close the application to release this console.
"%PYTHON_EXE%" -m app.main %*
set "APP_EXIT_CODE=%ERRORLEVEL%"
popd
if "%APP_EXIT_CODE%"=="0" exit /b 0
echo [ERROR] OCRTranslator exited with code %APP_EXIT_CODE%.
pause
exit /b %APP_EXIT_CODE%

:check_only
"%PYTHON_EXE%" -c "import sys, requests, PIL, pynput, PySide6; import app.main, app.ui.main_window; print('[SUCCESS] Windows Python ' + sys.version.split()[0] + ' can import the WSL source and GUI dependencies.')"
set "CHECK_EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %CHECK_EXIT_CODE%

:no_local_app_data
echo [ERROR] LOCALAPPDATA is unavailable. Run this file from Windows.
goto :failed

:source_unavailable
echo [ERROR] Cannot access the project. Start WSL and keep this file in the repository root.
goto :failed

:venv_failed
echo [ERROR] Cannot create or use the Windows Python 3.15 environment.
echo Install Python 3.15 with the Windows Python launcher, then try again.
echo Environment: "%VENV_DIR%"
goto :failed

:install_failed
echo [ERROR] Windows dependency installation failed. See the pip output above.
goto :failed

:failed
if defined SOURCE_PUSHED popd
if /i not "%~1"=="--check" pause
exit /b 1
