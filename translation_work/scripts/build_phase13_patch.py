"""Translate opponent profiles and surrounding menus, cumulatively over v12.

Run from project root; stdlib only. Never writes the original ELF/ISO/resources.
Strings retain their addresses. Validated zero padding up to the next 8-byte
alignment is usable, but not any neighbouring string or binary field.
Record every changed span for independent rollback and BPS verification.
"""
import json
import struct
from collections import Counter
from pathlib import Path
from build_test_patch import digest, EXPECTED_SHA, encode_json, write_new_or_identical
from build_phase9_patch import PRINTF, COLORS

ROOT = Path('translation_work')
PREV = ROOT/'phase12/revision1'
OUT = ROOT/'phase13/revision3'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    original = Path('decompile/SLPM_621.12').read_bytes()
    base = (PREV/'patched/SLPM_621.12').read_bytes()
    assert digest(original) == EXPECTED_SHA
    assert digest(base) == 'a388e2810de478dc3da6df6ba8fa9e30ae360dc89a72e1405b51573281275515'
    todos = {}
    for kind, filename in [('opponent','opponents_phase13_en.json'),('ui','ui_phase13_en.json')]:
        for off, en in read(ROOT/'translations'/filename).items():
            offset = int(off,16)
            assert offset not in todos
            todos[offset] = (kind,en)
    pointer_values = set(struct.unpack_from('<I',original,i)[0] for i in range(0x139594,len(original)-3,4))
    patched = bytearray(base); records = []; allowed = set()
    for off,(kind,en) in sorted(todos.items()):
        assert off >= 0x139594 and original[off-1] == 0
        end = original.index(b'\0',off)+1
        text = original[off:end-1].decode('cp932')
        assert text and all(c.isprintable() or c in '\n\u3000' for c in text)
        payload = en.encode('ascii')+b'\0'
        padded = (end+7)&~7
        if len(payload) > end-off:
            assert original[end:padded] == b'\0'*(padded-end), (hex(off),'nonzero padding')
            assert base[end:padded] == original[end:padded], (hex(off),'modified padding')
            assert not any(p+0xFF000 in pointer_values for p in range(end,padded)), (hex(off),'padding reference')
            end = padded
        assert len(payload) <= end-off, (hex(off),en,len(payload),end-off)
        assert PRINTF.findall(text) == PRINTF.findall(en), (hex(off),'printf')
        assert COLORS.findall(text) == COLORS.findall(en)
        assert en.endswith('\n') == text.endswith('\n')
        if off == 0x360988:
            assert len(en.split('\n')) <= 4 and max(map(len,en.split('\n'))) <= 14
        if kind == 'opponent':
            assert '\n' not in en and len(en) <= 17
        assert not allowed.intersection(range(off,end))
        allowed.update(range(off,end))
        after = payload.ljust(end-off,b'\0')
        patched[off:end] = after
        records.append(dict(kind=kind, offset=off, offset_hex=hex(off),capacity=end-off,
                            japanese=text, english=en, original_hex=original[off:end].hex(),
                            before_hex=base[off:end].hex(), after_hex=after.hex(),
                            consumed_alignment_padding=max(0,len(payload)-(len(text.encode('cp932'))+1))))
    assert patched[0x1000:0x139594] == base[0x1000:0x139594]
    assert patched[0x3182E8:0x318528] == original[0x3182E8:0x318528], 'profile pointers changed'
    # 20-pixel profile font, 350 pixels available before the portrait.
    # The header uses the name, two spaces and age; other rows have prefixes.
    profiles = []
    for index in range(12):
        fields = struct.unpack_from('<8I',patched,0x3182E8+index*32)
        texts = [bytes(patched[p-0xFF000:]).split(b'\0')[0].decode('ascii') for p in fields]
        rows = [texts[0]+'  '+texts[1], texts[2], 'Home:'+texts[3], 'Job:'+texts[4], 'Like:'+texts[5]]
        assert max(map(len,rows)) <= 17, (index,rows)
        profiles.append(dict(index=index, rows=rows, rank=texts[6], short_name=texts[7]))
    assert len(patched) == len(original)
    assert all(i in allowed for i,(a,b) in enumerate(zip(base,patched)) if a!=b)
    prior = read(PREV/'phase12_manifest.json')
    for r in prior['resources']:
        raw = (PREV/'patched'/r['relative_iso_path']).read_bytes()
        assert digest(raw) == r['patched_sha256']
        write_new_or_identical(OUT/'patched'/r['relative_iso_path'],raw)
    manifest = dict(source_sha256=EXPECTED_SHA,base_sha256=digest(base),patched_sha256=digest(patched),
                    patches=records,resources=prior['resources'],counts=dict(Counter(r['kind'] for r in records)),
                    code_changes=0,previous_version='phase12/revision1',
                    profile_pointer_table_unchanged=True, title_and_maps_preserved=True,
                    runtime_test='pending', screenshots_reviewed=14)
    write_new_or_identical(OUT/'patched/SLPM_621.12',bytes(patched))
    write_new_or_identical(OUT/'phase13_manifest.json',encode_json(manifest))
    write_new_or_identical(OUT/'profile_layout_checks.json',encode_json(profiles))
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('patches','resources')},indent=2))

if __name__ == '__main__':
    main()
