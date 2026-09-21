@echo off
setlocal
cd /d "%~dp0" || exit /b 1
echo Building for Windows...

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Windows virtual environment not found.
    echo Create it with: py -m venv venv
    echo Then install dependencies with: venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

if not exist "venv\Scripts\pyinstaller.exe" (
    echo ERROR: PyInstaller is not installed in the Windows virtual environment.
    echo Install it with: venv\Scripts\python.exe -m pip install pyinstaller
    exit /b 1
)

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
venv\Scripts\pyinstaller.exe invoice_creator.spec --noconfirm
if errorlevel 1 exit /b 1
echo Build complete! Output: dist\invoice_creator\
pause