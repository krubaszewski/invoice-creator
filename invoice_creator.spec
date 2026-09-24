# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

_icon_map = {"win32": "resources/icon.ico", "darwin": "resources/icon.icns", "linux": "resources/icon.png"}
_icon = _icon_map.get(sys.platform, "resources/icon.png")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("resources/fonts", "resources/fonts"),
    ],
    hiddenimports=[
        "pymupdf",
        "fpdf",
        "PIL",
        "PIL.ImageFont",
        "weasyprint",
        "cssselect2",
        "tinycss2",
        "pyphen",
        "lxml",
        "reportlab",
        "pydyf",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["runtime_hook.py"],
    excludes=[
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="invoice_creator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon,
    onefile=False,
)
