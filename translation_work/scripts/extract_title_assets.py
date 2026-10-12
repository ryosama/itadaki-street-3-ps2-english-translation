"""Read-only discovery/export of indexed multi-image SYS TI textures.

Supports observed PSMT8 descriptors with 256-entry RGBA palettes. Retains
headers, original indexes, CLUTs and offsets separately for future reinjection.
No source editing; stdlib PNG encoder. SYSTEM.TI mixed resources excluded.
"""
import struct
from pathlib import Path
from extract_ti import decode_linear,png_chunk
from build_test_patch import digest,encode_json,write_new_or_identical
import zlib

OUT=Path('translation_work/phase10/title_assets')
def rgba_png(w,h,rgba):
 rows=b''.join(b'\0'+rgba[y*w*4:(y+1)*w*4] for y in range(h))
 return b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+png_chunk(b'IDAT',zlib.compress(rows,9))+png_chunk(b'IEND',b'')

def extract(source):
 b=source.read_bytes(); np,ni=struct.unpack_from('<HH',b,4); header=struct.unpack_from('<I',b,8)[0]
 assert np==ni and 1<=ni<=3 and header==16+16*(np+ni)
 records=[]; bounds=[]
 for i in range(ni):
  pal=header+struct.unpack_from('<I',b,16+16*i+8)[0]
  d=16+16*np+16*i; w,h,fmt=struct.unpack_from('<HHH',b,d+2)
  pixels=header+struct.unpack_from('<I',b,d+8)[0]
  assert fmt==1 and w in (128,256,512) and h in (128,256,512)
  assert pal>=header and pixels>=header and pixels+w*h<=len(b) and pal+1024<=len(b)
  assert pixels==pal+1024
  palette=[tuple(b[pal+4*j:pal+4*j+4]) for j in range(256)]
  raw=b[pixels:pixels+w*h]; rgba=decode_linear(palette,raw)
  png=rgba_png(w,h,rgba); name=f'{source.stem}_{i:02d}.png'
  write_new_or_identical(OUT/'previews'/name,png)
  write_new_or_identical(OUT/'raw'/f'{source.stem}_{i:02d}.indices.bin',raw)
  write_new_or_identical(OUT/'raw'/f'{source.stem}_{i:02d}.clut.bin',b[pal:pal+1024])
  records.append(dict(image=i,png=name,width=w,height=h,palette_offset=pal,pixel_offset=pixels,
                      pixel_bytes=w*h,png_sha256=digest(png),clut_sha256=digest(b[pal:pal+1024]),
                      alpha_conversion='min(255, ps2_alpha * 255 // 128)',layout='linear PSMT8 with CSM1 palette permutation'))
  bounds.append((pal,pixels+w*h))
 assert sorted(bounds)[0][0]==header and sorted(bounds)[-1][1]==len(b)
 assert all(sorted(bounds)[i][1]==sorted(bounds)[i+1][0] for i in range(ni-1))
 return dict(source=str(source),source_size=len(b),source_sha256=digest(b),header_hex=b[:header].hex(),images=records)

def main():
 records=[]
 for name in ['STREET.TI','TAI01.TI','TAI02.TI','ENIX.TI','KOKUTI.TI','MENU0.TI','MENU1.TI','MENU2.TI']:
  r=extract(Path('decompile/SYS')/name); records.append(r)
 write_new_or_identical(OUT/'texture_inventory.json',encode_json(records))
 for r in records: print(r['source'],[(x['png'],x['width'],x['height']) for x in r['images']])

if __name__=='__main__':main()
