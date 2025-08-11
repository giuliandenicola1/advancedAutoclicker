#!/usr/bin/env bash
set -euo pipefail

# create_dmg.sh
# Packages the built macOS .app bundle into a compressed DMG for distribution.
# Prerequisites:
#   1. Run PyInstaller build so that "dist/Advanced Autoclicker.app" exists.
#   2. (Optional) Codesign the .app before packaging for better user experience.
# Usage:
#   bash scripts/create_dmg.sh                # Produces dist/AdvancedAutoclicker-macOS.dmg
#   APP_NAME="Advanced Autoclicker" DMG_NAME="AdvancedAutoclicker" bash scripts/create_dmg.sh

APP_NAME=${APP_NAME:-"Advanced Autoclicker"}
APP_BUNDLE_PATH=${APP_BUNDLE_PATH:-"dist/${APP_NAME}.app"}
DMG_NAME=${DMG_NAME:-"AdvancedAutoclicker-macOS"}
VOL_NAME=${VOL_NAME:-"${APP_NAME}"}
STAGING_DIR="dist/dmg_staging"
OUTPUT_DMG="dist/${DMG_NAME}.dmg"

if [[ ! -d "${APP_BUNDLE_PATH}" ]]; then
  echo "ERROR: App bundle not found at: ${APP_BUNDLE_PATH}" >&2
  echo "Build it first, e.g.: pyinstaller --noconfirm AdvancedAutoclicker_Modern.spec" >&2
  exit 1
fi

echo "[create_dmg] Packaging '${APP_BUNDLE_PATH}' -> ${OUTPUT_DMG}";
rm -rf "${STAGING_DIR}" "${OUTPUT_DMG}" || true
mkdir -p "${STAGING_DIR}" || true

# Copy app bundle
cp -R "${APP_BUNDLE_PATH}" "${STAGING_DIR}/"  # preserves bundle structure

# Create Applications symlink for drag-and-drop install UX
ln -s /Applications "${STAGING_DIR}/Applications" || true

# Build compressed DMG (UDZO = zlib-compressed read-only)
hdiutil create -volname "${VOL_NAME}" -srcfolder "${STAGING_DIR}" -ov -format UDZO "${OUTPUT_DMG}" >/dev/null

echo "[create_dmg] DMG created: ${OUTPUT_DMG}";
echo "[create_dmg] Verifying DMG checksum:";
shasum -a 256 "${OUTPUT_DMG}" || true

echo "Done.";
