#!/bin/bash
# Build a self-contained "SSH Manager.app" and a drag-to-install DMG.
#
# Produces:
#   dist/SSH Manager.app   — standalone app (bundles its own Python + Tk 9)
#   dist/SSH Manager.dmg   — drag-to-Applications installer
#
# Requirements (build machine only — NOT the end user):
#   - Homebrew Python with Tk:  brew install python-tk
#   - create-dmg:               brew install create-dmg
#
# The resulting app has no external dependencies and the menu bar shows
# "SSH Manager" (not "Python").
set -e

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SRC_DIR"

APP_NAME="SSH Manager"
BUNDLE_ID="co.novaweb.sshmanager"
VENV="${BUILD_VENV:-/tmp/sshmgr-buildvenv}"

# Locate a Homebrew Python with a working Tk (Intel or Apple Silicon).
PY=""
for cand in \
    /usr/local/opt/python@3.14/bin/python3.14 \
    /opt/homebrew/opt/python@3.14/bin/python3.14 \
    "$(command -v python3.14)"; do
    if [ -x "$cand" ]; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
    echo "ERROR: Homebrew python@3.14 not found. Run: brew install python-tk" >&2
    exit 1
fi
echo "Using Python: $PY"

# Build venv with PyInstaller.
if [ ! -x "$VENV/bin/pyinstaller" ]; then
    echo "Creating build venv at $VENV"
    "$PY" -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip pyinstaller
fi

echo "Building app bundle…"
rm -rf build "dist/$APP_NAME.app" "dist/$APP_NAME.dmg"
"$VENV/bin/pyinstaller" --noconfirm --windowed --name "$APP_NAME" \
    --icon icon.icns \
    --add-data "logo.png:." \
    --osx-bundle-identifier "$BUNDLE_ID" \
    ssh_manager.py

# Build a drag-to-install DMG with hdiutil (no Finder automation needed).
echo "Building DMG…"
STAGE="$(mktemp -d)"
cp -R "dist/$APP_NAME.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" \
    -ov -format UDZO "dist/$APP_NAME.dmg" >/dev/null
rm -rf "$STAGE"
echo "Done: dist/$APP_NAME.dmg"
