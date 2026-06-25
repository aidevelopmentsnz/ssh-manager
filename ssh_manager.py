#!/usr/bin/env python3
"""
SSH Manager — a modern, lightweight dark GUI for saving SSH connections
and opening them in Terminal.

Pick a saved connection (double-click, or select + Connect) and Terminal.app
opens and SSHes straight in. Connections are stored as JSON at
~/.config/ssh-manager/connections.json so they're easy to back up or edit.

Requires a modern Tk (e.g. Homebrew python-tk). The system Command Line Tools
Python ships a broken Tk 8.5 and will crash.
"""

import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog

CONFIG_DIR = os.path.expanduser("~/.config/ssh-manager")
CONFIG_PATH = os.path.join(CONFIG_DIR, "connections.json")

DONATE_URL = "https://buy.stripe.com/fZu5kE74kbb67dK5V86J200"


def resource_path(name):
    """Locate a bundled data file, whether running from source or frozen."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS",
                       os.path.dirname(os.path.abspath(sys.executable)))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)

# ---------------------------------------------------------------------------
# Palette (Proton-inspired)
# ---------------------------------------------------------------------------
BG = "#16141F"          # deep window base
SURFACE = "#25232E"     # cards / inputs
SURFACE_HI = "#322F3D"  # hover
SEL = "#312C46"         # selected card (purple-tinted)
BORDER = "#34313F"
TEXT = "#EDECF0"
SUBTEXT = "#8F8A9D"
ACCENT = "#6D4AFF"      # Proton purple
ACCENT_HI = "#8A6EFF"
RED = "#DC3251"
RED_HI = "#E85575"
ON_ACCENT = "#FFFFFF"

# Avatar badge colors (Proton-style contact avatars)
BADGE_COLORS = ["#6D4AFF", "#DB60D6", "#3CB6A6", "#2C8DFF", "#F0A23B", "#E8638B"]


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
def load_connections():
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def save_connections(connections):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(connections, f, indent=2)


# ---------------------------------------------------------------------------
# SSH launching
# ---------------------------------------------------------------------------
def build_ssh_command(conn):
    parts = ["ssh"]
    port = str(conn.get("port", "")).strip()
    if port and port != "22":
        parts += ["-p", port]
    identity = conn.get("identity", "").strip()
    if identity:
        parts += ["-i", os.path.expanduser(identity)]
    extra = conn.get("extra", "").strip()
    if extra:
        parts.append(extra)
    user = conn.get("user", "").strip()
    host = conn.get("host", "").strip()
    target = f"{user}@{host}" if user else host
    parts.append(target)
    return " ".join(parts)


def open_in_terminal(conn):
    cmd = build_ssh_command(conn)
    escaped = cmd.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        f'tell application "Terminal"\n'
        f'    activate\n'
        f'    do script "{escaped}"\n'
        f'end tell'
    )
    subprocess.run(["osascript", "-e", script])


# ---------------------------------------------------------------------------
# Canvas drawing helpers
# ---------------------------------------------------------------------------
def round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def badge_color(name):
    return BADGE_COLORS[sum(ord(c) for c in name) % len(BADGE_COLORS)]


# ---------------------------------------------------------------------------
# Rounded button
# ---------------------------------------------------------------------------
class RoundButton(tk.Canvas):
    def __init__(self, parent, text, command, *, fill, fill_hi, fg, font,
                 outer_bg, height=42, padx=22, radius=12):
        width = font.measure(text) + 2 * padx
        super().__init__(parent, width=width, height=height,
                         bg=outer_bg, highlightthickness=0, cursor="pointinghand")
        self.command = command
        self.fill, self.fill_hi, self.fg = fill, fill_hi, fg
        self.font, self.radius, self.text = font, radius, text
        self._hover = False
        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: self.command())

    def _draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        fill = self.fill_hi if self._hover else self.fill
        round_rect(self, 1, 1, w - 1, h - 1, self.radius, fill=fill, outline="")
        self.create_text(w / 2, h / 2, text=self.text, fill=self.fg, font=self.font)

    def _on_enter(self, _):
        self._hover = True
        self._draw()

    def _on_leave(self, _):
        self._hover = False
        self._draw()


# ---------------------------------------------------------------------------
# Rounded entry
# ---------------------------------------------------------------------------
class RoundEntry(tk.Canvas):
    def __init__(self, parent, textvariable, *, outer_bg, font, placeholder="",
                 height=44, radius=12):
        super().__init__(parent, height=height, bg=outer_bg, highlightthickness=0)
        self.radius = radius
        self.var = textvariable
        self.placeholder = placeholder
        self._focused = False
        self.entry = tk.Entry(
            self, textvariable=textvariable, relief="flat", bd=0,
            bg=SURFACE, fg=TEXT, insertbackground=ACCENT, font=font,
            highlightthickness=0,
        )
        self._win = self.create_window(0, 0, window=self.entry, anchor="w")
        self.bind("<Configure>", self._draw)
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        if placeholder:
            self._show_placeholder()

    def _draw(self, _=None):
        self.delete("bg")
        w, h = self.winfo_width(), self.winfo_height()
        outline = ACCENT if self._focused else BORDER
        round_rect(self, 1, 1, w - 1, h - 1, self.radius,
                   fill=SURFACE, outline=outline, width=1.5, tags="bg")
        self.tag_lower("bg")
        self.coords(self._win, 15, h / 2)
        self.itemconfig(self._win, width=w - 30)

    def _focus_in(self, _):
        self._focused = True
        if self.placeholder and self.entry.get() == self.placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT)
        self._draw()

    def _focus_out(self, _):
        self._focused = False
        if self.placeholder and not self.entry.get():
            self._show_placeholder()
        self._draw()

    def _show_placeholder(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=SUBTEXT)

    def get(self):
        v = self.entry.get()
        return "" if v == self.placeholder else v


# ---------------------------------------------------------------------------
# Thin themed scrollbar (native macOS scrollbars ignore colors)
# ---------------------------------------------------------------------------
class ThinScrollbar(tk.Canvas):
    PAD = 2

    def __init__(self, parent, command, *, outer_bg, width=8):
        super().__init__(parent, width=width, bg=outer_bg, highlightthickness=0)
        self.command = command  # the canvas's yview
        self.first, self.last = 0.0, 1.0
        self._drag_offset = 0
        self._hover = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def set(self, first, last):
        """Called by the canvas via yscrollcommand."""
        self.first, self.last = float(first), float(last)
        self._draw()

    def _track_h(self):
        return max(1, self.winfo_height() - 2 * self.PAD)

    def _thumb_bounds(self):
        th = self._track_h()
        y1 = self.PAD + self.first * th
        y2 = self.PAD + self.last * th
        return y1, y2

    def _draw(self):
        self.delete("all")
        # Hide entirely when everything fits.
        if self.first <= 0.0 and self.last >= 1.0:
            return
        w = self.winfo_width()
        y1, y2 = self._thumb_bounds()
        if y2 - y1 < 24:  # enforce a minimum draggable size
            mid = (y1 + y2) / 2
            y1, y2 = mid - 12, mid + 12
        r = (w - 2 * self.PAD) / 2
        color = ACCENT if self._hover else SURFACE_HI
        round_rect(self, self.PAD, y1, w - self.PAD, y2, r,
                   fill=color, outline="")

    def _on_enter(self, _):
        self._hover = True
        self._draw()

    def _on_leave(self, _):
        self._hover = False
        self._draw()

    def _on_click(self, event):
        y1, y2 = self._thumb_bounds()
        if y1 <= event.y <= y2:
            self._drag_offset = event.y - y1
        else:
            self._drag_offset = (y2 - y1) / 2
            self._move_to(event.y)

    def _on_drag(self, event):
        self._move_to(event.y)

    def _move_to(self, y):
        top = y - self._drag_offset
        frac = (top - self.PAD) / self._track_h()
        frac = max(0.0, min(1.0, frac))
        self.command("moveto", frac)


# ---------------------------------------------------------------------------
# Connection card
# ---------------------------------------------------------------------------
class Card(tk.Canvas):
    HEIGHT = 74

    def __init__(self, parent, conn, *, selected, on_select, on_connect,
                 fonts):
        super().__init__(parent, height=self.HEIGHT, bg=BG,
                         highlightthickness=0, cursor="pointinghand")
        self.conn = conn
        self.selected = selected
        self.fonts = fonts
        self._hover = False
        self.on_connect = on_connect
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: on_select())
        self.bind("<Double-Button-1>", lambda e: on_connect())

    def _on_enter(self, _):
        self._hover = True
        self._draw()

    def _on_leave(self, _):
        self._hover = False
        self._draw()

    def set_selected(self, value):
        if self.selected != value:
            self.selected = value
            self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.HEIGHT
        conn = self.conn
        host = conn.get("host", "")
        user = conn.get("user", "")
        name = conn.get("name", host) or host
        port = str(conn.get("port", "")).strip()
        target = f"{user}@{host}" if user else host
        if port and port != "22":
            target += f":{port}"

        if self.selected:
            fill, outline = SEL, ACCENT
        elif self._hover:
            fill, outline = SURFACE_HI, ""
        else:
            fill, outline = SURFACE, ""
        round_rect(self, 4, 4, w - 4, h - 4, 16, fill=fill,
                   outline=outline, width=1.5 if outline else 0)

        # Avatar badge
        cx, cy, r = 38, h / 2, 19
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         fill=badge_color(name), outline="")
        self.create_text(cx, cy, text=(name[:1].upper() or "?"),
                         fill=ON_ACCENT, font=self.fonts["badge"])

        # Text
        self.create_text(70, cy - 11, text=name, anchor="w",
                         fill=TEXT, font=self.fonts["title"])
        self.create_text(70, cy + 11, text=target, anchor="w",
                         fill=SUBTEXT, font=self.fonts["sub"])

        # Chevron / connect affordance
        chev_color = ACCENT_HI if (self._hover or self.selected) else SUBTEXT
        self.create_text(w - 22, cy, text="›", anchor="e",
                         fill=chev_color, font=self.fonts["chev"])


# ---------------------------------------------------------------------------
# Add / Edit dialog
# ---------------------------------------------------------------------------
class ConnectionDialog(tk.Toplevel):
    def __init__(self, parent, title, conn=None):
        super().__init__(parent)
        self.configure(bg=BG)
        self.title("")
        self.resizable(False, False)
        self.result = None
        conn = conn or {}
        self.transient(parent)
        self.grab_set()

        f_label = tkfont.Font(family="Helvetica Neue", size=11)
        f_entry = tkfont.Font(family="Menlo", size=12)
        f_title = tkfont.Font(family="Helvetica Neue", size=18, weight="bold")
        f_btn = tkfont.Font(family="Helvetica Neue", size=12, weight="bold")

        wrap = tk.Frame(self, bg=BG, padx=28, pady=24)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(1, weight=1)

        tk.Label(wrap, text=title, bg=BG, fg=TEXT, font=f_title).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 20))

        fields = [
            ("Name", "name", ""),
            ("Host / IP", "host", ""),
            ("Username", "user", ""),
            ("Port", "port", "22"),
            ("Identity file", "identity", ""),
            ("Extra options", "extra", ""),
        ]
        self.entries = {}
        for i, (label, key, default) in enumerate(fields, start=1):
            tk.Label(wrap, text=label, bg=BG, fg=SUBTEXT, font=f_label).grid(
                row=i, column=0, sticky="w", pady=7, padx=(0, 16))
            var = tk.StringVar(value=str(conn.get(key, default)))
            ent = RoundEntry(wrap, var, outer_bg=BG, font=f_entry)
            ent.configure(width=260)
            ent.grid(row=i, column=1, sticky="ew", pady=7)
            self.entries[key] = ent
            if key == "identity":
                RoundButton(wrap, "Browse", self._browse_key,
                            fill=SURFACE, fill_hi=SURFACE_HI, fg=TEXT,
                            font=f_label, outer_bg=BG, height=38, padx=12).grid(
                    row=i, column=2, padx=(10, 0))
            if i == 1:
                ent.entry.focus_set()

        self.err = tk.Label(wrap, text="", bg=BG, fg=RED, font=f_label)
        self.err.grid(row=len(fields) + 1, column=0, columnspan=3, sticky="w",
                      pady=(8, 0))

        btns = tk.Frame(wrap, bg=BG)
        btns.grid(row=len(fields) + 2, column=0, columnspan=3, pady=(16, 0),
                  sticky="e")
        RoundButton(btns, "Cancel", self.destroy, fill=SURFACE,
                    fill_hi=SURFACE_HI, fg=TEXT, font=f_btn, outer_bg=BG).pack(
            side="left", padx=(0, 10))
        RoundButton(btns, "Save", self._save, fill=ACCENT, fill_hi=ACCENT_HI,
                    fg=ON_ACCENT, font=f_btn, outer_bg=BG).pack(side="left")

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())
        self._center(parent)

    def _center(self, parent):
        self.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _browse_key(self):
        path = filedialog.askopenfilename(
            title="Choose SSH key", initialdir=os.path.expanduser("~/.ssh"))
        if path:
            self.entries["identity"].entry.delete(0, "end")
            self.entries["identity"].entry.insert(0, path)
            self.entries["identity"].entry.config(fg=TEXT)

    def _save(self):
        data = {k: e.get().strip() for k, e in self.entries.items()}
        if not data["host"]:
            self.err.config(text="Host is required.")
            return
        if not data["name"]:
            data["name"] = data["host"]
        self.result = data
        self.destroy()


# ---------------------------------------------------------------------------
# Confirm dialog
# ---------------------------------------------------------------------------
class ConfirmDialog(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.configure(bg=BG)
        self.title("")
        self.resizable(False, False)
        self.ok = False
        self.transient(parent)
        self.grab_set()

        f_title = tkfont.Font(family="Helvetica Neue", size=15, weight="bold")
        f_body = tkfont.Font(family="Helvetica Neue", size=12)
        f_btn = tkfont.Font(family="Helvetica Neue", size=12, weight="bold")

        wrap = tk.Frame(self, bg=BG, padx=28, pady=24)
        wrap.pack()
        tk.Label(wrap, text=title, bg=BG, fg=TEXT, font=f_title).pack(anchor="w")
        tk.Label(wrap, text=message, bg=BG, fg=SUBTEXT, font=f_body).pack(
            anchor="w", pady=(6, 20))
        btns = tk.Frame(wrap, bg=BG)
        btns.pack(anchor="e")
        RoundButton(btns, "Cancel", self.destroy, fill=SURFACE,
                    fill_hi=SURFACE_HI, fg=TEXT, font=f_btn, outer_bg=BG).pack(
            side="left", padx=(0, 10))
        RoundButton(btns, "Delete", self._confirm, fill=RED, fill_hi=RED_HI,
                    fg=ON_ACCENT, font=f_btn, outer_bg=BG).pack(side="left")

        self.bind("<Escape>", lambda e: self.destroy())
        self._center(parent)

    def _confirm(self):
        self.ok = True
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.configure(bg=BG)
        self.title("SSH Manager")
        self.geometry("540x640")
        self.minsize(460, 480)

        self.connections = load_connections()
        self.filtered = list(self.connections)
        self.selected = None
        self.cards = []

        self.fonts = {
            "h1": tkfont.Font(family="Helvetica Neue", size=24, weight="bold"),
            "sub": tkfont.Font(family="Helvetica Neue", size=8),
            "title": tkfont.Font(family="Helvetica Neue", size=14, weight="bold"),
            "cardsub": tkfont.Font(family="Menlo", size=11),
            "btn": tkfont.Font(family="Helvetica Neue", size=12, weight="bold"),
            "badge": tkfont.Font(family="Helvetica Neue", size=15, weight="bold"),
            "chev": tkfont.Font(family="Helvetica Neue", size=22),
        }

        self._build_header()
        self._build_list()
        self._build_footer()
        self.render()

        self.bind("<Return>", lambda e: self.connect())
        self.after(120, self._bring_to_front)

    # -- layout ------------------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self, bg=BG, padx=24, pady=18)
        header.pack(fill="x")
        row = tk.Frame(header, bg=BG)
        row.pack(fill="x")

        logo_path = resource_path("logo.png")
        try:
            self.logo_img = tk.PhotoImage(file=logo_path)
            tk.Label(row, image=self.logo_img, bg=BG).pack(side="left",
                                                           padx=(0, 14))
        except Exception:
            self.logo_img = None

        titlecol = tk.Frame(row, bg=BG)
        titlecol.pack(side="left")
        tk.Label(titlecol, text="SSH Manager", bg=BG, fg=TEXT,
                 font=self.fonts["h1"]).pack(anchor="w")

        subrow = tk.Frame(titlecol, bg=BG)
        subrow.pack(anchor="w", pady=(1, 0))
        tk.Label(subrow, text="by AI Developments", bg=BG, fg=SUBTEXT,
                 font=self.fonts["sub"]).pack(side="left")
        donate_font = tkfont.Font(family="Helvetica Neue", size=8,
                                  weight="bold", underline=True)
        donate = tk.Label(subrow, text="Donate", bg=BG, fg=ACCENT,
                          font=donate_font, cursor="pointinghand")
        donate.pack(side="left", padx=(8, 0))
        donate.bind("<Button-1>", lambda e: self._open_donate())
        donate.bind("<Enter>", lambda e: donate.config(fg=ACCENT_HI))
        donate.bind("<Leave>", lambda e: donate.config(fg=ACCENT))

        search_wrap = tk.Frame(self, bg=BG, padx=24)
        search_wrap.pack(fill="x", pady=(14, 6))
        self.search_var = tk.StringVar()
        self.search = RoundEntry(search_wrap, self.search_var, outer_bg=BG,
                                 font=self.fonts["sub"],
                                 placeholder="Search connections…")
        self.search.pack(fill="x")
        self.search.entry.bind("<KeyRelease>", lambda e: self._on_search())

    def _build_list(self):
        container = tk.Frame(self, bg=BG, padx=16)
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll = ThinScrollbar(container, self.canvas.yview, outer_bg=BG)
        scroll.pack(side="right", fill="y", padx=(4, 0))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.list_frame = tk.Frame(self.canvas, bg=BG)
        self.win = self.canvas.create_window((0, 0), window=self.list_frame,
                                             anchor="nw")
        self.list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.win, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _build_footer(self):
        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", padx=0)
        footer = tk.Frame(self, bg=BG, padx=24)
        footer.pack(fill="x", pady=(14, 0))
        RoundButton(footer, "Connect", self.connect, fill=ACCENT,
                    fill_hi=ACCENT_HI, fg=ON_ACCENT, font=self.fonts["btn"],
                    outer_bg=BG, padx=28).pack(side="left")
        RoundButton(footer, "Delete", self.delete, fill=SURFACE,
                    fill_hi=SURFACE_HI, fg=RED, font=self.fonts["btn"],
                    outer_bg=BG).pack(side="right")
        RoundButton(footer, "Edit", self.edit, fill=SURFACE,
                    fill_hi=SURFACE_HI, fg=TEXT, font=self.fonts["btn"],
                    outer_bg=BG).pack(side="right", padx=8)
        RoundButton(footer, "+ Add", self.add, fill=SURFACE,
                    fill_hi=SURFACE_HI, fg=TEXT, font=self.fonts["btn"],
                    outer_bg=BG).pack(side="right")

        link_font = tkfont.Font(family="Helvetica Neue", size=8, underline=True)
        hosts_link = tk.Label(self, text="edit /etc/hosts", bg=BG, fg=SUBTEXT,
                              font=link_font, cursor="pointinghand")
        hosts_link.pack(anchor="e", padx=24, pady=(4, 12))
        hosts_link.bind("<Button-1>", lambda e: self._edit_hosts())
        hosts_link.bind("<Enter>", lambda e: hosts_link.config(fg=TEXT))
        hosts_link.bind("<Leave>", lambda e: hosts_link.config(fg=SUBTEXT))

    # -- helpers -----------------------------------------------------------
    def _open_donate(self):
        subprocess.run(["open", DONATE_URL])

    def _edit_hosts(self):
        script = (
            'tell application "Terminal"\n'
            '    activate\n'
            '    do script "sudo nano /etc/hosts"\n'
            'end tell'
        )
        subprocess.run(["osascript", "-e", script])

    def _bring_to_front(self):
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()
        self.after(400, lambda: self.attributes("-topmost", False))

    def _on_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 3)), "units")

    def _on_search(self):
        q = self.search.get().strip().lower()
        if not q:
            self.filtered = list(self.connections)
        else:
            self.filtered = [
                c for c in self.connections
                if q in c.get("name", "").lower()
                or q in c.get("host", "").lower()
                or q in c.get("user", "").lower()
            ]
        self.selected = None
        self.render()

    # -- rendering ---------------------------------------------------------
    def render(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.cards = []
        if not self.filtered:
            msg = ("No connections yet.\nClick “+ Add” to create one."
                   if not self.connections else "No matches.")
            tk.Label(self.list_frame, text=msg, bg=BG, fg=SUBTEXT,
                     font=self.fonts["sub"], justify="center", pady=70).pack(
                expand=True)
            return
        for idx, conn in enumerate(self.filtered):
            card = Card(
                self.list_frame, conn, selected=(self.selected == idx),
                on_select=lambda i=idx: self._select(i),
                on_connect=lambda i=idx: self._connect_idx(i),
                fonts={"title": self.fonts["title"], "sub": self.fonts["cardsub"],
                       "badge": self.fonts["badge"], "chev": self.fonts["chev"]},
            )
            card.pack(fill="x", padx=4, pady=4)
            self.cards.append(card)

    def _select(self, idx):
        # Update selection state in place — rebuilding the list here would
        # destroy the card mid-double-click and swallow the connect event.
        self.selected = idx
        for i, card in enumerate(self.cards):
            card.set_selected(i == idx)

    def _connect_idx(self, idx):
        self.selected = idx
        self.connect()

    # -- actions -----------------------------------------------------------
    def _current(self):
        if self.selected is None or self.selected >= len(self.filtered):
            return None
        return self.filtered[self.selected]

    def connect(self):
        conn = self._current()
        if conn and conn.get("host", "").strip():
            open_in_terminal(conn)

    def add(self):
        dlg = ConnectionDialog(self, "Add connection")
        self.wait_window(dlg)
        if dlg.result:
            self.connections.append(dlg.result)
            save_connections(self.connections)
            self._on_search()

    def edit(self):
        conn = self._current()
        if not conn:
            return
        real_idx = self.connections.index(conn)
        dlg = ConnectionDialog(self, "Edit connection", conn)
        self.wait_window(dlg)
        if dlg.result:
            self.connections[real_idx] = dlg.result
            save_connections(self.connections)
            self._on_search()

    def delete(self):
        conn = self._current()
        if not conn:
            return
        name = conn.get("name", "this connection")
        dlg = ConfirmDialog(self, f"Delete “{name}”?", "This can't be undone.")
        self.wait_window(dlg)
        if dlg.ok:
            self.connections.remove(conn)
            save_connections(self.connections)
            self.selected = None
            self._on_search()


if __name__ == "__main__":
    App().mainloop()
