"""Independent byte-diff/rollback verification for the final phase-5 test copy."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'translation_work/phase5/revision3'
original = (ROOT / 'decompile/SLPM_621.12').read_bytes()
base = (ROOT / 'translation_work/phase4/patched/SLPM_621.12').read_bytes()
patched = (OUT / 'patched/SLPM_621.12').read_bytes()
manifest = json.loads((OUT / 'menu_patch_manifest.json').read_text(encoding='utf-8'))
assert hashlib.sha256(original).hexdigest() == manifest['source_sha256']
assert hashlib.sha256(base).hexdigest() == manifest['base_sha256']
assert hashlib.sha256(patched).hexdigest() == manifest['patched_sha256']
assert len(patched) == len(original) == len(base) == manifest['size']
restored = bytearray(patched)
allowed = set()
for record in manifest['patches'] + [manifest['font_patch']]:
    off = record['offset']
    before, after = bytes.fromhex(record['original_hex']), bytes.fromhex(record['patched_hex'])
    assert original[off:off+len(before)] == base[off:off+len(before)] == before
    assert patched[off:off+len(after)] == after
    allowed.update(range(off, off+len(before)))
    restored[off:off+len(before)] = before
    if 'english' in record:
        text = patched[off:patched.index(b'\0',off)].decode('ascii')
        assert text == record['english']
        assert record['english'].count('\n') == record['japanese'].count('\n') or record['kind'] in ('main_description','prompt')
        for ref in record['pointer_offsets']:
            assert patched[ref:ref+4] == original[ref:ref+4]
changed = [i for i, (a,b) in enumerate(zip(base,patched)) if a != b]
assert changed == manifest['changed_offsets_relative_to_phase4']
assert all(i in allowed for i in changed)
assert bytes(restored) == base
phase4 = json.loads((ROOT / 'translation_work/phase4/patch_manifest.json').read_text(encoding='utf-8'))
for record in phase4['patches']:
    off = record['file_offset']
    raw = bytes.fromhex(record['patched_hex'])
    assert patched[off:off+len(raw)] == raw
    restored[off:off+len(raw)] = bytes.fromhex(record['original_hex'])
assert bytes(restored) == original
result = dict(menu_strings_verified=len(manifest['patches']),
              changed_bytes_relative_to_phase4=len(changed),
              full_original_reconstruction_verified=True, phase4_patches_preserved=True,
              only_code_change='0x1C01C8: menu font selector 20 -> 16',
              original_source_unchanged=True)
rev2 = json.loads((ROOT / 'translation_work/phase5/revision2/menu_patch_manifest.json').read_text(encoding='utf-8'))
rev2_by_offset = {r['offset']:r for r in rev2['patches']}
changes_since_observed_revision = [r['offset_hex'] for r in manifest['patches']
                                   if r['patched_hex'] != rev2_by_offset[r['offset']]['patched_hex']]
assert len(changes_since_observed_revision) == 3
assert all(r['patched_hex'] == rev2_by_offset[r['offset']]['patched_hex']
           for r in manifest['patches'] if r['kind'] in ('main_label','main_description','player_label'))
assert manifest['font_patch'] == rev2['font_patch']
result['changed_strings_since_visually_observed_revision2'] = changes_since_observed_revision
result['observed_main_menu_and_player_labels_identical_to_revision2'] = True
setup = json.loads((ROOT / 'translation_work/phase4/pcsx2_setup_manifest.json').read_text(encoding='utf-8'))
for entry in setup['copies']:
    assert hashlib.sha256(Path(entry['source']).read_bytes()).hexdigest() == entry['source_sha256']
result['original_bios_and_memory_cards_unchanged'] = True
for name in ('idataki3.original.iso','idataki3.iso'):
    with (ROOT/name).open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest() == '6e8e471f9b6aef1af78b9cf99407ffd9adaa2c51a871f622dd84db140404dcab'
result['original_isos_unchanged'] = True
(OUT / 'binary_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
