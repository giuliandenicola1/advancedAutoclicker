"""py2app setup script for Modern Autoclicker (new_ui based).

Build on macOS (after creating icons):
    python scripts/make_app_icons.py
    python setup_modern.py py2app

Resulting .app placed in 'dist'.
"""

from setuptools import setup

APP = ['modern_main.py']
OPTIONS = {
    'iconfile': 'build/icons/advanced_autoclicker.icns',
    'argv_emulation': False,
    'packages': ['PIL', 'numpy', 'pyautogui', 'pytesseract', 'ttkbootstrap', 'cv2'],
    'plist': {
        'CFBundleName': 'Advanced Autoclicker',
        'CFBundleDisplayName': 'Advanced Autoclicker',
        'CFBundleIdentifier': 'com.example.advancedautoclicker',
    }
}

setup(
    app=APP,
    name='Advanced Autoclicker',
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
