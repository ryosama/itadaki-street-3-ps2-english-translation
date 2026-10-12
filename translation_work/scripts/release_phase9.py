"""Package v9 BPS including ELF AND district MAP resources; verify virtually.

Original ISO and resources read only, no ISO rebuilding/writing. Uses ISO9660
directory records, not searches/replacement of arbitrary ISO byte patterns.
Reuses the v8 BPS codec and independent package applier without changing v8.
"""
import importlib.util
import json
import struct
import zlib
from pathlib import Path
from build_test_patch import digest,encode_json,write_new_or_identical
from build_iso_bps import locate_elf,directory_record,differences,checksums,number,ISO_SHA,SECTOR

ROOT=Path('translation_work'); BUILD=ROOT/'phase9/revision1'; OUT=ROOT/'release/english_v9'

def directory(stream,record):
 stream.seek(record['extent']*SECTOR); data=stream.read(record['size']); pos=0; result=[]
 while pos<len(data):
  size=data[pos]
  if not size: pos=(pos//SECTOR+1)*SECTOR; continue
  assert pos+size<=len(data)
  row=directory_record(data[pos:pos+size]); result.append(row); pos+=size
 return result

def main(build=BUILD,out=OUT,manifest_name='phase9_manifest.json',base_path=ROOT/'phase8/revision1/patched/SLPM_621.12'):
 BUILD=build; OUT=out; version=OUT.name.removeprefix('english_')
 manifest=json.loads((BUILD/manifest_name).read_text(encoding='utf-8'))
 original=Path('decompile/SLPM_621.12').read_bytes()
 base=base_path.read_bytes()
 elf=(BUILD/'patched/SLPM_621.12').read_bytes()
 assert digest(original)==manifest['source_sha256'] and digest(elf)==manifest['patched_sha256']
 assert digest(base)==manifest['base_sha256']
 # Independently verify ELF translations and rollback to v8.
 restored=bytearray(elf); allowed=set()
 for r in manifest['patches']:
  offset=r['offset']; stop=offset+r['capacity']
  assert original[offset:stop]==bytes.fromhex(r['original_hex'])
  assert base[offset:stop]==bytes.fromhex(r['before_hex'])
  assert elf[offset:stop]==bytes.fromhex(r['after_hex'])
  assert not allowed.intersection(range(offset,stop)); allowed.update(range(offset,stop))
  restored[offset:stop]=bytes.fromhex(r['before_hex'])
 assert restored==base and elf[0x1000:0x139594]==base[0x1000:0x139594]
 assert all(i in allowed for i,(a,b) in enumerate(zip(base,elf)) if a!=b)
 source=Path('idataki3.original.iso'); total=source.stat().st_size; assert total==575420416
 files=[]; changes=[]; checks=[]
 with source.open('rb') as stream:
  elf_record,root=locate_elf(stream)
  resource_dirs={}
  todo=[('SLPM_621.12',elf_record,original,elf,None)]
  for r in manifest['resources']:
   before=Path(r['source']).read_bytes(); after=(BUILD/'patched'/r['relative_iso_path']).read_bytes()
   assert digest(before)==r['source_sha256'] and digest(after)==r['patched_sha256']
   parts=r['relative_iso_path'].split('/'); assert len(parts)==2
   folder,filename=parts
   if folder not in resource_dirs:
    folder_record=next(x for x in root if x['name'].split(';')[0]==folder)
    assert folder_record['flags']&2
    resource_dirs[folder]=directory(stream,folder_record)
   record=next(x for x in resource_dirs[folder] if x['name'].split(';')[0]==filename)
   todo.append((r['relative_iso_path'],record,before,after,r))
  for name,record,before,after,resource in todo:
   assert not record['flags']&0x82 and record['size']==len(before)==len(after)
   start=record['extent']*SECTOR; stream.seek(start); assert stream.read(record['size'])==before
   if resource:
    rolled=bytearray(after); bounds=set()
    for r in resource['records']:
     off=r['offset']; cap=r['capacity']; old=bytes.fromhex(r['original_hex'])
     assert after[off:off+cap]==bytes.fromhex(r['after_hex']) and before[off:off+cap]==old
     assert not bounds.intersection(range(off,off+cap)); bounds.update(range(off,off+cap))
     rolled[off:off+cap]=old
    assert rolled==before
    assert all(i in bounds for i,(a,b) in enumerate(zip(before,after)) if a!=b)
   changes.extend(differences(before,after,start))
   files.append(dict(path=name,iso_offset=start,size=len(after),original_sha256=digest(before),patched_sha256=digest(after)))
   checks.append(dict(file=name,original_iso_content_matches=True,fixed_size=True,rollback=True))
  changes.sort(); assert all(changes[i][0]+len(changes[i][1])<=changes[i+1][0] for i in range(len(changes)-1))
  source_sha,target_sha,source_crc,target_crc=checksums(stream,changes,total)
 assert source_sha==ISO_SHA
 patch=bytearray(b'BPS1'+number(total)+number(total)+number(0)); cursor=0
 for pos,data in changes:
  if pos>cursor: patch+=number((pos-cursor-1)<<2)
  patch+=number(((len(data)-1)<<2)|1)+data; cursor=pos+len(data)
 if cursor<total: patch+=number((total-cursor-1)<<2)
 patch+=struct.pack('<II',source_crc,target_crc); patch+=struct.pack('<I',zlib.crc32(patch))
 release=dict(format='BPS1',patch_file=f'Itadaki_Street_3_English_{version}.bps',source_file=source.name,
              source_size=total,target_size=total,source_sha256=source_sha,target_sha256=target_sha,
              source_crc32=f'{source_crc:08x}',target_crc32=f'{target_crc:08x}',patch_sha256=digest(patch),
              patched_elf_sha256=digest(elf),counts=manifest['counts'],files=files,
              original_iso_required=True,cumulative=True,iso_created=False,
              visual_test='not run; tutor coverage is partial')
 write_new_or_identical(OUT/release['patch_file'],bytes(patch))
 write_new_or_identical(OUT/'release_manifest.json',encode_json(release))
 # Same validated v8 applier; only its default output filename changes.
 applier=(ROOT/'release/english_v8/apply_iso_patch.py').read_text(encoding='utf-8').replace('English_v8.iso',f'English_{version}.iso')
 write_new_or_identical(OUT/'apply_iso_patch.py',applier.encode('utf-8'))
 wrapper=(ROOT/'release/english_v8/apply_iso_patch.ps1').read_text(encoding='utf-8').replace('English_v8.iso',f'English_{version}.iso')
 write_new_or_identical(OUT/'apply_iso_patch.ps1',wrapper.encode('utf-8'))
 write_new_or_identical(OUT/'Apply_English_Patch.cmd',(ROOT/'release/english_v8/Apply_English_Patch.cmd').read_bytes())
 spec=importlib.util.spec_from_file_location('v9_applier',OUT/'apply_iso_patch.py')
 mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
 rel,commands,sc,tc=mod.load_recipe(); src_sha,crc=mod.hash_source(source)
 assert src_sha==source_sha and crc==sc
 actual_sha,crc=mod.generate(source,commands); assert actual_sha==target_sha and crc==tc
 recovered={f['path']:bytearray(Path('decompile',f['path']).read_bytes()) for f in files}
 for pos,size,payload in commands:
  if payload is None: continue
  matches=[f for f in files if f['iso_offset']<=pos and pos+size<=f['iso_offset']+f['size']]
  assert len(matches)==1, 'BPS writes outside verified file extents'
  f=matches[0]; off=pos-f['iso_offset']; recovered[f['path']][off:off+size]=payload
 for f in files: assert digest(recovered[f['path']])==f['patched_sha256']
 checks.append(dict(file='ISO',status='PASS',virtual_target_sha256=actual_sha,
                    bps_reconstructs_all_resources=True,writes_only_verified_extents=True,iso_created=False))
 write_new_or_identical(BUILD/'binary_and_bps_verification.json',encode_json(dict(status='PASS',checks=checks)))
 print(json.dumps(dict(status='PASS',counts=manifest['counts'],patch_bytes=len(patch),
                       elf_sha256=digest(elf),target_iso_sha256=target_sha,files=len(files)),indent=2))

if __name__=='__main__':main()
