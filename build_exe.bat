@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)
call ".venv\Scripts\activate"
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --noconsole --onefile --name OCRTranslator launcher.pyw
echo.
echo Build complete. EXE: dist\OCRTranslator.exe
pause
