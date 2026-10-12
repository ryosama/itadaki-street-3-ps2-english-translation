"""Reinject a Photoshop PNG into a NEW TAI01.TI copy; never touch originals.

PNG: noninterlaced RGB/RGBA 8-bit or indexed 1/2/4/8-bit, <=256 RGBA colors.
No approximate RGB quantization: if too many colors, export indexed PNG with
256 colors in Photoshop. PS2 alpha is quantized to its native 0..128 range.
Preserves TI dimensions/descriptors and the other texture byte-for-byte.
Run from project root. --self-test checks both exact no-op roundtrips plus a
one-pixel edit against an independent decode using the extractor.
"""
import argparse
import binascii
import struct
import zlib
from pathlib import Path
from extract_ti import clut_index_ps2,decode_linear
from extract_title_assets import rgba_png
from build_test_patch import digest,encode_json,write_new_or_identical

WORK=Path('translation_work').resolve()
SOURCE=Path('decompile/SYS/TAI01.TI')
OUT=Path('translation_work/phase10/title_assets')

def png_rgba(path):
 data=path.read_bytes()
 if data[:8]!=b'\x89PNG\r\n\x1a\n': raise ValueError('not PNG')
 pos=8; compressed=bytearray(); palette=None; transparency=b''; header=None; ended=False
 while pos<len(data):
  if pos+12>len(data): raise ValueError('truncated PNG chunk')
  count=struct.unpack_from('>I',data,pos)[0]; kind=data[pos+4:pos+8]
  payload=data[pos+8:pos+8+count]; end=pos+12+count
  if end>len(data): raise ValueError('truncated PNG data')
  if binascii.crc32(kind+payload)&0xffffffff!=struct.unpack_from('>I',data,end-4)[0]: raise ValueError('PNG CRC mismatch')
  if kind==b'IHDR':
   if header is not None or count!=13: raise ValueError('bad IHDR')
   header=struct.unpack('>IIBBBBB',payload)
  elif kind==b'PLTE':
   if count%3 or count>768: raise ValueError('bad PNG palette')
   palette=[tuple(payload[i:i+3]) for i in range(0,count,3)]
  elif kind==b'tRNS': transparency=payload
  elif kind==b'IDAT': compressed.extend(payload)
  elif kind==b'IEND': ended=True; break
  elif not kind[0]&32: raise ValueError(f'unsupported critical chunk: {kind}')
  pos=end
 if header is None or not ended: raise ValueError('PNG header/end missing')
 w,h,depth,color,compression,filter_method,interlace=header
 if (w,h) not in ((512,512),(256,256)) or compression or filter_method or interlace:
  raise ValueError('keep original dimensions and export noninterlaced PNG')
 if color==3 and depth in (1,2,4,8): bits=depth; bpp=1
 elif color in (2,6) and depth==8: bits=24 if color==2 else 32; bpp=bits//8
 else: raise ValueError('use 8-bit RGB/RGBA or indexed PNG, not 16-bit/grayscale')
 if color in (2,6) and transparency: raise ValueError('use RGBA for RGB transparency')
 stride=(w*bits+7)//8; expected=(stride+1)*h
 decoder=zlib.decompressobj(); raw=decoder.decompress(bytes(compressed),expected+1)
 if len(raw)!=expected or not decoder.eof: raise ValueError('unexpected decompressed PNG size')
 prev=bytearray(stride); rgba=bytearray()
 for y in range(h):
  begin=y*(stride+1); method=raw[begin]; row=bytearray(raw[begin+1:begin+1+stride])
  if method>4: raise ValueError('unknown PNG filter')
  for i in range(stride):
   a=row[i-bpp] if i>=bpp else 0; b=prev[i]; c=prev[i-bpp] if i>=bpp else 0
   if method==1: add=a
   elif method==2: add=b
   elif method==3: add=(a+b)//2
   elif method==4:
    p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
    add=a if pa<=pb and pa<=pc else b if pb<=pc else c
   else: add=0
   row[i]=(row[i]+add)&255
  if color==6: rgba.extend(row)
  elif color==2:
   for x in range(w): rgba.extend(row[x*3:x*3+3]+b'\xff')
  else:
   if palette is None: raise ValueError('indexed PNG needs a palette')
   for x in range(w):
    ix=(row[x*depth//8]>>(8-depth-(x*depth%8)))&((1<<depth)-1)
    if ix>=len(palette): raise ValueError('PNG palette index out of range')
    rgba.extend((*palette[ix],transparency[ix] if ix<len(transparency) else 255))
  prev=row
 return w,h,bytes(rgba)

def rewrite(data,image,w,h,rgba):
 np,ni=struct.unpack_from('<HH',data,4); header=struct.unpack_from('<I',data,8)[0]
 assert np==ni==2 and header==80 and image in (0,1)
 descriptor=16+16*np+16*image; ew,eh,fmt=struct.unpack_from('<HHH',data,descriptor+2)
 if (w,h)!=(ew,eh) or fmt!=1: raise ValueError('PNG dimensions do not match selected TI texture')
 pal=header+struct.unpack_from('<I',data,16+16*image+8)[0]
 pixels=header+struct.unpack_from('<I',data,descriptor+8)[0]
 palette=[tuple(data[pal+4*i:pal+4*i+4]) for i in range(256)]
 old=decode_linear(palette,data[pixels:pixels+w*h])
 if rgba==old: return data,dict(no_op=True,colors=len({rgba[i:i+4] for i in range(0,len(rgba),4)}))
 colors={}; indexes=bytearray()
 for i in range(0,len(rgba),4):
  color=rgba[i:i+4]
  if color not in colors:
   if len(colors)==256: raise ValueError('More than 256 RGBA colors. Export Indexed Color, 256 colors in Photoshop.')
   colors[color]=len(colors)
  indexes.append(colors[color])
 after=bytearray(data); alpha_error=0
 for color,idx in colors.items():
  r,g,b,a=color; ps2alpha=(a*128+127)//255
  alpha_error=max(alpha_error,abs(a-ps2alpha*255//128))
  slot=pal+4*clut_index_ps2(idx); after[slot:slot+4]=bytes((r,g,b,ps2alpha))
 after[pixels:pixels+w*h]=indexes
 assert len(after)==len(data) and after[:header]==data[:header]
 assert all(i in range(pal,pal+1024) or i in range(pixels,pixels+w*h)
            for i,(a,b) in enumerate(zip(data,after)) if a!=b)
 decoded=decode_linear([tuple(after[pal+4*i:pal+4*i+4]) for i in range(256)],bytes(indexes))
 assert all(decoded[i:i+3]==rgba[i:i+3] for i in range(0,len(rgba),4)), 'RGB roundtrip differs'
 return bytes(after),dict(no_op=False,colors=len(colors),max_alpha_rounding_error=alpha_error,
                         palette_offset=pal,pixel_offset=pixels,width=w,height=h)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--png',type=Path); parser.add_argument('--image',type=int,choices=[0,1],default=0)
 parser.add_argument('--output',type=Path); parser.add_argument('--self-test',action='store_true')
 parser.add_argument('--base',type=Path,help='previous separate TI copy, for editing both textures successively')
 args=parser.parse_args(); data=SOURCE.read_bytes()
 # Check against the extraction metadata, not just a filename.
 import json
 inventory=json.loads((OUT/'texture_inventory.json').read_text(encoding='utf-8'))
 expected=next(r for r in inventory if Path(r['source']).name=='TAI01.TI')['source_sha256']
 if digest(data)!=expected: raise ValueError('original TAI01.TI hash changed')
 if args.self_test:
  results=[]
  for i in (0,1):
   png=OUT/'previews'/f'TAI01_{i:02d}.png'; w,h,rgba=png_rgba(png)
   result,info=rewrite(data,i,w,h,rgba); assert result==data
   # Use an existing second pixel color; this is a synthetic transport test only.
   edited=bytearray(rgba); other=next(rgba[p:p+4] for p in range(4,len(rgba),4) if rgba[p:p+4]!=rgba[:4])
   edited[:4]=other; changed,edit_info=rewrite(data,i,w,h,bytes(edited)); assert changed!=data
   results.append(dict(image=i,exact_unedited_roundtrip=True,synthetic_edit_decode=True))
  write_new_or_identical(OUT/'reinjection_self_test.json',encode_json(dict(status='PASS',source_sha256=digest(data),tests=results)))
  print('PASS: both textures roundtrip exactly; both one-pixel tests decode correctly. No original writes.'); return
 if args.png is None or args.output is None: parser.error('provide --png and --output, or --self-test')
 if not args.png.resolve().is_relative_to(WORK) or not args.output.resolve().is_relative_to(WORK):
  raise ValueError('PNG and output must be inside translation_work')
 if args.output.resolve()==SOURCE.resolve(): raise ValueError('cannot overwrite original')
 original=data
 if args.base:
  if not args.base.resolve().is_relative_to(WORK): raise ValueError('base must be inside translation_work')
  data=args.base.read_bytes()
  if len(data)!=len(original) or data[:80]!=original[:80]: raise ValueError('base has wrong TI header or size')
 w,h,rgba=png_rgba(args.png); result,info=rewrite(data,args.image,w,h,rgba)
 write_new_or_identical(args.output,result)
 write_new_or_identical(args.output.with_suffix('.json'),encode_json(dict(source=str(SOURCE),
     source_sha256=digest(original),base_sha256=digest(data),output_sha256=digest(result),png=str(args.png),image=args.image,**info)))
 assert SOURCE.read_bytes()==original
 print('Created separate TI:',args.output)

if __name__=='__main__':main()
