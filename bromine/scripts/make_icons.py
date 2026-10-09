#!/usr/bin/env python3
"""Bromine icon tool.

  make_icons.py preview OUTDIR          write preview PNGs
  make_icons.py apply DIR [--dry-run]   overwrite launcher icons found under DIR

`apply` looks for app_icon*.png / ic_launcher*.png inside mipmap-*/drawable-* folders and
re-renders each one at its existing pixel size, so no resource names have to be hard-coded.
Run it on the repo root, and again on the Chromium source tree after patching.
"""
import argparse
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

BG_TOP, BG_BOTTOM = (58, 22, 16), (28, 12, 10)
DROP_TOP, DROP_BOTTOM = (255, 154, 92), (214, 58, 28)
SS = 4  # supersampling factor

NAME_RE = re.compile(r"^(app_icon|ic_launcher)(?P<kind>_round|_foreground|_background|_monochrome)?\.png$")
DIR_RE = re.compile(r"^(mipmap|drawable)(-.+)?$")
SKIP_DIRS = {".git", "third_party", "out", "node_modules"}


def vgradient(w, h, top, bottom):
    col = Image.new("RGB", (1, h))
    px = col.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return col.resize((w, h))


def drop_points(cx, cy, height, n=360):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = math.sin(t) * math.sin(t / 2)
        y = -math.cos(t)
        pts.append((cx + x * height / 2, cy + y * height / 2))
    return pts


def render(size, shape="rounded", layer="full"):
    """shape: rounded | circle | bleed.  layer: full | foreground | background | monochrome."""
    S = size * SS
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    if layer in ("full", "background"):
        bg = vgradient(S, S, BG_TOP, BG_BOTTOM).convert("RGBA")
        mask = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(mask)
        if layer == "background" or shape == "bleed":
            d.rectangle([0, 0, S, S], fill=255)
        elif shape == "circle":
            d.ellipse([0, 0, S - 1, S - 1], fill=255)
        else:
            d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=255)
        out.paste(bg, (0, 0), mask)

    if layer in ("full", "foreground", "monochrome"):
        dh = S * (0.56 if layer == "full" else 0.46)  # adaptive layers keep to the safe zone
        cx, cy = S / 2, S / 2 + dh * 0.04
        pts = drop_points(cx, cy, dh)
        dmask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(dmask).polygon(pts, fill=255)

        if layer == "monochrome":
            out.paste(Image.new("RGBA", (S, S), (255, 255, 255, 255)), (0, 0), dmask)
        else:
            grad = vgradient(S, S, DROP_TOP, DROP_BOTTOM).convert("RGBA")
            out.paste(grad, (0, 0), dmask)
            glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            hx, hy = cx - dh * 0.17, cy + dh * 0.12
            ImageDraw.Draw(glow).ellipse(
                [hx - dh * 0.05, hy - dh * 0.12, hx + dh * 0.05, hy + dh * 0.12],
                fill=(255, 255, 255, 120),
            )
            glow = glow.filter(ImageFilter.GaussianBlur(S * 0.004))
            out = Image.alpha_composite(out, glow)

    return out.resize((size, size), Image.LANCZOS)


def kind_to_args(kind):
    return {
        None: ("rounded", "full"),
        "_round": ("circle", "full"),
        "_foreground": ("bleed", "foreground"),
        "_background": ("bleed", "background"),
        "_monochrome": ("bleed", "monochrome"),
    }[kind]


def cmd_preview(outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    render(512).save(outdir / "icon_512.png")
    render(512, "circle").save(outdir / "icon_512_round.png")
    print(f"wrote previews to {outdir}")


def cmd_apply(root, dry):
    root = Path(root)
    n = 0
    for p in sorted(root.rglob("*.png")):
        rel_parts = p.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts[:-1]):
            continue
        m = NAME_RE.match(p.name)
        if not m or not DIR_RE.match(p.parent.name):
            continue
        try:
            with Image.open(p) as im:
                w, h = im.size
        except Exception as e:  # unreadable file
            print(f"skip {p}: {e}", file=sys.stderr)
            continue
        if w != h or w < 36:
            continue
        shape, layer = kind_to_args(m.group("kind"))
        n += 1
        if dry:
            print(f"would replace icon: {p.relative_to(root)} ({w}px, {layer})")
        else:
            render(w, shape, layer).save(p)
            print(f"replaced icon: {p.relative_to(root)} ({w}px, {layer})")
    print(f"launcher icons {'that would be ' if dry else ''}replaced: {n}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("preview")
    sp.add_argument("outdir")
    sa = sub.add_parser("apply")
    sa.add_argument("dir")
    sa.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.cmd == "preview":
        cmd_preview(a.outdir)
    else:
        cmd_apply(a.dir, a.dry_run)


if __name__ == "__main__":
    main()
