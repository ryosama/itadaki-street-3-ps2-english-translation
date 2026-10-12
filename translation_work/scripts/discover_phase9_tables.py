"""Bounded read-only resource and tutor-pointer discovery; no original writes."""
import struct
from pathlib import Path
from inspect_mips import Elf
from build_test_patch import encode_json,write_new_or_identical

OUT=Path('translation_work/phase9/analysis')
def main():
 queries=['ストロベリタウン','チェリーレイク','ノースメロン','サウスオレンジ','マフィン観光']
 matches=[]
 for path in sorted(Path('decompile/STAGE').glob('MAP*.BIN')):
  b=path.read_bytes()
  for q in queries:
   pos=b.find(q.encode('cp932'))
   if pos>=0: matches.append(dict(file=str(path),query=q,offset=pos))
  if path.name=='MAP000.BIN':
   print('MAP000 header',b[:96].hex(' '))
   for off in range(len(b)):
    if b[off] and (off==0 or b[off-1]==0):
     end=b.index(b'\0',off) if b'\0' in b[off:] else len(b)
     try: s=b[off:end].decode('cp932')
     except UnicodeDecodeError: continue
     if len(s)>=2 and all(c.isprintable() for c in s): print(hex(off),repr(s))
 print('RESOURCE MATCHES',matches)
 elf=Elf('decompile/SLPM_621.12'); b=elf.data
 target_offsets=[0x3a0450,0x3a0600,0x3a1860,0x3ab7e8,0x3ac630,0x36f900]
 targets={off+0xff000:[] for off in target_offsets}
 for off in range(0,len(b)-3,4):
  value=struct.unpack_from('<I',b,off)[0]
  if value in targets: targets[value].append(off)
 refs={hex(k):[hex(p) for p in v] for k,v in targets.items()}; print('POINTERS',refs)
 for k,vals in targets.items():
  for off in vals[:3]:
   for p in range(max(0,off-16),off+20,4):
    v=struct.unpack_from('<I',b,p)[0]; t=v-0xff000
    if 0x36d000<=t<0x3b8000:
     try: s=b[t:b.index(b'\0',t)].decode('cp932')
     except UnicodeDecodeError: continue
     print('NEIGHBOR',hex(p),hex(t),repr(s))
 # Find calls to the known formatter, with a bounded context per call.
 calls=[]
 for off in range(0x1000,0x139594,4):
  w=struct.unpack_from('<I',b,off)[0]
  if w>>26==3 and ((w&0x3ffffff)<<2) in (0x136ac0,0x136fd0):
   pc=off+0xff000; calls.append(hex(pc))
   write_new_or_identical(OUT/f'formatter_call_{pc:08x}.asm',elf.disasm(pc-0x50,0xa0).encode())
 print('FORMATTER CALLS',calls)
 write_new_or_identical(OUT/'table_discovery.json',encode_json(dict(resource_matches=matches,pointer_references=refs,formatter_calls=calls)))

if __name__=='__main__':main()
