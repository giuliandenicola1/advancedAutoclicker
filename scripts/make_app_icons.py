"""Generate .icns and .ico application icons from the provided PNG.

Usage:
    python scripts/make_app_icons.py 

Input PNG (default): src/ChatGPT Image Aug 11, 2025, 11_41_23 PM.png
Outputs:
    build/icons/advanced_autoclicker.icns
    build/icons/advanced_autoclicker.ico

Requires Pillow. On macOS, tries to use iconutil (if available) for .icns;
otherwise falls back to a pure Pillow-based simple .icns (PNG placeholder) variant.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    from PIL import Image
except ImportError:
    print("Pillow is required. Install with: pip install pillow", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SOURCE_ICON = ROOT / "src" / "ChatGPT Image Aug 11, 2025, 11_41_23 PM.png"
OUT_DIR = ROOT / "build" / "icons"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ICNS_PATH = OUT_DIR / "advanced_autoclicker.icns"
ICO_PATH = OUT_DIR / "advanced_autoclicker.ico"


def build_icns(base_image: Image.Image):
    """Build .icns using iconutil if available, else a minimal fallback."""
    if platform.system() != "Darwin":
        # Non-macOS: still output something so spec file doesn't break
        base_image.resize((512, 512), Image.LANCZOS).save(ICNS_PATH, format="PNG")
        print(f"Created placeholder (non-mac) {ICNS_PATH}")
        return
    try:  # macOS path using iconutil
        subprocess.run(["iconutil", "--version"], capture_output=True, check=True)
        with TemporaryDirectory() as td:
            iconset = Path(td) / "AppIcon.iconset"
            iconset.mkdir()
            sizes = [16, 32, 64, 128, 256, 512, 1024]
            for size in sizes:
                img = base_image.resize((size, size), Image.LANCZOS)
                png_path = iconset / f"icon_{size}x{size}.png"
                img.save(png_path, format="PNG")
                if size in (16, 32, 128, 256, 512):
                    img2x = base_image.resize((size * 2, size * 2), Image.LANCZOS)
                    img2x.save(iconset / f"icon_{size}x{size}@2x.png", format="PNG")
            subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(ICNS_PATH)], check=True)
        print(f"Created {ICNS_PATH}")
    except Exception as e:  # pragma: no cover - mac utility path
        print(f"iconutil not available or failed ({e}); using fallback simple icns.")
        base_image.resize((1024, 1024), Image.LANCZOS).save(ICNS_PATH, format="PNG")
        print(f"Created fallback {ICNS_PATH}")


def build_ico(base_image: Image.Image):
    sizes = [16, 24, 32, 48, 64, 128, 256]
    variants = [base_image.resize((s, s), Image.LANCZOS) for s in sizes]
    variants[0].save(ICO_PATH, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Created {ICO_PATH}")


def main():
    if not SOURCE_ICON.exists():
        print(f"Source PNG not found: {SOURCE_ICON}", file=sys.stderr)
        sys.exit(1)
    base = Image.open(SOURCE_ICON).convert("RGBA")
    build_icns(base)
    build_ico(base)
    print("Icon generation complete.")


if __name__ == "__main__":
    main()
