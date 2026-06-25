#!/usr/bin/env python3
"""Render the SSH Manager app icon (Proton-inspired) as a 1024px master PNG."""

import os

from PIL import Image, ImageDraw

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "icon_master.png")

S = 1024
SS = 4  # supersample factor for crisp anti-aliasing
W = S * SS

# Proton-style purple gradient
TOP = (138, 110, 255)     # #8A6EFF
BOTTOM = (88, 52, 224)    # #5834E0
WHITE = (255, 255, 255, 255)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make():
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))

    # Vertical gradient layer
    grad = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gpx = grad.load()
    for y in range(W):
        c = lerp(TOP, BOTTOM, y / W) + (255,)
        for x in range(W):
            gpx[x, y] = c

    # Squircle mask (macOS Big Sur proportions)
    margin = int(W * 0.10)
    radius = int((W - 2 * margin) * 0.225)
    mask = Image.new("L", (W, W), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle(
        [margin, margin, W - margin, W - margin], radius=radius, fill=255
    )
    img.paste(grad, (0, 0), mask)

    # Subtle top highlight for depth
    hi = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hd.rounded_rectangle(
        [margin, margin, W - margin, int(W * 0.5)],
        radius=radius, fill=(255, 255, 255, 26),
    )
    himask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(himask).rounded_rectangle(
        [margin, margin, W - margin, W - margin], radius=radius, fill=255
    )
    img = Image.alpha_composite(img, Image.composite(
        hi, Image.new("RGBA", (W, W), (0, 0, 0, 0)), himask))

    d = ImageDraw.Draw(img)
    cx, cy = W // 2, W // 2

    # --- Terminal prompt glyph ">_" -------------------------------------
    stroke = int(W * 0.052)
    # Chevron ">"
    chev_h = int(W * 0.26)
    chev_w = int(W * 0.17)
    chev_left = cx - int(W * 0.20)
    top = (chev_left, cy - chev_h // 2)
    tip = (chev_left + chev_w, cy)
    bot = (chev_left, cy + chev_h // 2)
    d.line([top, tip], fill=WHITE, width=stroke, joint="curve")
    d.line([tip, bot], fill=WHITE, width=stroke, joint="curve")
    for p in (top, tip, bot):  # round the caps
        r = stroke // 2
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=WHITE)

    # Underscore "_"
    u_w = int(W * 0.20)
    u_left = cx + int(W * 0.02)
    u_y = cy + chev_h // 2
    d.rounded_rectangle(
        [u_left, u_y - stroke // 2, u_left + u_w, u_y + stroke // 2],
        radius=stroke // 2, fill=WHITE,
    )

    img = img.resize((S, S), Image.LANCZOS)
    img.save(OUT_PATH)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    make()
