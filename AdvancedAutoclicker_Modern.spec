"""PyInstaller spec for Advanced Autoclicker using the modern (new_ui) interface.

Build:
    pyinstaller --noconfirm AdvancedAutoclicker_Modern.spec
"""

# -*- mode: python ; coding: utf-8 -*-

import platform
from pathlib import Path
import os

project_root = Path(os.getcwd())
icon_dir = project_root / "build" / "icons"
icns_icon = icon_dir / "advanced_autoclicker.icns"
ico_icon = icon_dir / "advanced_autoclicker.ico"

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
    name='Advanced Autoclicker',
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
    # Only set icon when a valid file exists to avoid PyInstaller CopyIcons errors on Windows.
    icon=(chosen_icon or None),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Advanced Autoclicker',
)

if platform.system() == 'Darwin':
    app = BUNDLE(
        coll,
        name='Advanced Autoclicker.app',
        icon=chosen_icon or None,
        bundle_identifier=None,
    )
