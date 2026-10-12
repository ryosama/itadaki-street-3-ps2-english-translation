"""New cumulative ELF + MAP copies for tutors, district names and UI fixes.

Stdlib only; original files and prior versions are never written.
Tutor renderer is direct 0x139390, NOT the card formatter: no literal quotes.
Tutor font=24, width=336, pitch=28: conservatively <=14 chars, <=4 lines.
MAP name fields: 32 bytes in 48-byte records; preserve all following metadata.
"""
import csv
import io
import json
import re
import struct
import textwrap
from collections import Counter
from pathlib import Path
from build_test_patch import EXPECTED_SHA,digest,encode_json,write_new_or_identical

ROOT=Path('translation_work'); OUT=ROOT/'phase9/revision1'
BASE=ROOT/'phase8/revision1/patched/SLPM_621.12'
PRINTF=re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs])')
COLORS=re.compile(r'/c\d')
UI={
 0x3600E0:'Options\n', 0x360A20:'Who will play?',
 0x34D048:'All', 0x34D068:'Text\n', 0x34D088:'Trade\n', 0x34D098:'Save\n',
 0x34D3C0:'Tutor', 0x34D3D0:'Full help\nNormal help\nLess help',
 0x3693E8:'Change how much\nhelp your tutor\ngives you.',
 0x3B8880:'Bid\n', 0x3B8888:'Swap\n', 0x3B8890:'Redo', 0x3B8898:'Net\n',
 0x3B88A0:'Fast\n', 0x3B88A8:'Normal\n', 0x3B88B0:'Slow',
 0x3B88B8:'Yes\n', 0x3B88C0:'No',
 0x3B8820:'Name', 0x3B8828:'Cash', 0x3B8830:'Stk', 0x3B8838:'Shops',
 0x3B8848:'%d', 0x3B8850:'%d', 0x3B8858:'Badge', 0x3B8860:'Closed', 0x3B8868:'Casino',
 0x3B8958:'%d', 0x3B8900:'L%d',
 0x34CC28:'Value', 0x34CC38:'Fee', 0x34CC60:'Shop rank', 0x34CC70:'Inv. left',
 0x3B87C8:'Stall', 0x3B87D0:'Plot',
 0x34E208:'Price Result', 0x3B8910:'Price', 0x3B8918:'Left', 0x3B8920:'Result',
 0x34E1F8:'Area',
 0x34E970:'$%7dG', 0x34E980:'S%7dG', 0x34E990:'Sh%7dG', 0x34E9A0:'NW%7dG',
 0x34E9B0:'Shp%6d', 0x34E9C0:'Stk%6d',
 0x3B8AF8:'$', 0x3B8B00:'S', 0x3B8B08:'Sh', 0x3B8B10:'NW',
 0x361CF8:'Goal   %d', 0x361D10:'Busts  %s', 0x361D28:'Casino %s',
 0x3692A8:'Goal %dG\nBusts %d',
 0x36EC38:'A simple board for\nbeginners. Only the\nbank offers a fork.\nLearn the basics here.',
 0x36F900:'Bank\nAll suits: salary\nPass to buy stock',
 0x36F948:'Spade\nPass to collect\nthe spade suit',
 0x36F980:'Heart\nPass to collect\nthe heart suit',
 0x36F9B0:'Diamond\nPass to collect\nthe diamond suit',
 0x36F9E0:'Club\nPass to collect\nthe club suit',
 0x36FA18:'Chance\nLand here to draw\na Chance card',
 0x36FA48:'Closed\nYour shops close\nwhile you stay here',
 0x36FA88:'Lucky\nGet a share of fees\nwhile you stay here',
 0x36FAC0:'Broker\nLand here\nto buy stock',
 0x36FAE8:'Dice shop\nLand here to\nroll again',
 0x36FB20:'Casino\nLand here to\nplay a minigame',
}

