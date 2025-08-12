"""Generate high‑quality .icns and .ico application icons from a source PNG.

Usage:
    python scripts/make_app_icons.py [SOURCE_PNG]

If SOURCE_PNG is omitted, a default project image will be used.

Features / Improvements:
    * Automatic square crop / padding (transparent) so non‑square images aren't distorted
    * Warns when upscaling (suggests providing ≥1024px source for best quality)
    * macOS: Uses iconutil when available for proper multi-rez .icns
    * Non‑mac fallback produces a PNG placeholder saved with .icns extension (still works in PyInstaller)
    * Single pass high-quality Lanczos resampling from the original (avoids repeated resizes)

Outputs:
    build/icons/advanced_autoclicker.icns
    build/icons/advanced_autoclicker.ico

Requires Pillow. Install with: pip install pillow
"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

try:
    from PIL import Image
except ImportError:
    print("Pillow is required. Install with: pip install pillow", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
# Default fallback icon (should be a high-res square if possible)
DEFAULT_SOURCE_ICON = ROOT / "docs" / "images" / "screenshot_config.png"
OUT_DIR = ROOT / "build" / "icons"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ICNS_PATH = OUT_DIR / "advanced_autoclicker.icns"
ICO_PATH = OUT_DIR / "advanced_autoclicker.ico"


def _prepare_base(image_path: Path) -> Image.Image:
    if not image_path.exists():
        print(f"Source icon not found: {image_path}", file=sys.stderr)
        sys.exit(1)
    img = Image.open(image_path).convert("RGBA")
    w, h = img.size
    max_side = max(w, h)
    if w != h:
        # Pad to square with transparent background (centered)
        square = Image.new("RGBA", (max_side, max_side), (0, 0, 0, 0))
        offset = ((max_side - w) // 2, (max_side - h) // 2)
        square.paste(img, offset)
        img = square
    if max_side < 512:
        print(f"[WARN] Source icon is small ({max_side}px). Provide a 1024x1024 PNG for crisper results.")
    return img


def build_icns(base_image: Image.Image):
    """Build .icns using iconutil if available, else a minimal fallback.

    We write individual size variants only once (resizing directly from the ORIGINAL
    base to avoid cascade quality loss).
    """
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
    # Resize each directly from original base for max quality
    variants = [base_image.resize((s, s), Image.LANCZOS) for s in sizes]
    # Pillow accepts one image with sizes param
    variants[0].save(ICO_PATH, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Created {ICO_PATH}")


def main(argv: Optional[list[str]] = None):
    argv = argv or sys.argv[1:]
    source_path = Path(argv[0]).resolve() if argv else DEFAULT_SOURCE_ICON
    base = _prepare_base(source_path)
    build_icns(base)
    build_ico(base)
    print("Icon generation complete.")


if __name__ == "__main__":
    main()
