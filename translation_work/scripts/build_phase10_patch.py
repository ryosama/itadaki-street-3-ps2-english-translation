"""Cumulative v10 text/board copies; original and v9 sources remain read-only.

Tutor text directly rendered, <=14 characters/line and four lines.
Embedded map descriptors have 32-byte names and 12-byte numeric metadata.
All changes are fixed-size, recorded and reversible. No texture editing here.
"""
import json
import struct
from pathlib import Path
from collections import Counter
from build_test_patch import digest,EXPECTED_SHA,encode_json,write_new_or_identical
from build_phase9_patch import PRINTF,COLORS

ROOT=Path('translation_work'); OUT=ROOT/'phase10/revision2'; PREV=ROOT/'phase9/revision1'
UI={
 0x35FEF0:'Map %s\n',0x34CDE0:'Lap',0x34CDF0:'Net',0x34CE00:'Shops',0x34CE10:'Stocks',
 0x3B8808:'Goal',0x305E20:'Lucky',
 0x34CE20:'Lap%2d',0x34CEC0:'Lucky',
 0x36C6D8:'Lucky chance!\nShare in other\nplayers\' fees.',
 0x34D0B8:'Mono\n',0x34D0C8:'ST',0x34D0D8:'ON\n',0x34D0E8:'OFF',
 0x3B88A8:'Med\n',
}
ELF_MAPS={
 0x1C6F00:'Right Half',0x1C6F2C:'Sophie Cave',0x1C6F58:'Candyland',
 0x1C6F84:'Mermaid City',0x1C6FB0:'Space Cafe',0x1C6FDC:'Rainforest',
 0x1C7008:'Moon Cruise',0x1C7034:'Sushi Loop',0x1C7060:'Zipang',
 0x1C708C:'Horror House',0x1C70B8:'Cross',0x1C70E4:'Machu Picchu',
 0x1C7110:'Maharata Is.',0x1C713C:'Lake Mtn',0x1C7168:'Cloverland',
 0x1C7194:'Moon City',0x1C71C0:'Skyscrapers',0x1C71EC:'Dream World',
 0x1C7218:'Freeway',0x1C7244:'Sea City',0x1C7270:'Casino Town',
 0x1C729C:'Japan',0x1C72C8:'America',0x1C72F4:'Nebula',
 0x1C7320:'Space Colony',0x1C734C:'Queen Bunny',0x1C7378:'Prehistory',
 0x1C73A4:'Float Land',0x1C73D0:'Cursed Manor',0x1C73FC:'Sapata Lines',0x1C7428:'Solar System'
}
MAP_TITLES=['SW','Left Half','Sophie Cave','Candyland','Mermaid City','Space Cafe','Lakeland',
 'Moon Cruise','Sushi Loop','Zipang','Horror Land','Cross','Machu Picchu','Maharata Is.',
 'Lake Mtn','Cloverland','Moon City','Skyscrapers','Dream World','Freeway','Sea City',
 'Casino Town','Japan','America','Nebula','Space Colony','Queen Bunny','Prehistory',
 'Float Land','Cursed Manor','Sapata Lines','Solar System','Debug Street']