SHORT={
 'Australia':'Austral.','Devil Swamp':'D Swamp','Icicle Wall':'Icicle',
 'Ice Cliff':'IceCliff','Flame Wall':'Flame','Pine Blow':'PineBlow',
 'Open Cafe':'OpenCafe','Comet Ginza':'C Ginza','Planet Mall':'Planet',
 'Misty Hill':'Misty','Cliff Edge':'Cliff','Blue Marlin':'Marlin',
 'Chef Center':'Chef Ctr','Chef Front':'C Front','Chef Back':'C Back',
 'Cross Warp':'X Warp','Skull Warp':'Skull',
 'Right Arrow':'R Arrow','Left Arrow':'L Arrow',
 'Yunohana Spa':'Yunohana','Lake Castle':'Castle','Safari Land':'Safari',
 'My Downtown':'My Town','Lucky Panel':'L Panel','Near Resort':'Resort',
 'Grand Cross':'G Cross','Feather L':'Feath L','Mad Dining':'Dining',
 'Hell Stairs':'Stairs','Blood Mural':'Mural','Crash Room':'Crash',
 'Dark Kitchen':'Kitchen','Right Base':'R Base','Left Base':'L Base',
 'Strawb Town':'Strawby','South Orange':'S Orange','North Melon':'N Melon',
 'Middle East':'Mid East','Marble Tea':'Marb Tea','Marble Cafe':'MarbCafe',
 'Moonlight St':'Moonlit','Raincloud Town':'Raincld','Rainbow Hill':'Rainbow',
 'Northwest':'NW','Northeast':'NE','Southwest':'SW','Southeast':'SE',
 'San Francisco':'San Fran','Los Angeles':'LA','New York':'New York',
 'Central Lily':'C Lily','Central Space':'C Space','Central Park':'C Park',
 'Central St':'C Street','Center Bridge':'C Bridge',
 'Red Mountain':'Red Mtn','Blue Mountain':'Blue Mtn','Quaking Crater':'Crater',
 'North Bridge':'N Bridge','South Bridge':'S Bridge','Sky Blue Bay':'Sky Blue',
 'Green Harbor':'G Harbor','Yellow Beach':'Y Beach','Full Belly Is.':'FullBely',
 'Warrior Graves':'Graves','Blizzard Shrine':'Blizzard','Spring Pool':'Spring',
 'Lower Cliff St':'Cliff St','Jellyfish Lane':'Jellyfsh','Dolphin Lane':'Dolphin',
 'Soy Sauce St':'Soy St','Hot Sand Dunes':'Hot Sand','Heaven Garden':'Heaven',
 'Cambrian Plain':'Cambrian','Jurassic Lake':'Jurassic','Silurian Range':'Silurian',
 'Ordovis Land':'Ordovis','Devonia Cave':'Devonia','Bongo Village':'Bongo',
 'Satan Corridor':'Satan','Papillon St':'Papillon','Rainbow Steps':'Rainbow',
 'Thunder Tower':'Thunder','Raincloud Gate':'Raincld','Archimes Vale':'Archimes',
 'Rocket Center':'Rocket','Princess Area':'Princess','Mountain Area':'Mountain',
 'Govt Area':'Govt','Industry Block':'Industry','Marine Factory':'Factory',
 'Royal Straight':'Royal','Neptune':'Neptune','Koshinetsu':'Koshin',
 'Ochanomizu':'Ochanomi','Shinjuku':'Shinjuku','Hokkaido':'Hokkaido',
 'Gull Wing':'Gullwing','Escape Board':'Escape','Chimney Road':'Chimney',
 'Willow Walk':'Willow','Melakoi Park':'Melakoi','Canola Bay':'Canola',
 'Kerria Land':'Kerria','Anemone River':'Anemone','Timothy River':'Timothy',
 'Milky Plateau':'Milky','Seagull Hills':'Seagull',
 'Maharata Isle':'Maharata','Shopping Isle':'Shopping',
 'Ghostfire St':'Ghost','Back Mist St':'Mist','Armageddon':'Armagdn','Apocalypse':'Apocalyp',
}
SUFFIXES=(' Area',' Line',' Block',' Town',' Road',' St',' Center',' Park',' Gate',' Ring',
          ' Corridor',' Bay',' Isle',' Temple',' Course',' Loop',' Circle',' Farm',' Palace',
          ' Port',' Dome',' Factory',' Range',' Hall',' Lake',' Hotel',' Mountain',' Plain',
          ' Village',' Bridge',' Walk',' Way',' Vale',' Pool',' Front',' Back',' Deck',' Dunes')

