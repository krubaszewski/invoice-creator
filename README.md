# Invoice Creator

Desktop application for generating invoices. Built with Python and PyInstaller.

## Prerequisites

- Python 3.x
- [PyInstaller](https://www.pyinstaller.org/)
- Git repository with dependencies installed

### Install dependencies

```bash
pip install -r requirements.txt
```

## Build

### macOS

```bash
./build_mac.sh
```

Output: `dist/invoice_creator.app`

### Linux

```bash
./build_linux.sh
```

Output: `dist/invoice_creator/`

### Windows

```bat
py -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m pip install pyinstaller
build_win.bat
```

Output: `dist\invoice_creator\`

## Run

```bash
python main.py
```
