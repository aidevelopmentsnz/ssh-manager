#!/bin/bash
# Build "SSH Manager.app" into ~/Applications.
# Regenerates icon.icns and logo.png from icon_master.png if sips is available.
set -e

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$HOME/Applications/SSH Manager.app"

echo "Building $APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

# --- Icon assets ---------------------------------------------------------
if command -v sips >/dev/null && command -v iconutil >/dev/null \
   && [ -f "$SRC_DIR/icon_master.png" ]; then
    ICONSET="$SRC_DIR/AppIcon.iconset"
    rm -rf "$ICONSET"; mkdir "$ICONSET"
    M="$SRC_DIR/icon_master.png"
    sips -z 16 16   "$M" --out "$ICONSET/icon_16x16.png"      >/dev/null
    sips -z 32 32   "$M" --out "$ICONSET/icon_16x16@2x.png"   >/dev/null
    sips -z 32 32   "$M" --out "$ICONSET/icon_32x32.png"      >/dev/null
    sips -z 64 64   "$M" --out "$ICONSET/icon_32x32@2x.png"   >/dev/null
    sips -z 128 128 "$M" --out "$ICONSET/icon_128x128.png"    >/dev/null
    sips -z 256 256 "$M" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
    sips -z 256 256 "$M" --out "$ICONSET/icon_256x256.png"    >/dev/null
    sips -z 512 512 "$M" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
    sips -z 512 512 "$M" --out "$ICONSET/icon_512x512.png"    >/dev/null
    cp "$M" "$ICONSET/icon_512x512@2x.png"
    iconutil -c icns "$ICONSET" -o "$SRC_DIR/icon.icns"
    rm -rf "$ICONSET"
    sips -z 56 56 "$M" --out "$SRC_DIR/logo.png" >/dev/null
    echo "  regenerated icon.icns + logo.png"
fi
cp "$SRC_DIR/icon.icns" "$APP/Contents/Resources/icon.icns"

# --- Info.plist ----------------------------------------------------------
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>SSH Manager</string>
    <key>CFBundleDisplayName</key><string>SSH Manager</string>
    <key>CFBundleIdentifier</key><string>co.novaweb.sshmanager</string>
    <key>CFBundleVersion</key><string>1.0</string>
    <key>CFBundleShortVersionString</key><string>1.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleExecutable</key><string>launcher</string>
    <key>CFBundleIconFile</key><string>icon</string>
    <key>LSMinimumSystemVersion</key><string>10.13</string>
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST

# --- Launcher ------------------------------------------------------------
# Points at this source checkout so edits are picked up immediately.
cat > "$APP/Contents/MacOS/launcher" <<SH
#!/bin/bash
for PY in \\
    /usr/local/opt/python@3.14/bin/python3.14 \\
    /opt/homebrew/opt/python@3.14/bin/python3.14 \\
    "\$(command -v python3.14)" \\
    "\$(command -v python3)"; do
    if [ -x "\$PY" ]; then
        exec "\$PY" "$SRC_DIR/ssh_manager.py"
    fi
done
SH
chmod +x "$APP/Contents/MacOS/launcher"

echo "Done. Launch with: open \"$APP\""
