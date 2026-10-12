"""Include user's English title PNG in a cumulative v11 working copy.

Reads the original TI, the unchanged user PNG, and v10 translated resources.
Verifies exact RGBA reconstruction, unchanged header/second texture and v10
preservation. Writes only new translation_work/phase11 artifacts.
"""
import struct
from pathlib import Path
import json
from build_test_patch import digest,encode_json,write_new_or_identical,EXPECTED_SHA
from reinject_title_png import png_rgba
from extract_ti import decode_linear
from extract_title_assets import rgba_png

ROOT=Path('translation_work'); OUT=ROOT/'phase11/revision1'; BASE=ROOT/'phase10/revision2'
PNG=ROOT/'phase10/title_assets/editing/title_main_512_english.png'

def main():
 previous=json.loads((BASE/'phase10_manifest.json').read_text(encoding='utf-8'))
 original_elf=Path('decompile/SLPM_621.12').read_bytes()
 base_elf=(BASE/'patched/SLPM_621.12').read_bytes()
 assert digest(original_elf)==EXPECTED_SHA
 assert digest(base_elf)==previous['patched_sha256']=='a388e2810de478dc3da6df6ba8fa9e30ae360dc89a72e1405b51573281275515'
 source=Path('decompile/SYS/TAI01.TI'); original=source.read_bytes()
 assert digest(original)=='deecc401d6a4e4ae369d65d0cd4543ce3e3c6a2758ca2c90c4028500cc205301'
 patched=(OUT/'patched/SYS/TAI01.TI').read_bytes()
 import_manifest=json.loads((OUT/'patched/SYS/TAI01.json').read_text(encoding='utf-8'))
 assert digest(patched)==import_manifest['output_sha256']
 assert len(patched)==len(original)==329808
 assert original[:80]==patched[:80]
 # Preserve ALL of the right-hand atlas and its independent CLUT.
 assert patched[263248:]==original[263248:]
 w,h,expected=png_rgba(PNG); assert (w,h)==(512,512)
 pal=80; pixels=1104; pixel_bytes=512*512
 actual=decode_linear([tuple(patched[pal+4*i:pal+4*i+4]) for i in range(256)],patched[pixels:pixels+pixel_bytes])
 assert actual==expected, 'title RGBA roundtrip differs from user PNG'
 assert import_manifest['max_alpha_rounding_error']==0
 records=[]
 for kind,start,count in [('title_palette',pal,1024),('title_pixels',pixels,pixel_bytes)]:
  records.append(dict(kind=kind,offset=start,capacity=count,original_hex=original[start:start+count].hex(),
                      after_hex=patched[start:start+count].hex()))
 title=dict(source=str(source),relative_iso_path='SYS/TAI01.TI',source_sha256=digest(original),
            patched_sha256=digest(patched),size=len(patched),records=records)
 resources=previous['resources']+[title]
 copies=[(OUT/'patched/SLPM_621.12',base_elf)]
 for r in previous['resources']:
  data=(BASE/'patched'/r['relative_iso_path']).read_bytes()
  assert digest(data)==r['patched_sha256']
  copies.append((OUT/'patched'/r['relative_iso_path'],data))
 for path,data in copies:write_new_or_identical(path,data)
 write_new_or_identical(OUT/'title_redecoded_512.png',rgba_png(w,h,actual))
 result=dict(source_sha256=EXPECTED_SHA,base_sha256=digest(base_elf),patched_sha256=digest(base_elf),
             patches=[],resources=resources,counts=dict(title_texture=1,new_text_strings=0),code_changes=0,
             previous_version='phase10/revision2',cumulative=True,title_artwork_unchanged=False,
             title_input=str(PNG),title_png_sha256=digest(PNG.read_bytes()),title_ti_sha256=digest(patched),
             prior_text_counts_preserved=previous['counts'],tutor_pages_total_translated=149,
             title_verification=dict(exact_rgba_roundtrip=True,unchanged_right_atlas=True,
                                     unchanged_ti_header=True,alpha_rounding_error=0,
                                     width=w,height=h,colors=import_manifest['colors']),
             visual_test='not run in PCSX2')
 write_new_or_identical(OUT/'phase11_manifest.json',encode_json(result))
 print(json.dumps({k:v for k,v in result.items() if k not in ('patches','resources')},indent=2))

if __name__=='__main__':main()
