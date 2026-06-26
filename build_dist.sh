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

# Locate a Python with a working Tk. A DISTRIBUTION build MUST ship a
# universal2 binary (Intel + Apple Silicon); a single-arch interpreter would
# silently produce an Intel-only (or arm64-only) app — the v1.0 bug, where the
# app only launched on machines that happened to have Rosetta 2 installed. So
# we PREFER a universal2 interpreter and refuse to build single-arch unless
# ALLOW_SINGLE_ARCH=1.
#
# NOTE: python.org framework builds are universal2 (but ship Tk 8.6). Homebrew
# python@3.14 has the newer Tk 9 (nicer HiDPI text) but is single-arch, so it
# is NOT suitable for a release build. Override the interpreter with PYTHON=.
is_universal() {
    local a; a="$(lipo -archs "$(readlink -f "$1" 2>/dev/null || echo "$1")" 2>/dev/null)"
    echo "$a" | grep -q arm64 && echo "$a" | grep -q x86_64
}

CANDIDATES=(
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3
    /opt/homebrew/opt/python@3.14/bin/python3.14
    /usr/local/opt/python@3.14/bin/python3.14
    "$(command -v python3.14)"
    "$(command -v python3)"
)
PY="${PYTHON:-}"
# Pass 1: first universal2 interpreter wins.
if [ -z "$PY" ]; then
    for cand in "${CANDIDATES[@]}"; do
        [ -x "$cand" ] || continue
        if is_universal "$cand"; then PY="$cand"; break; fi
    done
fi
# Pass 2: fall back to any working interpreter (single-arch).
if [ -z "$PY" ]; then
    for cand in "${CANDIDATES[@]}"; do
        [ -x "$cand" ] && { PY="$cand"; break; }
    done
fi
if [ -z "$PY" ]; then
    echo "ERROR: no suitable Python found. Install the universal2 build from python.org." >&2
    exit 1
fi

# Decide target arch from the interpreter's own slices.
TARGET_FLAG=""
if is_universal "$PY"; then
    TARGET_FLAG="--target-arch universal2"
    echo "Using Python: $PY  (universal2 -> building universal app)"
else
    ARCHS="$(lipo -archs "$(readlink -f "$PY" 2>/dev/null || echo "$PY")" 2>/dev/null || true)"
    if [ "${ALLOW_SINGLE_ARCH:-0}" != "1" ]; then
        echo "ERROR: $PY is single-arch (${ARCHS:-unknown}); a release build must be universal2." >&2
        echo "       Install python.org's universal2 build, or set ALLOW_SINGLE_ARCH=1 to override." >&2
        exit 1
    fi
    echo "WARNING: building SINGLE-ARCH app from $PY (${ARCHS:-unknown}) — ALLOW_SINGLE_ARCH=1"
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

# Re-sign AFTER the Info.plist edits. PyInstaller ad-hoc signs the bundle during
# the build, but the PlistBuddy edits above modify Info.plist and break that
# seal (Gatekeeper reports "plist or signature have been modified" /
# "Info.plist=not bound", which surfaces to end users as a "damaged" app).
# Codesign must therefore be the LAST mutation of the bundle.
echo "Re-signing bundle (ad-hoc) after Info.plist edits…"
codesign --force --deep --sign - "dist/$APP_NAME.app"
codesign --verify --deep --strict --verbose=2 "dist/$APP_NAME.app"

# Build a drag-to-install DMG with hdiutil (no Finder automation needed).
echo "Building DMG…"
STAGE="$(mktemp -d)"
cp -R "dist/$APP_NAME.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" \
    -ov -format UDZO "dist/$APP_NAME.dmg" >/dev/null
rm -rf "$STAGE"
echo "Done: dist/$APP_NAME.dmg"
