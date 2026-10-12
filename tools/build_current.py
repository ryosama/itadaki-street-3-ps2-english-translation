"""Reproduce exact v13 resource copies and BPS from the original ISO (stdlib).

Never writes an ISO. Private copies go only under ignored work/. Does not need
historical phase artifacts. Different existing outputs are never overwritten.
"""
import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'translation_work/scripts'))
from build_test_patch import digest,encode_json,write_new_or_identical
from build_iso_bps import differences,checksums,number
from reinject_title_png import png_rgba,rewrite

def require(condition,message):
    if not condition:raise ValueError(message)

def hash_iso(path):
    sha=hashlib.sha256();crc=0
    with path.open('rb') as stream:
        while raw:=stream.read(4*1024*1024):sha.update(raw);crc=zlib.crc32(raw,crc)
    return sha.hexdigest(),f'{crc:08x}'

def verify_bps(patch,source,expected):
    """Independent streaming decoder of our SourceRead/TargetRead BPS subset."""
    require(patch[:4]==b'BPS1','BPS signature')
    require(zlib.crc32(patch[:-4])==struct.unpack_from('<I',patch,len(patch)-4)[0],'BPS footer CRC')
    pos=4
    def integer():
        nonlocal pos
        value=0;shift=1
        while True:
            require(pos<len(patch)-12,'truncated BPS integer')
            byte=patch[pos];pos+=1;value+=(byte&127)*shift
            if byte&128:return value
            shift<<=7;value+=shift
    require(integer()==expected['source_size'],'BPS source length')
    total=integer();require(total==expected['target_size'],'BPS target length')
    metadata=integer();pos+=metadata
    sha=hashlib.sha256();crc=0;cursor=0
    with source.open('rb') as stream:
        while cursor<total:
            action=integer();mode=action&3;size=(action>>2)+1
            require(cursor+size<=total,'BPS action overflow')
            if mode==0:
                stream.seek(cursor);left=size
                while left:
                    raw=stream.read(min(left,4*1024*1024));require(bool(raw),'truncated ISO')
                    sha.update(raw);crc=zlib.crc32(raw,crc);left-=len(raw)
            elif mode==1:
                require(pos+size<=len(patch)-12,'BPS literal overflow')
                raw=patch[pos:pos+size];pos+=size;sha.update(raw);crc=zlib.crc32(raw,crc)
            else:raise ValueError('unsupported generated BPS action')
            cursor+=size
    require(pos==len(patch)-12,'BPS trailing command bytes')
    source_crc,target_crc=struct.unpack_from('<II',patch,pos)
    require(f'{source_crc:08x}'==expected['source_crc32'],'BPS source CRC')
    require(f'{target_crc:08x}'==expected['target_crc32']==f'{crc:08x}','BPS target CRC')
    require(sha.hexdigest()==expected['target_sha256'],'decoded BPS target SHA256')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso',type=Path,required=True,help='unpatched SLPM-62112 ISO, read-only')
    parser.add_argument('--output',type=Path,default=ROOT/'work/v13')
    args=parser.parse_args();out=args.output.resolve();source=args.iso.resolve()
    require(out.is_relative_to(ROOT/'work'),'output must be inside this repository/work/')
    recipe=json.loads((ROOT/'data/v13_recipe.json').read_text(encoding='utf-8'))
    require(source.stat().st_size==recipe['source_size'],'wrong original ISO size')
    sha,crc=hash_iso(source)
    require(sha==recipe['source_sha256'] and crc==recipe['source_crc32'],'wrong original ISO revision')
    changes=[];pending=[]
    with source.open('rb') as stream:
        for file in recipe['files']:
            name=Path(file['path'])
            require(not name.is_absolute() and '..' not in name.parts,'unsafe resource path')
            start=file['iso_offset'];size=file['size']
            require(0<=start and start+size<=recipe['source_size'],'invalid ISO extent')
            stream.seek(start);original=stream.read(size)
            require(digest(original)==file['original_sha256'],f'original resource mismatch: {name}')
            edited=bytearray(original)
            if file['mode']=='strings':
                end=0
                for rec in sorted(file['records'],key=lambda r:r['offset']):
                    off=rec['offset'];cap=rec['capacity']
                    require(off>=end and off+cap<=size,'overlapping or out-of-bounds edit');end=off+cap
                    require(digest(original[off:end])==rec['source_span_sha256'],'original span mismatch')
                    if 'payload_hex' in rec:payload=bytes.fromhex(rec['payload_hex'])
                    else:
                        payload=rec['encoded_text'].encode('cp932')+b'\0'
                        require(len(payload)<=cap,'English text exceeds allocation');payload=payload.ljust(cap,b'\0')
                    require(len(payload)==cap,'fixed-size payload mismatch');edited[off:end]=payload
            elif file['mode']=='title_pngs':
                for item in recipe['title_pngs']:
                    png=ROOT/item['path'];require(digest(png.read_bytes())==item['sha256'],'title PNG changed')
                    w,h,rgba=png_rgba(png);raw,info=rewrite(bytes(edited),item['image'],w,h,rgba)
                    require(info.get('max_alpha_rounding_error',0)==0,'title alpha rounding');edited=bytearray(raw)
                require(edited[:80]==original[:80],'title header changed')
            else:raise ValueError('unknown recipe mode')
            require(len(edited)==size and digest(edited)==file['patched_sha256'],f'target mismatch: {name}')
            changes.extend(differences(original,edited,start))
            pending.extend([(out/'original'/name,original),(out/'patched'/name,bytes(edited))])
        changes.sort()
        require(all(a+len(b)<=c for (a,b),(c,d) in zip(changes,changes[1:])),'ISO edits overlap')
        source_sha,target_sha,source_crc,target_crc=checksums(stream,changes,recipe['source_size'])
    require(target_sha==recipe['target_sha256'] and f'{target_crc:08x}'==recipe['target_crc32'],'virtual target mismatch')
    patch=bytearray(b'BPS1'+number(recipe['source_size'])+number(recipe['target_size'])+number(0));cursor=0
    for pos,raw in changes:
        if pos>cursor:patch+=number((pos-cursor-1)<<2)
        patch+=number(((len(raw)-1)<<2)|1)+raw;cursor=pos+len(raw)
    if cursor<recipe['target_size']:patch+=number((recipe['target_size']-cursor-1)<<2)
    patch+=struct.pack('<II',source_crc,target_crc);patch+=struct.pack('<I',zlib.crc32(patch))
    require(digest(patch)==recipe['patch_sha256'],'reproduced BPS differs from published v13')
    verify_bps(bytes(patch),source,recipe)
    for path,raw in pending:write_new_or_identical(path,raw)
    write_new_or_identical(out/'Itadaki_Street_3_English_v13.bps',bytes(patch))
    result=dict(status='PASS',files=len(recipe['files']),iso_written=False,source_sha256=source_sha,
                target_sha256=target_sha,target_crc32=f'{target_crc:08x}',patch_sha256=digest(patch),exact_published_bps=True)
    write_new_or_identical(out/'verification.json',encode_json(result));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
