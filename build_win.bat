@echo off
cd /d "%~dp0"
echo Building for Windows...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
venv\Scripts\pyinstaller.exe invoice_creator.spec --noconfirm
echo Build complete! Output: dist\invoice_creator\
pause