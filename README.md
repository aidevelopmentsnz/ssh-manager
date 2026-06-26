# SSH Manager

A modern, dark-themed SSH connection manager for macOS. Save your SSH
connections and open them in Terminal with a double-click — no more typing
host, user, and key details every time.

![SSH Manager icon](logo.png)

## Features

- **One-click connect** — double-click a saved connection (or select it and
  hit Connect) to open Terminal and SSH straight in.
- **Connection manager** — add, edit, and delete connections with host, user,
  port, identity file, and extra SSH options.
- **Search/filter** as your list grows.
- **Clean dark UI** — rounded cards, avatar badges, a themed scrollbar, and a
  Proton-inspired purple accent.
- **Quick `/etc/hosts` edit** shortcut.

Connections are stored as plain JSON at
`~/.config/ssh-manager/connections.json`, so they're easy to back up or edit
by hand.

## Download

**[⬇️ Download the latest DMG](https://github.com/aidevelopmentsnz/ssh-manager/releases/latest)** — open it and drag SSH Manager to your Applications folder. The bundled app ships its own Python + Tk, so end users need nothing installed.

Or with [Homebrew](https://brew.sh):

```sh
brew install --cask --no-quarantine aidevelopmentsnz/tap/ssh-manager
```

> **First launch:** the app is currently **unsigned** (not yet notarized), so
> macOS Gatekeeper will warn. Either install with `--no-quarantine` (as above),
> or **right-click the app → Open → Open** once to approve it. Apple Silicon Macs
> run it via Rosetta — you'll be prompted to install Rosetta on first launch if
> it isn't already present.

The sections below are for **running from source or building it yourself**.

## Requirements

| Requirement | Notes |
|-------------|-------|
| macOS | 10.13 or newer |
| [Homebrew](https://brew.sh) | Package manager, used to install a modern Python + Tk |
| `python-tk` (Python 3 + Tk 9) | The system Command Line Tools Python ships a **broken Tk 8.5** that crashes on launch — you must use Homebrew's build |
| `ssh` + `Terminal.app` | Built into macOS |
| Pillow | **Optional** — only needed to regenerate the app icon (see below) |

### 1. Install Homebrew (skip if you already have it)

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Python + Tk

```sh
brew install python-tk
```

This pulls in `python@3.14` and `tcl-tk` (Tk 9). Verify Tk works (should print
a version like `9.0` and **not** crash):

```sh
python3 -c "import tkinter; tkinter.Tk(); print('Tk OK')"
```

> ⚠️ If you run the app with the system `/usr/bin/python3` it will crash with
> a `Tcl_Panic` / `TkpInit` abort. Always use the Homebrew Python.

## Install & run

Clone the repo:

```sh
git clone https://github.com/aidevelopmentsnz/ssh-manager.git
cd ssh-manager
```

Run it directly:

```sh
/usr/local/opt/python@3.14/bin/python3.14 ssh_manager.py
# (Apple Silicon: /opt/homebrew/opt/python@3.14/bin/python3.14 ssh_manager.py)
```

…or build a double-clickable app bundle in `~/Applications`:

```sh
./build_app.sh
open "$HOME/Applications/SSH Manager.app"
```

The build script auto-detects the Homebrew Python (Intel or Apple Silicon) and
points the bundle at your local checkout, so edits to `ssh_manager.py` take
effect next launch.

> First launch may be blocked by Gatekeeper (unsigned app). Right-click the
> app → **Open** → **Open** to approve it once.

## Build a distributable app + DMG

To produce a **self-contained app** (bundles its own Python + Tk, so end users
need *nothing* installed — and the menu bar reads "SSH Manager", not "Python")
plus a drag-to-install DMG:

```sh
./build_dist.sh
```

The release build is **universal2** (Intel + Apple Silicon), so it needs a
universal2 interpreter — install the framework build from
[python.org](https://www.python.org/downloads/macos/) and `build_dist.sh` picks
it up automatically. (Homebrew's `python@3.14` has the newer Tk 9 but is
single-arch, so the script refuses it for a release build; override with
`PYTHON=…` or `ALLOW_SINGLE_ARCH=1` to build a single-arch app anyway.)

Outputs:

- `dist/SSH Manager.app` — standalone app, no dependencies
- `dist/SSH Manager.dmg` — drag-to-Applications installer

The app is **unsigned**, so on first launch recipients right-click the app →
**Open** → **Open** to get past Gatekeeper (only needed once). To ship without
that warning you'd sign + notarize with an Apple Developer ID.

## Regenerating the icon

The app icon is generated from `make_icon.py` (requires Pillow). Use a venv so
you don't touch the Homebrew Python:

```sh
python3 -m venv /tmp/iconvenv
/tmp/iconvenv/bin/pip install Pillow
/tmp/iconvenv/bin/python make_icon.py    # writes icon_master.png
./build_app.sh                           # rebuilds icon.icns + logo.png
```

## Project layout

| File | Purpose |
|------|---------|
| `ssh_manager.py` | The app (UI + connection logic) |
| `build_app.sh` | Builds `SSH Manager.app` into `~/Applications` |
| `make_icon.py` | Generates the icon master PNG |
| `icon_master.png` | 1024px icon source |
| `icon.icns` / `logo.png` | App-bundle icon / in-app header logo |

## License

MIT
