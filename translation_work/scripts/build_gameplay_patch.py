"""Integrate every prepared phase8 draft in a NEW ELF, with bounded corrections.

Read-only originals; no relocation or code changes. Run from project root.
The manifest records the final wording, exact reversible bytes and visual limits.
"""
import csv
import io
import json
import re
from pathlib import Path
from build_test_patch import EXPECTED_SHA, digest, encode_json, write_new_or_identical

ROOT=Path('translation_work')
OUT=ROOT/'phase8/revision1'
BASE=ROOT/'phase7/revision3/patched/SLPM_621.12'
PRINTF=re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs])')
COLORS=re.compile(r'/c\d')
CORRECTIONS={
 0x34D008:'Sell stk\n', 0x34D128:'Stocks:\n', 0x34D138:'none owned.',
 0x34D1D8:'Shops:\n', 0x34D1F0:'No trades\n', 0x34D200:'available.',
 0x34D218:'No shops\n', 0x34E850:'Inv. left', 0x363840:'Rent earned',
 0x36C760:'/c2No cash!/c0', 0x36C778:'Sell stk\nSell shop',
 0x36C8A0:'Choose their\nshop.', 0x3B9AA8:'Class',
}
EXTRA={
 0x34CFD8:'Yes\nNo',
 0x3602D0:'Rank    Map rank\n', 0x3602F8:'Busts   Caused\n',
 0x360318:'Max in  Max out\n', 0x360338:'Rent in Rent out\n',
 0x360358:'Value   Stocks',
 0x363A20:'Defied      %4d', 0x363A38:'Comforted   %4d',
 0x3B8B28:'Lap%3d', 0x34C7B0:'Shop',
}

def main():
 original=Path('decompile/SLPM_621.12').read_bytes(); base=BASE.read_bytes()
 assert digest(original)==EXPECTED_SHA
 assert digest(base)=='9b297f21d71c86719ca7f2a3e37d53fff765a17103841e144e2e703404e981c1'
 catalog=json.loads((ROOT/'phase8/screenshot_review/gameplay_text_candidates.json').read_text(encoding='utf-8'))
 translations={int(r['offset'],16):r['english_draft'] for r in catalog if r['english_draft']}
 assert len(translations)==145
 translations.update(CORRECTIONS); translations.update(EXTRA)
 patched=bytearray(base); records=[]; allowed=set()
 for start,english in sorted(translations.items()):
  end=original.index(b'\0',start)+1; before=original[start:end]
  ja=before[:-1].decode('cp932'); current=base[start:end]
  # The sole overlap is the previously translated map-set label.
  assert current==before or start==0x3607E8
  if start==0x3607E8: assert current.split(b'\0')[0]==b'Itadaki Maps'
  assert all(c.isprintable() or c in '\n\u3000' for c in ja)
  raw=english.encode('ascii')+b'\0'
  assert len(raw)<=len(before), (hex(start),english,len(raw),len(before))
  assert PRINTF.findall(ja)==PRINTF.findall(english), hex(start)
  assert COLORS.findall(ja)==COLORS.findall(english), hex(start)
  assert ja.endswith('\n')==english.endswith('\n'), hex(start)
  if start in (0x34D228,0x34D250,0x36C358,0x34CFD8,0x36C480,0x36C778,0x34DDA0,0x34DEE8,0x34DF08):
   assert ja.count('\n')==english.count('\n'), 'choice count changed'
  if start in (0x34D228,0x34D250):
   lines=COLORS.sub('',english).split('\n')
   assert len(lines)==3 and all(len(s)==8 for s in lines)
  assert not allowed.intersection(range(start,end))
  allowed.update(range(start,end)); after=raw.ljust(len(before),b'\0')
  patched[start:end]=after
  records.append(dict(offset=start,offset_hex=hex(start),capacity=len(before),japanese=ja,
                      english=english,original_hex=before.hex(),before_hex=current.hex(),after_hex=after.hex(),
                      visual_status='requires in-game validation'))
 assert len(patched)==len(original)==3923328
 assert patched[0x1000:0x139594]==base[0x1000:0x139594]
 assert all(i in allowed for i,(a,b) in enumerate(zip(base,patched)) if a!=b)
 restored=bytearray(patched)
 for r in records: restored[r['offset']:r['offset']+r['capacity']]=bytes.fromhex(r['before_hex'])
 assert restored==base
 manifest=dict(source_sha256=EXPECTED_SHA,base=str(BASE),base_sha256=digest(base),
               patched_sha256=digest(patched),patch_count=len(records),prepared_drafts_integrated=145,
               code_changes=0,relocations=0,patches=records)
 write_new_or_identical(OUT/'patched/SLPM_621.12',bytes(patched))
 write_new_or_identical(OUT/'gameplay_patch_manifest.json',encode_json(manifest))
 stream=io.StringIO(newline=''); fields=['offset_hex','japanese','english','capacity','visual_status']
 writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
 for r in records: writer.writerow({k:r[k] for k in fields})
 write_new_or_identical(OUT/'gameplay_translations.csv',stream.getvalue().encode('utf-8-sig'))
 print(json.dumps({k:v for k,v in manifest.items() if k!='patches'},indent=2))

if __name__=='__main__': main()
