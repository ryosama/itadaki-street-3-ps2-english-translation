"""Create a cumulative ISO BPS patch without writing/rebuilding an ISO.

Read ISO9660 directory to find SLPM_621.12; preserve extent, size and every
other byte. Streaming source/virtual-target SHA256 and CRC32, stdlib only.
BPS format: https://raw.githubusercontent.com/Alcaro/Flips/master/bps_spec.md
Only SourceRead and TargetRead are needed for this same-size patch.
"""
import hashlib
import json
import struct
import zlib
from pathlib import Path
from build_test_patch import EXPECTED_SHA, digest, encode_json, write_new_or_identical

SOURCE=Path('idataki3.original.iso')
PATCHED=Path('translation_work/phase8/revision1/patched/SLPM_621.12')
OUT=Path('translation_work/release/english_v8')
ISO_SHA='6e8e471f9b6aef1af78b9cf99407ffd9adaa2c51a871f622dd84db140404dcab'
SECTOR=2048

def number(value):
 result=bytearray()
 while True:
  low=value&127; value>>=7
  if value==0: result.append(low|128); return bytes(result)
  result.append(low); value-=1

def directory_record(raw):
 assert len(raw)>=34
 extent=struct.unpack_from('<I',raw,2)[0]; size=struct.unpack_from('<I',raw,10)[0]
 assert extent==struct.unpack_from('>I',raw,6)[0]
 assert size==struct.unpack_from('>I',raw,14)[0]
 return dict(name=raw[33:33+raw[32]].decode('ascii'),extent=extent,size=size,flags=raw[25])

def locate_elf(stream):
 for sector in range(16,64):
  stream.seek(sector*SECTOR); vd=stream.read(SECTOR)
  assert vd[1:6]==b'CD001' and vd[6]==1
  if vd[0]==1:
   assert struct.unpack_from('<H',vd,128)[0]==SECTOR
   root=directory_record(vd[156:156+vd[156]])
   break
  if vd[0]==255: raise ValueError('ISO9660 primary descriptor missing')
 else: raise ValueError('descriptor scan limit reached')
 stream.seek(root['extent']*SECTOR); data=stream.read(root['size']); pos=0; files=[]
 while pos<len(data):
  length=data[pos]
  if not length: pos=(pos//SECTOR+1)*SECTOR; continue
  assert pos+length<=len(data)
  record=directory_record(data[pos:pos+length]); files.append(record); pos+=length
 matches=[r for r in files if r['name'].split(';')[0].upper()=='SLPM_621.12']
 assert len(matches)==1, 'expected one root executable'
 result=matches[0]; assert not result['flags']&0x82, 'directory or multi-extent unsupported'
 return result,files

def differences(before,after,base):
 # Merge very short unchanged gaps to avoid inefficient tiny BPS actions.
 runs=[]; i=0
 while i<len(before):
  if before[i]==after[i]: i+=1; continue
  start=i; end=i+1; i+=1
  while i<len(before):
   if before[i]!=after[i]: end=i+1
   elif i-end>=8: break
   i+=1
  runs.append((base+start,after[start:end]))
 return runs

def checksums(stream,changes,total):
 source_hash=hashlib.sha256(); target_hash=hashlib.sha256(); source_crc=target_crc=0
 stream.seek(0); offset=0; idx=0
 while offset<total:
  raw=stream.read(min(4*1024*1024,total-offset)); assert raw
  source_hash.update(raw); source_crc=zlib.crc32(raw,source_crc)
  result=bytearray(raw); stop=offset+len(raw)
  while idx<len(changes) and changes[idx][0]+len(changes[idx][1])<=offset: idx+=1
  j=idx
  while j<len(changes) and changes[j][0]<stop:
   pos,data=changes[j]; left=max(offset,pos); right=min(stop,pos+len(data))
   result[left-offset:right-offset]=data[left-pos:right-pos]; j+=1
  target_hash.update(result); target_crc=zlib.crc32(result,target_crc); offset=stop
 return source_hash.hexdigest(),target_hash.hexdigest(),source_crc,target_crc

def main():
 original=Path('decompile/SLPM_621.12').read_bytes(); patched=PATCHED.read_bytes()
 assert digest(original)==EXPECTED_SHA
 manifest=json.loads(Path('translation_work/phase8/revision1/gameplay_patch_manifest.json').read_text(encoding='utf-8'))
 assert digest(patched)==manifest['patched_sha256']
 total=SOURCE.stat().st_size; assert total==575420416
 with SOURCE.open('rb') as stream:
  record,files=locate_elf(stream); base=record['extent']*SECTOR
  assert record['size']==len(original)==len(patched)
  stream.seek(base); assert stream.read(len(original))==original, 'ISO executable differs from extracted original'
  cnf=next(r for r in files if r['name'].split(';')[0]=='SYSTEM.CNF')
  stream.seek(cnf['extent']*SECTOR); config=stream.read(cnf['size']).decode('ascii')
  assert 'SLPM_621.12' in config, 'unexpected boot executable'
  changes=differences(original,patched,base)
  source_sha,target_sha,source_crc,target_crc=checksums(stream,changes,total)
 assert source_sha==ISO_SHA, 'wrong original ISO revision'
 patch=bytearray(b'BPS1'+number(total)+number(total)+number(0)); cursor=0
 for pos,data in changes:
  if pos>cursor: patch+=number(((pos-cursor-1)<<2)|0)
  patch+=number(((len(data)-1)<<2)|1)+data; cursor=pos+len(data)
 if cursor<total: patch+=number(((total-cursor-1)<<2)|0)
 patch+=struct.pack('<II',source_crc,target_crc)
 patch+=struct.pack('<I',zlib.crc32(patch))
 assert all(base<=pos and pos+len(raw)<=base+len(original) for pos,raw in changes)
 release=dict(format='BPS1',patch_file='Itadaki_Street_3_English_v8.bps',
              source_file=SOURCE.name,source_size=total,source_sha256=source_sha,
              target_size=total,target_sha256=target_sha,patch_sha256=digest(patch),
              source_crc32=f'{source_crc:08x}',target_crc32=f'{target_crc:08x}',
              elf_iso_offset=base,elf_sector=record['extent'],elf_size=len(patched),
              patched_elf_sha256=digest(patched),replacement_runs=len(changes),
              changed_bytes=sum(a!=b for a,b in zip(original,patched)),
              new_phase8_strings=155,prepared_drafts_integrated=145,
              preserved_phases=[4,5,6,7],iso_created=False,
              visual_validation='required for new gameplay texts; not yet tested in PCSX2')
 write_new_or_identical(OUT/release['patch_file'],bytes(patch))
 write_new_or_identical(OUT/'release_manifest.json',encode_json(release))
 print(json.dumps(release,indent=2)); print('BPS bytes:',len(patch))

if __name__=='__main__': main()
