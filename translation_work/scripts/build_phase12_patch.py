"""Cumulative v12: add the user's second title texture, preserving v11.

Writes only new phase12 artifacts. Exact PNG RGBA roundtrip, unchanged main
texture/header, unchanged English ELF/MAPs, and reversible TI changes.
"""
import json
from pathlib import Path
from build_test_patch import digest,encode_json,write_new_or_identical,EXPECTED_SHA
from reinject_title_png import png_rgba
from extract_ti import decode_linear
from extract_title_assets import rgba_png

ROOT=Path('translation_work'); OUT=ROOT/'phase12/revision1'; BASE=ROOT/'phase11/revision1'
PNG=ROOT/'phase10/title_assets/editing/title_tiles_256_english.png'

def main():
 previous=json.loads((BASE/'phase11_manifest.json').read_text(encoding='utf-8'))
 elf=(BASE/'patched/SLPM_621.12').read_bytes()
 assert digest(Path('decompile/SLPM_621.12').read_bytes())==EXPECTED_SHA
 assert digest(elf)==previous['patched_sha256']=='a388e2810de478dc3da6df6ba8fa9e30ae360dc89a72e1405b51573281275515'
 source=Path('decompile/SYS/TAI01.TI'); original=source.read_bytes()
 assert digest(original)=='deecc401d6a4e4ae369d65d0cd4543ce3e3c6a2758ca2c90c4028500cc205301'
 base_title=(BASE/'patched/SYS/TAI01.TI').read_bytes()
 assert digest(base_title)==previous['title_ti_sha256']=='700d7912fb5feb208f70add273b80e2194173fb0d0cfc14596660ef968795fe0'
 patched=(OUT/'patched/SYS/TAI01.TI').read_bytes()
 imported=json.loads((OUT/'patched/SYS/TAI01.json').read_text(encoding='utf-8'))
 assert digest(patched)==imported['output_sha256']
 assert imported['base_sha256']==digest(base_title) and imported['image']==1
 assert len(patched)==len(original)==len(base_title)==329808
 assert original[:80]==patched[:80]
 # All main texture bytes including its CLUT are preserved from v11.
 assert patched[:263248]==base_title[:263248]
 w,h,expected=png_rgba(PNG); assert (w,h)==(256,256)
 pal=263248; pixels=264272; pixel_bytes=256*256
 actual=decode_linear([tuple(patched[pal+4*i:pal+4*i+4]) for i in range(256)],patched[pixels:pixels+pixel_bytes])
 assert actual==expected, 'second title texture does not match the user PNG'
 assert imported['max_alpha_rounding_error']==0
 fields=[]
 for kind,start,count in [('main_title_palette',80,1024),('main_title_pixels',1104,262144),
                          ('tiles_title_palette',pal,1024),('tiles_title_pixels',pixels,pixel_bytes)]:
  fields.append(dict(kind=kind,offset=start,capacity=count,original_hex=original[start:start+count].hex(),
                     after_hex=patched[start:start+count].hex()))
 title=dict(source=str(source),relative_iso_path='SYS/TAI01.TI',source_sha256=digest(original),
            patched_sha256=digest(patched),size=len(patched),records=fields)
 resources=[]; copies=[(OUT/'patched/SLPM_621.12',elf)]
 for r in previous['resources']:
  if r['relative_iso_path']=='SYS/TAI01.TI':
   resources.append(title); continue
  data=(BASE/'patched'/r['relative_iso_path']).read_bytes(); assert digest(data)==r['patched_sha256']
  resources.append(r); copies.append((OUT/'patched'/r['relative_iso_path'],data))
 assert len(resources)==34 and sum(r['relative_iso_path']=='SYS/TAI01.TI' for r in resources)==1
 for path,data in copies:write_new_or_identical(path,data)
 write_new_or_identical(OUT/'title_tiles_redecoded_256.png',rgba_png(w,h,actual))
 result=dict(source_sha256=EXPECTED_SHA,base_sha256=digest(elf),patched_sha256=digest(elf),
             patches=[],resources=resources,counts=dict(title_texture=1,new_text_strings=0),code_changes=0,
             previous_version='phase11/revision1',cumulative=True,title_artwork_unchanged=False,
             title_input=str(PNG),title_png_sha256=digest(PNG.read_bytes()),title_ti_sha256=digest(patched),
             previous_title_main_png_sha256=previous['title_png_sha256'],
             tutor_pages_total_translated=previous['tutor_pages_total_translated'],
             title_verification=dict(exact_rgba_roundtrip=True,unchanged_main_atlas=True,
                                     unchanged_ti_header=True,alpha_rounding_error=0,
                                     width=w,height=h,colors=imported['colors'],english_textures_total=2),
             visual_test='v12 not tested in PCSX2; user reports v11 title worked')
 write_new_or_identical(OUT/'phase12_manifest.json',encode_json(result))
 print(json.dumps({k:v for k,v in result.items() if k not in ('patches','resources')},indent=2))

if __name__=='__main__':main()
