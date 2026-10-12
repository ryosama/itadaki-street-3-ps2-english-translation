"""Independent phase7 binary verification, including rollback to original ELF.

Read-only sources, stdlib only. Writes a new verification artifact under phase7.
Does not import the builder or launch the emulator.
"""
import hashlib
import json
import re
import struct
from pathlib import Path
from build_test_patch import encode_json, write_new_or_identical

ROOT=Path('translation_work')
OUT=ROOT/'phase7/revision3'

def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    original=Path('decompile/SLPM_621.12').read_bytes()
    base=(ROOT/'phase6/revision3/patched/SLPM_621.12').read_bytes()
    patched=(OUT/'patched/SLPM_621.12').read_bytes()
    manifest=read(OUT/'rules_patch_manifest.json')
    assert sha(original)==manifest['source_sha256']=='d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5'
    assert sha(base)==manifest['base_sha256']=='caf7931bcf43c87de8c2363dedd05fff0cbe7fbe720bbdcb80af658d0f687889'
    assert sha(patched)==manifest['patched_sha256']
    assert len(original)==len(base)==len(patched)==3923328
    restored=bytearray(patched); ranges=set(); rules=[]
    printf=re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs])')
    for r in manifest['patches']:
        start=r['offset']; end=start+r['capacity']
        region=set(range(start,end)); assert not region&ranges; ranges.update(region)
        assert patched[start:end]==bytes.fromhex(r['after_hex'])
        assert base[start:end]==bytes.fromhex(r['before_hex'])==bytes.fromhex(r['original_hex'])
        assert original[start:end]==bytes.fromhex(r['original_hex'])
        text=patched[start:patched.index(b'\0',start)].decode('ascii')
        assert text==r['english'] and len(text)+1<=r['capacity']
        assert printf.findall(r['japanese'])==printf.findall(text)
        for ref in r['pointer_offsets']:
            assert patched[ref:ref+4]==original[ref:ref+4]==struct.pack('<I',start+0xFF000)
        if r['kind']=='rules':
            rules.append(start)
            assert len(text.split('\n'))<=3 and max(map(len,text.split('\n')))<=14
        restored[start:end]=bytes.fromhex(r['before_hex'])
    assert restored==base
    assert all(i in ranges for i,(a,b) in enumerate(zip(base,patched)) if a!=b)
    assert patched[0x1000:0x139594]==base[0x1000:0x139594]
    assert len(rules)==62
    assert [struct.unpack_from('<I',patched,0x319230+4*i)[0]-0xFF000 for i in range(62)]==rules
    # Roll back phase6, then phase5 strings/font, then phase4 initial examples.
    for p in read(ROOT/'phase6/revision3/translation_manifest.json')['patches']:
        raw=bytes.fromhex(p['before_hex']); start=p['offset']; restored[start:start+len(raw)]=raw
    previous=read(ROOT/'phase5/revision3/menu_patch_manifest.json')
    for p in previous['patches']+[previous['font_patch']]:
        raw=bytes.fromhex(p['original_hex']); start=p['offset']; restored[start:start+len(raw)]=raw
    for p in read(ROOT/'phase4/patch_manifest.json')['patches']:
        raw=bytes.fromhex(p['original_hex']); start=p['file_offset']; restored[start:start+len(raw)]=raw
    assert restored==original, 'full rollback failed'
    result=dict(status='PASS',counts=manifest['counts'],patched_sha256=sha(patched),
                full_rollback_to_original=True,rules_table_unchanged=True,
                code_unchanged_from_base=True,printf_signatures_preserved=True,
                visual_validation='separate emulator test required')
    write_new_or_identical(OUT/'binary_verification.json',encode_json(result))
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
