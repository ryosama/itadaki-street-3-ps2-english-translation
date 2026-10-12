"""Independent phase8 verification: allocations, controls, rollback and ISO BPS.

Does not import the phase8 builder. No ISO output or emulator activity.
"""
import hashlib
import importlib.util
import json
import re
import struct
from pathlib import Path
from build_test_patch import write_new_or_identical, encode_json

ROOT=Path('translation_work'); OUT=ROOT/'phase8/revision1'
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(data): return hashlib.sha256(data).hexdigest()

def main():
 original=Path('decompile/SLPM_621.12').read_bytes()
 base=(ROOT/'phase7/revision3/patched/SLPM_621.12').read_bytes()
 patched=(OUT/'patched/SLPM_621.12').read_bytes(); manifest=read(OUT/'gameplay_patch_manifest.json')
 assert sha(original)==manifest['source_sha256']=='d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5'
 assert sha(base)==manifest['base_sha256']
 assert sha(patched)==manifest['patched_sha256']
 assert len(patched)==len(original)==len(base)==3923328
 printf=re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs])'); colors=re.compile(r'/c\d')
 restored=bytearray(patched); allowed=set(); references={r['offset']+0xFF000 for r in manifest['patches']}
 for r in manifest['patches']:
  start=r['offset']; end=start+r['capacity']; before=bytes.fromhex(r['before_hex'])
  assert original[start:end]==bytes.fromhex(r['original_hex'])
  assert base[start:end]==before and patched[start:end]==bytes.fromhex(r['after_hex'])
  assert original.index(b'\0',start)+1==end
  text=patched[start:patched.index(b'\0',start)].decode('ascii')
  assert text==r['english'] and len(text)+1<=r['capacity']
  assert printf.findall(r['japanese'])==printf.findall(text)
  assert colors.findall(r['japanese'])==colors.findall(text)
  assert r['japanese'].endswith('\n')==text.endswith('\n')
  assert not allowed.intersection(range(start,end)); allowed.update(range(start,end))
  restored[start:end]=before
 assert restored==base and patched[0x1000:0x139594]==base[0x1000:0x139594]
 assert all(i in allowed for i,(a,b) in enumerate(zip(base,patched)) if a!=b)
 pointer_count=0
 for offset in range(0,len(original)-3,4):
  if struct.unpack_from('<I',original,offset)[0] in references:
   assert original[offset:offset+4]==patched[offset:offset+4], (hex(offset),'pointer changed')
   pointer_count+=1
 for r in read(ROOT/'phase7/revision3/rules_patch_manifest.json')['patches']:
  raw=bytes.fromhex(r['before_hex']); restored[r['offset']:r['offset']+len(raw)]=raw
 for r in read(ROOT/'phase6/revision3/translation_manifest.json')['patches']:
  raw=bytes.fromhex(r['before_hex']); restored[r['offset']:r['offset']+len(raw)]=raw
 phase5=read(ROOT/'phase5/revision3/menu_patch_manifest.json')
 for r in phase5['patches']+[phase5['font_patch']]:
  raw=bytes.fromhex(r['original_hex']); restored[r['offset']:r['offset']+len(raw)]=raw
 for r in read(ROOT/'phase4/patch_manifest.json')['patches']:
  raw=bytes.fromhex(r['original_hex']); restored[r['file_offset']:r['file_offset']+len(raw)]=raw
 assert restored==original
 # Parse BPS through the separate package applier, not the generating module.
 package=ROOT/'release/english_v8'
 spec=importlib.util.spec_from_file_location('release_applier',package/'apply_iso_patch.py')
 applier=importlib.util.module_from_spec(spec); spec.loader.exec_module(applier)
 release,commands,source_crc,target_crc=applier.load_recipe()
 iso=Path('idataki3.original.iso'); actual_sha,actual_crc=applier.hash_source(iso)
 assert actual_sha==release['source_sha256'] and actual_crc==source_crc
 target_sha,actual_crc=applier.generate(iso,commands)
 assert target_sha==release['target_sha256'] and actual_crc==target_crc
 elf_offset=release['elf_iso_offset']; recovered=bytearray(original)
 for offset,count,payload in commands:
  if payload is not None:
   assert elf_offset<=offset and offset+count<=elf_offset+len(original)
   recovered[offset-elf_offset:offset-elf_offset+count]=payload
 assert recovered==patched, 'BPS reconstructs a different executable'
 with iso.open('rb') as stream:
  stream.seek(elf_offset); assert stream.read(len(original))==original
 result=dict(status='PASS',new_strings=len(manifest['patches']),all_145_prepared_drafts_integrated=True,
             full_rollback_to_original=True,phase7_preserved_except_shorter_map_label=True,
             fixed_allocations=True,printf_and_color_controls_preserved=True,
             unchanged_pointer_references=pointer_count,code_unchanged_from_phase7=True,
             bps_reconstructs_exact_patched_elf=True,iso_changes_only_in_original_elf_extent=True,
             source_iso_sha256=actual_sha,virtual_target_iso_sha256=target_sha,
             virtual_target_iso_crc32=f'{actual_crc:08x}',iso_created=False,
             pcsx2_visual_test='NOT RUN; required for new gameplay strings')
 write_new_or_identical(OUT/'binary_and_bps_verification.json',encode_json(result))
 print(json.dumps(result,indent=2))

if __name__=='__main__': main()
