"""Independent full-byte rollback and catalog verification for phase6 revision3.

Read-only verification of game sources; writes one new verification JSON under
translation_work. Does not import the translation builder or launch PCSX2.
"""
import hashlib
import json
import struct
from pathlib import Path
from message_format import tokenize
from build_test_patch import write_new_or_identical, encode_json

ROOT=Path('translation_work')
OUT=ROOT/'phase6/revision3'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def commands(text):
    return [t for t in tokenize(text) if t['kind']!='literal']

def main():
    original=Path('decompile/SLPM_621.12').read_bytes()
    base=(ROOT/'phase5/revision3/patched/SLPM_621.12').read_bytes()
    patched=(OUT/'patched/SLPM_621.12').read_bytes()
    manifest=read(OUT/'translation_manifest.json')
    catalog=read(OUT/'translation_catalog.json')
    assert sha(original)==manifest['source_sha256']=='d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5'
    assert sha(base)==manifest['base_sha256']=='7ca5c38cfb1c629a91abbe3a78e4d2f54fbad0bacd8c5e62ba702d3cfbb0501c'
    assert sha(patched)==manifest['patched_sha256']
    assert len(original)==len(base)==len(patched)==3923328
    restored=bytearray(patched)
    ranges=set()
    for patch in manifest['patches']:
        start=patch['offset']; end=start+patch['capacity']
        region=set(range(start,end))
        assert not ranges&region
        ranges.update(region)
        assert patched[start:end]==bytes.fromhex(patch['after_hex'])
        assert base[start:end]==bytes.fromhex(patch['before_hex'])
        assert original[start:end]==bytes.fromhex(patch['original_hex'])
        restored[start:end]=bytes.fromhex(patch['before_hex'])
    assert restored==base
    assert all(i in ranges for i,(a,b) in enumerate(zip(base,patched)) if a!=b)
    # Entire data/pointer tables, including shared pointers and type words.
    for start,end in ((0x3185E0,0x3188C8),(0x3188D8,0x3188D8+143*8)):
        assert patched[start:end]==original[start:end]
    for row in catalog:
        start=row['offset']
        if row['status'].startswith('integrated'):
            text=patched[start:patched.index(b'\0',start)].decode('cp932')
            assert text==row['encoded_text']
            assert row['required_bytes']<=row['capacity']
            if row['kind']=='card_detail':
                assert commands(row['japanese'])==commands(text)
                literal=''.join(t['text'] if t['kind']=='literal' else '{'+t['command']+'}' for t in tokenize(text))
                assert literal==row['english'], 'English formatter round-trip failed'
                assert text.count('%%')==row['japanese'].count('%%')
        else:
            assert patched[start:start+row['capacity']]==base[start:start+row['capacity']]
        if row['kind']=='card_detail':
            for table_id in row['detail_table_ids']:
                assert struct.unpack_from('<I',patched,0x3188DC+8*table_id)[0]==start+0xFF000
    # Restore all previous changes too: phase5 then phase4.
    menu=read(ROOT/'phase5/revision3/menu_patch_manifest.json')
    for p in menu['patches']:
        # inspect differing schemas explicitly, never infer capacity from text
        start=p['offset']
        raw=bytes.fromhex(p['original_hex'])
        restored[start:start+len(raw)]=raw
    font=menu['font_patch']
    start=font['offset']; raw=bytes.fromhex(font['original_hex'])
    restored[start:start+len(raw)]=raw
    phase4=read(ROOT/'phase4/patch_manifest.json')
    for p in phase4['patches']:
        start=p['file_offset']; raw=bytes.fromhex(p['original_hex'])
        restored[start:start+len(raw)]=raw
    assert restored==original, 'full rollback to Japanese original failed'
    iso_hashes={}
    for name in ('idataki3.iso','idataki3.original.iso'):
        h=hashlib.sha256()
        with Path(name).open('rb') as stream:
            for block in iter(lambda:stream.read(4*1024*1024),b''):
                h.update(block)
        iso_hashes[name]=h.hexdigest()
        assert h.hexdigest()=='6e8e471f9b6aef1af78b9cf99407ffd9adaa2c51a871f622dd84db140404dcab'
    result=dict(status='PASS',patched_sha256=sha(patched),iso_sha256=iso_hashes,
                stats=manifest['stats'],full_rollback_to_original=True,
                tables_unchanged=True,formatter_roundtrip=True,
                runtime_validation='not performed for this expanded batch')
    write_new_or_identical(OUT/'binary_verification.json',encode_json(result))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
