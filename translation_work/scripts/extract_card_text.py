#!/usr/bin/env python3
"""Extract the 186 Chance-card slots from the main PS2 executable.

The pointer table is at file offset 0x3185E0 in SLPM_621.12.
Strings are NUL terminated and encoded in Windows-31J/CP932.
The executable is read only. JSON records retain offsets and allocated byte
lengths needed for a future, conservative in-place reinsertion experiment.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


TABLE_START = 0x369470
TABLE_END = 0x36AA48
POINTER_TABLE = 0x3185E0
ADDRESS_DELTA = 0xFF000


def has_japanese(text: str) -> bool:
    return any("\u3040" <= c <= "\u30ff" or "\u3400" <= c <= "\u9fff" for c in text)


def extract(path: Path) -> list[dict[str, object]]:
    data = path.read_bytes()
    if len(data) < TABLE_END:
        raise ValueError("input is too short to contain the identified table")
    if data[:6] != b"\x7fELF\x01\x01":
        raise ValueError("expected ELF32 little-endian")
    records: list[dict[str, object]] = []
    for number in range(1, 187):
        location = POINTER_TABLE + (number - 1) * 4
        address = struct.unpack_from("<I", data, location)[0]
        start = address - ADDRESS_DELTA if address else None
        raw = b""
        if start is not None:
            if not 0 <= start < len(data):
                raise ValueError(f"invalid card {number} pointer")
            end = data.index(b"\0", start)
            raw = data[start:end]
        text = raw.decode("cp932") if start is not None else None
        records.append({
            "card_number": number,
            "texture": f"C{number:03d}.TI",
            "pointer_file_offset": location,
            "virtual_address": address,
            "file_offset": start,
            "file_offset_hex": f"0x{start:08X}" if start is not None else None,
            "byte_length": len(raw),
            "allocated_bytes_including_nul": len(raw) + 1 if start is not None else 0,
            "text_ja": text,
            "status": "null_pointer" if not address else "empty_string" if not raw else "decoded",
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    args = parser.parse_args()
    records = extract(args.executable)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