SHOPS=['Sweet Bank','Financier Gems','Tiramisu Drugs','Pie Diner','Berry Tart',
 'Muffin Tours','Fairy Transit','Waffle Cafe','Cherry Candy','Montblanc Ski',
 'Parfait Sport','Sherbet Works','Melon Frappe','Mousse Decor','Cookie Studio',
 'Choco Salon','Orange Cream','Chiboust Co','Madeleine Wood','Jelly Flowers',
 'Pine Crepes','Spade','Diamond','Heart','Club','?','Closed','Lucky']

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def main():
 original=Path('decompile/SLPM_621.12').read_bytes(); base=(PREV/'patched/SLPM_621.12').read_bytes()
 assert digest(original)==EXPECTED_SHA
 assert digest(base)=='9e54f6208f4571ca649bcdda3fb48d18f23b11aa2af2dedb0bcd141748a2c4cc'
 tutors=read(ROOT/'translations/tutors_phase10_en.json')
 todo={int(k,16):('tutor',v,None) for k,v in tutors.items()}
 todo.update({o:('ui',v,None) for o,v in UI.items()})
 todo.update({o:('map_title',v,32) for o,v in ELF_MAPS.items()})
 # Exact stand-alone variants: no substring replacement inside dialogue.
 variants={'ひとり':'1','ふたり':'2','さんにん':'3','ぜんぶ':'All',
           '目標':'Goal','ラッキー':'Lucky','あゆみ':'Ayumi','レイ':'Rei','イタロー':'Itaro'}
 for ja,en in variants.items():
  raw=ja.encode('cp932')+b'\0'; pos=0
  while (o:=original.find(raw,pos))>=0:
   pos=o+1
   if o>=0x34CC00 and original[o-1]==0 and o not in todo:
    end=o+len(raw)
    if base[o:end]==original[o:end]:todo[o]=('ui',en,None)
 patched=bytearray(base); records=[]; allowed=set()
 for o,(kind,en,field) in sorted(todo.items()):
  end=o+field if field else original.index(b'\0',o)+1; before=original[o:end]
  text=before.split(b'\0')[0].decode('cp932')
  assert text and all(c.isprintable() or c in '\n\u3000' for c in text),(hex(o),text)
  if field:
   occupied=len(text.encode('cp932'))+1
   assert before[occupied:]==b'\0'*(field-occupied)
   assert len(en)<=12
  if text.endswith('\n') and not en.endswith('\n'):en+='\n'
  payload=en.encode('ascii')+b'\0'; assert len(payload)<=len(before),(hex(o),en,len(payload),len(before))
  if kind=='tutor':
   lines=en.rstrip('\n').split('\n'); assert len(lines)<=4 and max(map(len,lines))<=14,(hex(o),lines)
   assert not PRINTF.findall(text),'selected tutor page has dynamic parameters'
  else:assert PRINTF.findall(text)==PRINTF.findall(en),(hex(o),'printf')
  assert COLORS.findall(text)==COLORS.findall(en)
  assert text.endswith('\n')==en.endswith('\n')
  assert not allowed.intersection(range(o,end));allowed.update(range(o,end))
  after=payload.ljust(len(before),b'\0');patched[o:end]=after
  records.append(dict(kind=kind,offset=o,offset_hex=hex(o),capacity=len(before),japanese=text,
                      english=en,original_hex=before.hex(),before_hex=base[o:end].hex(),after_hex=after.hex()))
 assert len(patched)==len(original) and patched[0x1000:0x139594]==base[0x1000:0x139594]
 assert all(i in allowed for i,(a,b) in enumerate(zip(base,patched)) if a!=b)
 prior=read(PREV/'phase9_manifest.json'); resources=[]; pending=[]
 for prev in prior['resources']:
  name=prev['relative_iso_path']; source=Path(prev['source']); raw=source.read_bytes()
  current=(PREV/'patched'/name).read_bytes(); assert digest(current)==prev['patched_sha256']
  edited=bytearray(current); regions={r['offset']:r for r in prev['records']}
  filename=Path(name).name; idx=int(filename[3:6]); changes={64:MAP_TITLES[idx]}
  if filename=='MAP003.BIN':changes.update({0x1B0+i*48:n for i,n in enumerate(SHOPS)})
  for off,en in changes.items():
   original_field=raw[off:off+32]; ja=original_field.split(b'\0')[0].decode('cp932')
   assert b'\0' in original_field and len(en)<=16
   after=(en.encode('ascii')+b'\0').ljust(32,b'\0');edited[off:off+32]=after
   regions[off]=dict(kind='map_title' if off==64 else 'shop_name',offset=off,capacity=32,japanese=ja,
                     english=en,full_english=en,original_hex=original_field.hex(),after_hex=after.hex())
  rebuilt=bytearray(edited)
  for r in regions.values():rebuilt[r['offset']:r['offset']+32]=bytes.fromhex(r['original_hex'])
  assert rebuilt==raw and len(edited)==len(raw)
  resources.append(dict(source=str(source),relative_iso_path=name,source_sha256=digest(raw),
                        patched_sha256=digest(edited),size=len(raw),records=sorted(regions.values(),key=lambda r:r['offset'])))
  pending.append((OUT/'patched'/name,bytes(edited)))
 manifest=dict(source_sha256=EXPECTED_SHA,base_sha256=digest(base),patched_sha256=digest(patched),
               counts=dict(Counter(r['kind'] for r in records)),patches=records,resources=resources,code_changes=0,
               tutor_pages_total_translated=96+len(tutors),tutor_pages_total=1825,
               previous_version='phase9/revision1',title_artwork_unchanged=True)
 write_new_or_identical(OUT/'patched/SLPM_621.12',bytes(patched))
 for path,data in pending:write_new_or_identical(path,data)
 write_new_or_identical(OUT/'phase10_manifest.json',encode_json(manifest))
 print(json.dumps({k:v for k,v in manifest.items() if k not in ('patches','resources')},indent=2))

if __name__=='__main__':main()
