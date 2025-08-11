# Advanced Autoclicker

An advanced, modular desktop autoclicker that can monitor multiple screen positions and only click when user‑defined condition sets (ALL or ANY logic) are satisfied. Supports complex condition groups, color / pixel / area checks, delayed start, and real‑time monitoring with logs.

> Attribution: This codebase (application logic, UI structure, build scripts, and packaging configuration) was fully authored with the assistance of AI.

## Key Features
- Multiple independent click conditions (color match, position, area, etc.)
- Condition groups with ALL / ANY logic
- Real‑time monitoring & activity logs (separate action / error / startup logs)
- Configurable delays & controlled start/stop
- Modular Tk / ttkbootstrap modern UI (tabbed, resizable, splash screen)
- Cross‑platform build setup (macOS & Windows) using PyInstaller
- Optional macOS app bundle via py2app

## Project Layout (Essentials)
- `modern_main.py` – Packaged entrypoint (used by PyInstaller)
- `new_ui.py` – Modern modular UI (mixins in `ui_*.py` files)
- `clicker.py` – Core clicking logic
- `detection.py` / `monitor.py` – Condition evaluation & monitoring helpers
- `logger.py` – Centralized multi-file logging + heartbeat
- `diagnostics.py` – Startup environment diagnostics
- `AdvancedAutoclicker_Modern.spec` – PyInstaller spec
- `scripts/make_app_icons.py` – Icon generation (.icns / .ico)
- `requirements.txt` – Python dependencies

## Prerequisites
- Python 3.11+ (developed on 3.13)
- macOS or Windows (Linux may work but not the packaging focus)
- For macOS icon conversion (optional nicer .icns): Xcode Command Line Tools providing `iconutil`

## Install Dependencies
Create and activate a virtual environment (recommended):

```bash
python3 -m venv autoclicker_venv
source autoclicker_venv/bin/activate  # Windows: autoclicker_venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Running From Source (Dev Mode)
```bash
source autoclicker_venv/bin/activate
python modern_main.py
```
Logs are written to a per‑user directory (e.g. macOS: `~/Library/Logs/AdvancedAutoclicker`).

## Building (PyInstaller)
The spec file embeds the modern UI and optional icon assets generated into `build/icons`.

1. (Optional) Regenerate icons from a base PNG placed at `scripts/base_icon.png` (name it or adjust script):
	```bash
	source autoclicker_venv/bin/activate
	python scripts/make_app_icons.py
	```
2. Build the application:
	```bash
	source autoclicker_venv/bin/activate
	pyinstaller --noconfirm AdvancedAutoclicker_Modern.spec
	```
3. Result:
	- macOS: `dist/Advanced Autoclicker.app`
	- Windows (run analogous command on Windows): `dist/Advanced Autoclicker/Advanced Autoclicker.exe`

If the icon tool `iconutil` was not available, a fallback `.icns` containing a single size is created; install Xcode tools for better scaling:
```bash
xcode-select --install
```

## Alternative macOS Build (py2app)
```bash
python setup_modern.py py2app -A   # alias build for dev
python setup_modern.py py2app      # full optimized bundle
```
Output appears under `dist/Advanced Autoclicker.app`.

## Windows Build Notes
On Windows PowerShell / CMD (after cloning repo):
```powershell
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --noconfirm AdvancedAutoclicker_Modern.spec
```
Ensure `ttkbootstrap` is installed (it’s conditional in requirements; Windows satisfies condition).

## Logging & Diagnostics
At startup the app logs environment + frozen state. Heartbeat messages every 30s confirm liveness. Check:
```
macOS: ~/Library/Logs/AdvancedAutoclicker/
Windows: %AppData%\AdvancedAutoclicker\Logs\
```
Files include `autoclicker.log`, `errors.log`, and `actions.log`.

## Customizing Conditions
Within the UI you can add multiple condition rows and group them:
1. Select a screen position / area / color sample.
2. Define condition logic (e.g., color equals, area contains color, etc.).
3. Group conditions and choose group logic (ALL or ANY) before enabling the autoclicker.
4. Start monitoring; when active, a click triggers only when its group logic passes.

## Troubleshooting
- No window on macOS first launch: ensure app is focused (we lift/focus programmatically) or check logs.
- Icon blurry: regenerate icons with `iconutil` present.
- Tesseract OCR features missing: install native Tesseract separately if required for advanced detection.

## Roadmap Ideas
- Configuration persistence (save/load rule sets)
- Headless mode / CLI batch automation
- Extended condition types (image similarity, template matching)
- Auto update & code signing / notarization steps

## License
Specify your chosen license here (MIT / Apache-2.0 / etc.).

## Attribution Reminder
This project was fully authored with AI assistance (design, code, docs). Review and validate before production use.

---
Happy automating!
