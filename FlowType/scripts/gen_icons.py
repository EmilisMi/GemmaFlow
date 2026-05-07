"""
Generate tray icon PNGs for FlowType.
Run from the project root: python scripts/gen_icons.py
"""

import os
import struct
import zlib

ICON_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets", "icons")


def make_png_circle(r, g, b, size=64):
    """Generate a minimal PNG with an anti-aliased circle."""
    def chunk(name, data):
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(c[4:]) & 0xFFFFFFFF)

    cx, cy = size / 2.0, size / 2.0
    radius = size / 2.0 - 2

    raw = b""
    for y in range(size):
        raw += b"\x00"  # filter byte
        for x in range(size):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist <= radius - 1:
                raw += bytes([r, g, b, 255])
            elif dist <= radius:
                alpha = int(255 * (radius - dist))
                raw += bytes([r, g, b, alpha])
            else:
                raw += bytes([0, 0, 0, 0])

    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # RGBA
    ihdr = chunk(b"IHDR", ihdr_data)
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return header + ihdr + idat + iend


def main():
    os.makedirs(ICON_DIR, exist_ok=True)

    icons = {
        "tray-idle.png":   (80,  80, 100),
        "tray-active.png": (230, 57,  70),
    }

    for filename, (r, g, b) in icons.items():
        path = os.path.join(ICON_DIR, filename)
        with open(path, "wb") as f:
            f.write(make_png_circle(r, g, b, size=32))
        print(f"  Created {path}")

    print("  Done.")


if __name__ == "__main__":
    main()
