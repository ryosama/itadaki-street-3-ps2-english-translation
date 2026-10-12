"""Cross-check independent Python and PowerShell/C# extraction results.

Run from the project root after analyze_card_references.ps1 and
extract_card_text.py. No source resources are written.
"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
cards = json.loads((root / "extracted/card_text_ja.json").read_text(encoding="utf-8-sig"))
reference = json.loads((root / "extracted/phase2/card_mapping.json").read_text(encoding="utf-8-sig"))
assert len(cards) == len(reference) == 186
for first, second in zip(cards, reference):
    for field in ("card_number", "pointer_file_offset", "virtual_address", "file_offset", "byte_length", "text_ja", "status"):
        assert first[field] == second[field], (first["card_number"], field)
assert cards[39]["file_offset"] == 0x3B9E08
assert cards[45]["status"] == "null_pointer"
assert len({c["virtual_address"] for c in cards if c["virtual_address"]}) == 181
for a, b in ((19, 90), (132, 149), (169, 170), (183, 184)):
    assert cards[a - 1]["virtual_address"] == cards[b - 1]["virtual_address"]
print("OK: 186 slots agree across independent extractors; 181 unique nonzero pointers.")
