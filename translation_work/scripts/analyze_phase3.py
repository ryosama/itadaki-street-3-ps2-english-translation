"""Bounded static analysis of card text rendering; sources are read-only."""
import csv
import hashlib
import json
import struct
from pathlib import Path
from inspect_mips import Elf

OUT=Path('translation_work/extracted/phase3')
OUT.mkdir(parents=True,exist_ok=True)
elf=Elf('decompile/SLPM_621.12')
b=elf.data
phase2=json.loads(Path('translation_work/extracted/phase2/references.json').read_text(encoding='utf-8-sig'))
targets={0x4175E0:'summary_pointer_table',0x4178DC:'detail_pointer_table_candidate',0x3E7EE8:'current_card_global',0x23C320:'summary_font_object'}
for addr in range(0x4178C8,0x4178F4,4): targets[addr]=f'detail_table_neighbour_{addr:08X}'
for item in phase2['detail_strings_partial']:
    targets[item['vaddr']]=f'detail_{item["offset"]:08X}'
hits=[]
for pc in range(0x100000,0x238594,4):
    w=elf.word(pc)
    if w>>26!=15: continue
    reg=(w>>16)&31
    upper=(w&65535)<<16
    for step in range(1,13):
        q=pc+step*4
        z=elf.word(q)
        op,rs,rt=z>>26,(z>>21)&31,(z>>16)&31
        if rs==reg and op in (9,13,32,33,35,36,37,40,41,43):
            low=z&65535
            value=upper|low if op==13 else (upper+(low if low<32768 else low-65536))&0xffffffff
            if value in targets:
                hits.append(dict(lui_va=f'0x{pc:08X}',use_va=f'0x{q:08X}',target=f'0x{value:08X}',kind=targets[value],instruction=elf.disasm(q,4).strip()))
        # Stop at a recognised write to the upper-half register.
        if rt==reg and op in (9,13,15,32,33,35,36,37): break
        if op==0 and ((z>>11)&31)==reg and (z&63) in (0,2,3,9,33,35,36,37,43,45): break
        if op in (2,3): break

calls=[]
for pc in range(0x100000,0x238594,4):
    w=elf.word(pc)
    if w>>26 in (2,3):
        dest=((pc+4)&0xf0000000)|((w&0x3ffffff)<<2)
        if dest in (0x177F38,0x178038):
            calls.append(dict(va=f'0x{pc:08X}',destination=f'0x{dest:08X}',instruction='jal' if w>>26==3 else 'j'))

widths=[]
for code in range(32,127):
    # Two signed-byte tables used at VA 0x178210 and 0x1782E4.
    before=struct.unpack_from('b',b,elf.offset(0x457380+code-32))[0]
    after=struct.unpack_from('b',b,elf.offset(0x457320+code-32))[0]
    widths.append(dict(code=code,character=chr(code),left_adjust=before,right_advance=after,net_numerator=after-before,scale_denominator=24))
with (OUT/'ascii_metrics.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(widths[0]));writer.writeheader();writer.writerows(widths)
result=dict(source_sha256=hashlib.sha256(b).hexdigest(),address_candidates=hits,renderer_calls=calls,ascii_metrics=widths)
(OUT/'static_analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(address_candidates=len(hits),renderer_calls=len(calls),relevant=[h for h in hits if h['kind']!='summary_font_object']),ensure_ascii=False,indent=2))
