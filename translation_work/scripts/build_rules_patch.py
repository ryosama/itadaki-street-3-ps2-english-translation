"""Translate Rules and selected submenus in a new phase7 ELF copy.

Stdlib only. Strict hashes, fixed original allocations, ASCII English, preserved
printf signatures and all pointers. No original edits, no relocation, no code
patches, no ISO rebuilding. Every replacement carries exact rollback bytes.
Run from the project root. Outputs are created only if new or identical.
"""
import csv
import io
import json
import re
import struct
from collections import Counter
from pathlib import Path
from build_test_patch import EXPECTED_SHA, digest, encode_json, write_new_or_identical

ROOT=Path('translation_work')
OUT=ROOT/'phase7/revision3'
BASE=ROOT/'phase6/revision3/patched/SLPM_621.12'
BASE_SHA='caf7931bcf43c87de8c2363dedd05fff0cbe7fbe720bbdcb80af658d0f687889'
PRINTF=re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs])')

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    source=Path('decompile/SLPM_621.12')
    original=source.read_bytes(); base=BASE.read_bytes()
    assert digest(original)==EXPECTED_SHA
    assert digest(base)==BASE_SHA
    assert len(base)==len(original)==3923328
    rules=read(ROOT/'translations/rules_en.json')
    discovered=read(ROOT/'extracted/phase7/rules_discovery.json')['records']
    assert len(rules)==62 and {int(x,16) for x in rules}=={r['offset'] for r in discovered}
    assert [struct.unpack_from('<I',original,0x319230+4*i)[0] for i in range(62)]==[r['va'] for r in discovered]
    assert [r['offset'] for r in discovered]==sorted(r['offset'] for r in discovered)
    patched=bytearray(base); rows=[]; allowed=set()
    groups=[('rules',rules),('submenu',read(ROOT/'translations/submenus_en.json'))]
    references={int(k,16)+0xFF000:[] for _,translations in groups for k in translations}
    for off in range(0,len(original)-3,4):
        value=struct.unpack_from('<I',original,off)[0]
        if value in references: references[value].append(off)
    for kind,translations in groups:
        for key,english in translations.items():
            start=int(key,16); end=original.index(b'\0',start)+1
            before=original[start:end]
            assert base[start:end]==before, f'overlap with earlier translation at {key}'
            japanese=before[:-1].decode('cp932')
            assert japanese and all(c.isprintable() or c=='\n' for c in japanese)
            payload=english.encode('ascii')+b'\0'
            assert len(payload)<=len(before), (key,len(payload),len(before))
            assert '/' not in english, 'renderer slash controls are not literal English'
            assert PRINTF.findall(japanese)==PRINTF.findall(english), f'printf mismatch at {key}'
            widths=[len(x) for x in english.split('\n')]
            if kind=='rules':
                assert len(widths)<=3 and max(widths)<=14, (key,widths)
            else:
                assert len(widths)<=5 and max(widths)<=18, (key,widths)
            if start in (0x35FF00,0x35FF20,0x35FF48,0x35FF68,0x35FF80,0x35FFB0,
                         0x35FFD0,0x35FFF0,0x360128,0x360148,0x360168,0x360190,
                         0x361AD0,0x361B00):
                assert '\n' not in english, 'single-line selector banner'
            # Multi-option resources: preserve number of choices, not just bytes.
            if start in (0x35FE78,0x360100,0x360118,0x3601B8,0x360240,
                         0x360290,0x3602B8,0x360388,0x3603B8):
                assert english.count('\n')==japanese.count('\n')
            region=set(range(start,end))
            assert not allowed&region
            allowed.update(region)
            after=payload.ljust(len(before),b'\0')
            patched[start:end]=after
            refs=references[start+0xFF000]
            rows.append(dict(kind=kind,offset=start,offset_hex=key,virtual_address=start+0xFF000,
                             japanese=japanese,english=english,capacity=len(before),
                             required_bytes=len(payload),line_characters=widths,pointer_offsets=refs,
                             original_hex=before.hex(),before_hex=base[start:end].hex(),after_hex=after.hex(),
                             review='binary verified; visual testing incomplete'))
    changed=[i for i,(a,b) in enumerate(zip(base,patched)) if a!=b]
    assert changed and all(i in allowed for i in changed)
    assert patched[0x1000:0x139594]==base[0x1000:0x139594], 'unexpected code change'
    assert patched[0x319230:0x319328]==original[0x319230:0x319328]
    restored=bytearray(patched)
    for row in rows:
        raw=bytes.fromhex(row['before_hex']); start=row['offset']
        restored[start:start+len(raw)]=raw
    assert restored==base
    assert source.read_bytes()==original and BASE.read_bytes()==base
    counts=dict(Counter(r['kind'] for r in rows))
    manifest=dict(source_sha256=digest(original),base=str(BASE),base_sha256=digest(base),
                  patched_sha256=digest(patched),file_size=len(patched),counts=counts,
                  changed_bytes=len(changed),patches=rows)
    write_new_or_identical(OUT/'patched/SLPM_621.12',bytes(patched))
    write_new_or_identical(OUT/'rules_patch_manifest.json',encode_json(manifest))
    stream=io.StringIO(newline='')
    fields=['kind','offset_hex','japanese','english','capacity','required_bytes','line_characters','review']
    writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
    for row in rows: writer.writerow({f:row[f] for f in fields})
    write_new_or_identical(OUT/'rules_translation.csv',stream.getvalue().encode('utf-8-sig'))
    print(json.dumps(dict(counts=counts,sha256=digest(patched),changed_bytes=len(changed)),indent=2))

if __name__=='__main__': main()
