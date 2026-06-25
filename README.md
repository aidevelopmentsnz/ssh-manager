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

## Requirements

macOS with a **modern Tk** (Tk 9 / 8.6). The system Command Line Tools Python
ships a broken Tk 8.5 that crashes, so install Homebrew's Python + Tk:

```sh
brew install python-tk
```

## Run

```sh
python3 ssh_manager.py
```

…or build a double-clickable app bundle:

```sh
./build_app.sh
```

This creates **SSH Manager.app** in `~/Applications`.

## Regenerating the icon

The app icon is generated from `make_icon.py` (requires Pillow):

```sh
python3 -m venv /tmp/iconvenv && /tmp/iconvenv/bin/pip install Pillow
/tmp/iconvenv/bin/python make_icon.py   # writes icon_master.png
```

Then rebuild `icon.icns` / `logo.png` via `build_app.sh`.

## License

MIT