def compact_name(full):
 if len(full)<=8: return full
 if full in SHORT: return SHORT[full]
 for suffix in SUFFIXES:
  if full.endswith(suffix) and len(full[:-len(suffix)])<=8: return full[:-len(suffix)]
 raise ValueError(f'needs explicit compact district name: {full}')

def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def main():
 original=Path('decompile/SLPM_621.12').read_bytes(); base=BASE.read_bytes()
 assert digest(original)==EXPECTED_SHA
 assert digest(base)=='44284f55ee99f13d734346785c1fffee2ce3689e722c9ac264744038ae5fe1d2'
 tutors=read(ROOT/'translations/tutors_phase9_en.json')
 translations={int(k,16):('tutor',v) for k,v in tutors.items()}
 translations.update({k:('ui',v) for k,v in UI.items()})
 patched=bytearray(base); rows=[]; allowed=set()
 for start,(kind,full) in sorted(translations.items()):
  end=original.index(b'\0',start)+1; old=original[start:end]; ja=old[:-1].decode('cp932')
  english=('\n'.join(textwrap.wrap(full,width=14,break_long_words=False,break_on_hyphens=False))
           if kind=='tutor' and '\n' not in full else full)
  if ja.endswith('\n') and not english.endswith('\n'): english+='\n'
  payload=english.encode('ascii')+b'\0'
  assert len(payload)<=len(old), (hex(start),'bytes',len(payload),len(old),english)
  if kind=='tutor':
   assert max(map(len,english.rstrip('\n').split('\n')))<=14, (hex(start),english)
   assert len(english.rstrip('\n').split('\n'))<=4, (hex(start),'lines',english)
   assert all(c not in ja for c in '{}'), 'dynamic format requires separate analysis'
  assert PRINTF.findall(ja)==PRINTF.findall(english), (hex(start),'printf')
  assert COLORS.findall(ja)==COLORS.findall(english), (hex(start),'colors')
  assert ja.endswith('\n')==english.endswith('\n')
  assert not allowed.intersection(range(start,end)); allowed.update(range(start,end))
  after=payload.ljust(len(old),b'\0'); patched[start:end]=after
  rows.append(dict(kind=kind,offset=start,offset_hex=hex(start),capacity=len(old),japanese=ja,
                   english=english,full_english=full,original_hex=old.hex(),
                   before_hex=base[start:end].hex(),after_hex=after.hex(),visual_status='not yet tested'))
 assert patched[0x1000:0x139594]==base[0x1000:0x139594]
 assert len(patched)==len(original)
 assert all(i in allowed for i,(a,b) in enumerate(zip(base,patched)) if a!=b)
 resources=[]; districts=read(ROOT/'translations/districts_phase9_en.json')
 for filename,names in sorted(districts.items()):
  source=Path('decompile/STAGE')/filename; raw=source.read_bytes(); edited=bytearray(raw)
  assert struct.unpack_from('<I',raw,0)[0]==3
  start=struct.unpack_from('<I',raw,32)[0]; end=struct.unpack_from('<I',raw,48)[0]
  assert start==192 and end>=start and (end-start)%48==0 and end<=len(raw)
  assert len(names)==(end-start)//48
  records=[]; seen=set()
  for i,full in enumerate(names):
   off=start+48*i; field=raw[off:off+32]
   assert b'\0' in field
   japanese=field.split(b'\0')[0].decode('cp932'); english=compact_name(full)
   assert len(english)<=8 and english not in seen,(filename,english)
   seen.add(english); payload=english.encode('ascii')+b'\0'; assert len(payload)<=32
   assert field[len(field.split(b'\0')[0])+1:]==b'\0'*(31-len(field.split(b'\0')[0]))
   after=payload.ljust(32,b'\0'); edited[off:off+32]=after
   records.append(dict(kind='district',offset=off,capacity=32,japanese=japanese,english=english,
                       full_english=full,original_hex=field.hex(),after_hex=after.hex()))
  # Translate the visible Candyland title and one shop named in a screenshot.
  if filename=='MAP003.BIN':
   for off,english in [(64,'Candyland'),(672,'Muffin Tours')]:
    field=raw[off:off+32]; payload=english.encode('ascii')+b'\0'
    assert len(payload)<=32
    after=payload.ljust(32,b'\0'); edited[off:off+32]=after
    records.append(dict(kind='map_title' if off==64 else 'shop_name',offset=off,capacity=32,
                        japanese=field.split(b'\0')[0].decode('cp932'),english=english,
                        full_english=english,original_hex=field.hex(),after_hex=after.hex()))
  changed_regions={p for r in records for p in range(r['offset'],r['offset']+32)}
  assert all(i in changed_regions for i,(a,b) in enumerate(zip(raw,edited)) if a!=b)
  assert len(raw)==len(edited)
  resources.append(dict(source=str(source),relative_iso_path='STAGE/'+filename,
                        source_sha256=digest(raw),patched_sha256=digest(edited),size=len(raw),records=records))
  # Delay all output until every translation has passed checks.
  resources[-1]['temporary_bytes']=bytes(edited)
 # Catalogue the complete original tutor table, including remaining Japanese.
 inventory=[]
 for gender,start in [('female',0x31DE58),('male',0x321698)]:
  for event in range(720):
   for page in range(5):
    slot=start+20*event+4*page; va=struct.unpack_from('<I',original,slot)[0]
    if va==0: continue
    off=va-0xFF000; assert 0<=off<len(original)
    text=original[off:original.index(b'\0',off)].decode('cp932')
    inventory.append(dict(gender=gender,event=event,page=page,pointer_offset=slot,
                          text_offset=off,japanese=text,translated=hex(off) in tutors))
 write_new_or_identical(OUT/'patched/SLPM_621.12',bytes(patched))
 for r in resources:
  data=r.pop('temporary_bytes'); write_new_or_identical(OUT/'patched'/r['relative_iso_path'],data)
 counts=dict(Counter(r['kind'] for r in rows)); counts['district']=sum(len(d['records'])-(2 if d['relative_iso_path'].endswith('MAP003.BIN') else 0) for d in resources)
 manifest=dict(source_sha256=EXPECTED_SHA,base_sha256=digest(base),patched_sha256=digest(patched),
               counts=counts,patches=rows,resources=resources,code_changes=0,
               tutor_renderer='direct 0x139390, no card-formatter escaping',
               tutor_table_pages=len(inventory),tutor_pages_covered=sum(r['translated'] for r in inventory))
 write_new_or_identical(OUT/'phase9_manifest.json',encode_json(manifest))
 write_new_or_identical(OUT/'tutor_table_inventory.json',encode_json(inventory))
 stream=io.StringIO(newline=''); fields=['resource','kind','offset','japanese','english','full_english']
 writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
 for r in rows: writer.writerow(dict(resource='SLPM_621.12',**{k:r[k] for k in fields if k!='resource'}))
 for res in resources:
  for r in res['records']: writer.writerow(dict(resource=res['relative_iso_path'],**{k:r[k] for k in fields if k!='resource'}))
 write_new_or_identical(OUT/'translations.csv',stream.getvalue().encode('utf-8-sig'))
 print(json.dumps({k:v for k,v in manifest.items() if k not in ('patches','resources')},indent=2))

if __name__=='__main__':main()
