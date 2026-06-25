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
BUNDLE_ID="nz.co.aidevelopments.sshmanager"
APP_VERSION="${APP_VERSION:-1.0}"
VENV="${BUILD_VENV:-/tmp/sshmgr-buildvenv}"

# Locate a Python with a working Tk. Prefer a Homebrew python with the modern
# Tk 9 (proper Retina/HiDPI scaling — renders text at full size, matching the
# launcher build); fall back to a python.org framework build. Override with
# PYTHON=/path/to/python3.
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
    for cand in \
        /opt/homebrew/opt/python@3.14/bin/python3.14 \
        /usr/local/opt/python@3.14/bin/python3.14 \
        "$(command -v python3.14)" \
        /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
        /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
        /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 \
        "$(command -v python3)"; do
        if [ -x "$cand" ]; then PY="$cand"; break; fi
    done
fi
if [ -z "$PY" ]; then
    echo "ERROR: no suitable Python found. Run: brew install python-tk" >&2
    exit 1
fi

# Decide target arch from the interpreter's own slices.
ARCHS="$(lipo -archs "$(readlink -f "$PY" 2>/dev/null || echo "$PY")" 2>/dev/null || true)"
TARGET_FLAG=""
if echo "$ARCHS" | grep -q arm64 && echo "$ARCHS" | grep -q x86_64; then
    TARGET_FLAG="--target-arch universal2"
    echo "Using Python: $PY  (universal2 -> building universal app)"
else
    echo "Using Python: $PY  (single-arch: ${ARCHS:-unknown})"
fi

# Build venv with PyInstaller. (Keyed to the chosen interpreter.)
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
    $TARGET_FLAG \
    ssh_manager.py

# Stamp a real version into the bundle (PyInstaller leaves it at 0.0.0).
PLIST="dist/$APP_NAME.app/Contents/Info.plist"
for key in CFBundleShortVersionString CFBundleVersion; do
    /usr/libexec/PlistBuddy -c "Set :$key $APP_VERSION" "$PLIST" 2>/dev/null \
        || /usr/libexec/PlistBuddy -c "Add :$key string $APP_VERSION" "$PLIST"
done
echo "Stamped version $APP_VERSION"

# Build a drag-to-install DMG with hdiutil (no Finder automation needed).
echo "Building DMG…"
STAGE="$(mktemp -d)"
cp -R "dist/$APP_NAME.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" \
    -ov -format UDZO "dist/$APP_NAME.dmg" >/dev/null
rm -rf "$STAGE"
echo "Done: dist/$APP_NAME.dmg"
