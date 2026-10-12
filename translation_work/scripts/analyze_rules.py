"""Read-only bounded Rules text/table discovery. Stdlib; writes work files only."""
import json
import struct
from pathlib import Path
from inspect_mips import Elf
from build_test_patch import encode_json, write_new_or_identical

OUT=Path('translation_work/extracted/phase7')

def main():
    elf=Elf('decompile/SLPM_621.12')
    b=elf.data
    records=[]
    p=0x36CB48
    while p<0x36D7C8:
        end=b.index(b'\0',p)
        if end>p:
            text=b[p:end].decode('cp932')
            assert all(c.isprintable() or c=='\n' for c in text)
            records.append(dict(offset=p,va=p+0xFF000,japanese=text,capacity=end-p+1,refs=[]))
        p=end+1
    targets={r['va']:r for r in records}
    for off in range(0,len(b)-3,4):
        value=struct.unpack_from('<I',b,off)[0]
        if value in targets:
            targets[value]['refs'].append(off)
    tables={off+0xFF000 for r in records for off in r['refs']}
    # Include addresses of tables surrounding the Rules pointer references.
    table_region=[off for r in records for off in r['refs'] if 0x200000<off<0x350000]
    if table_region:
        tables.update(range((min(table_region)&~255)+0xFF000,(max(table_region)+256)+0xFF000,4))
    hits=[]
    for pc in range(0x100000,0x238594,4):
        w=elf.word(pc)
        if w>>26!=15: continue
        reg=(w>>16)&31; upper=(w&65535)<<16
        for step in range(1,10):
            q=pc+step*4; z=elf.word(q)
            op=z>>26; rs=(z>>21)&31; rt=(z>>16)&31; low=z&65535
            if rs==reg and op in (9,13,35,43):
                value=(upper|low) if op==13 else (upper+(low if low<32768 else low-65536))&0xFFFFFFFF
                if value in targets or value in tables:
                    hits.append(dict(pc=pc,use=q,address=value))
                    write_new_or_identical(OUT/f'rules_consumer_{q:08X}.asm',elf.disasm(max(0x100000,pc-0x60),0x180).encode())
            if rt==reg and op in (9,13,15,32,33,35,36,37): break
            if op in (2,3): break
    write_new_or_identical(OUT/'rules_discovery.json',encode_json(dict(records=records,code_candidates=hits)))
    for r in records:
        print(hex(r['offset']),r['capacity'],[hex(x) for x in r['refs']],repr(r['japanese']))
    print('CODE',hits)

if __name__=='__main__': main()
