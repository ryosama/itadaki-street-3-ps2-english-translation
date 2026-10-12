#!/usr/bin/env python3
"""Inspect and extract Itadaki Street 3 CARD/*.TI textures.

Uses only the Python standard library. Outputs are always created separately;
the source .TI file is opened read-only and is never modified.
"""

from __future__ import annotations

import argparse
import binascii
import json
import pathlib
import struct
import zlib


HEADER_SIZE = 0x30
CLUT_SIZE = 0x400
PIXEL_OFFSET = HEADER_SIZE + CLUT_SIZE
WIDTH = HEIGHT = 256


def clut_index_ps2(index: int) -> int:
    """Undo the standard 8-bit PS2 CSM1 CLUT 8/16-entry permutation."""
    return (index & 0xE7) | ((index & 0x08) << 1) | ((index & 0x10) >> 1)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF)


def write_rgba_png(path: pathlib.Path, width: int, height: int, rgba: bytes) -> None:
    if len(rgba) != width * height * 4:
        raise ValueError("invalid RGBA buffer size")
    rows = b"".join(b"\0" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
           + png_chunk(b"IDAT", zlib.compress(rows, 9)) + png_chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def parse_ti(path: pathlib.Path) -> tuple[bytes, list[tuple[int, int, int, int]], bytes]:
    data = path.read_bytes()
    if len(data) != 0x10430:
        raise ValueError(f"unexpected file size {len(data)} (expected 66608 / 0x10430)")
    header = data[:HEADER_SIZE]
    palette = [tuple(data[HEADER_SIZE + i * 4:HEADER_SIZE + i * 4 + 4]) for i in range(256)]
    pixels = data[PIXEL_OFFSET:]
    return header, palette, pixels


def decode_linear(palette: list[tuple[int, int, int, int]], pixels: bytes, ps2_clut: bool = True) -> bytes:
    out = bytearray()
    for value in pixels:
        r, g, b, a = palette[clut_index_ps2(value) if ps2_clut else value]
        # PS2 alpha is 0..0x80; scale it to PNG's 0..255 range.
        out.extend((r, g, b, min(255, a * 255 // 128)))
    return bytes(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("-o", "--output", type=pathlib.Path, help="output PNG path")
    parser.add_argument("--raw-clut", action="store_true", help="do not apply the usual PS2 CLUT permutation")
    parser.add_argument("--metadata", type=pathlib.Path, help="optional JSON metadata path")
    args = parser.parse_args()

    header, palette, pixels = parse_ti(args.input)
    rgba = decode_linear(palette, pixels, not args.raw_clut)
    output = args.output or pathlib.Path(args.input.stem + ".png")
    write_rgba_png(output, WIDTH, HEIGHT, rgba)

    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(json.dumps({
            "source": str(args.input), "file_size": args.input.stat().st_size,
            "header_hex": header.hex(), "palette_offset": HEADER_SIZE,
            "palette_entries": 256, "pixel_offset": PIXEL_OFFSET,
            "width": WIDTH, "height": HEIGHT, "bits_per_pixel": 8,
            "ps2_clut_permutation": not args.raw_clut,
        }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
