"""PyInstaller spec for the modern (new_ui) application.

Build (example macOS / Linux):
    pyinstaller --noconfirm ModernAutoclicker.spec

On Windows you can also just run:
    pyinstaller --noconfirm --windowed --icon build/icons/modern_app.ico modern_main.py
"""

# -*- mode: python ; coding: utf-8 -*-

import platform
from pathlib import Path
import os

# Stable bundle identifier for macOS bundle; ensure it matches other variants
BUNDLE_ID = 'com.giuliandenicola.advancedautoclicker'

# When PyInstaller executes the spec, __file__ may not be defined. Use CWD.
project_root = Path(os.getcwd())
icon_dir = project_root / "build" / "icons"
icns_icon = icon_dir / "modern_app.icns"
ico_icon = icon_dir / "modern_app.ico"

if platform.system() == 'Windows':
    chosen_icon = str(ico_icon) if ico_icon.exists() else ''
else:
    chosen_icon = str(icns_icon) if icns_icon.exists() else ''

a = Analysis(
    [str(project_root / 'modern_main.py')],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Modern Autoclicker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[chosen_icon],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Modern Autoclicker',
)

if platform.system() == 'Darwin':
    app = BUNDLE(
        coll,
        name='Modern Autoclicker.app',
        icon=chosen_icon or None,
        bundle_identifier=BUNDLE_ID,
    )
