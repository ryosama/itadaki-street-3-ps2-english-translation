"""Export exact indexed PNGs for Photoshop and verify PNG->TI no-op identity."""
import struct
import zlib
from pathlib import Path
from extract_ti import png_chunk,clut_index_ps2
from reinject_title_png import png_rgba,rewrite
from build_test_patch import digest,encode_json,write_new_or_identical

def main():
 source=Path('decompile/SYS/TAI01.TI'); data=source.read_bytes()
 out=Path('translation_work/phase10/title_assets/editing'); results=[]
 for image,name in [(0,'title_main_512.png'),(1,'title_tiles_256.png')]:
  d=48+16*image; w,h,fmt=struct.unpack_from('<HHH',data,d+2); assert fmt==1
  pal=80+struct.unpack_from('<I',data,16+16*image+8)[0]
  pixels=80+struct.unpack_from('<I',data,d+8)[0]
  colors=[tuple(data[pal+4*clut_index_ps2(i):pal+4*clut_index_ps2(i)+4]) for i in range(256)]
  plte=bytes(c for color in colors for c in color[:3]); alpha=bytes(min(255,c[3]*255//128) for c in colors)
  raw=data[pixels:pixels+w*h]; rows=b''.join(b'\0'+raw[y*w:(y+1)*w] for y in range(h))
  png=(b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,3,0,0,0))
       +png_chunk(b'PLTE',plte)+png_chunk(b'tRNS',alpha)+png_chunk(b'IDAT',zlib.compress(rows,9))+png_chunk(b'IEND',b''))
  path=out/name; write_new_or_identical(path,png)
  rw,rh,rgba=png_rgba(path); restored,_=rewrite(data,image,rw,rh,rgba)
  assert restored==data
  results.append(dict(png=str(path),width=w,height=h,image=image,mode='indexed 8-bit, 256 palette entries',
                      exact_roundtrip=True,original_ps2_alpha_values=sorted({c[3] for c in colors}),sha256=digest(png)))
 write_new_or_identical(out/'editing_manifest.json',encode_json(dict(source=str(source),source_sha256=digest(data),images=results)))
 print('PASS: two Photoshop indexed PNGs, both exact no-op roundtrips.')

if __name__=='__main__':main()
