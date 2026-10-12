"""Extract static evidence for the detailed-message state machine and fonts."""
import json
import struct
from pathlib import Path
from inspect_mips import Elf

elf=Elf('decompile/SLPM_621.12')
out=Path('translation_work/extracted/phase3')
out.mkdir(parents=True,exist_ok=True)
chars=[]
for code in range(116):
    target=elf.word(0x44DA70+code*4)
    if target!=0x136B88: chars.append(dict(code=code,character=chr(code),handler_va=f'0x{target:08X}'))
states=[dict(state=i,handler_va=f'0x{elf.word(0x44DA30+i*4):08X}') for i in range(13)]
glyph=[elf.word(0x30CDC8+i*4) for i in range(4)]
def string(va):
    start=elf.offset(va);end=elf.data.index(b'\0',start)
    return dict(va=f'0x{va:08X}',raw_hex=elf.data[start:end].hex(),text=elf.data[start:end].decode('cp932'))
result=dict(character_dispatch=chars,state_dispatch=states,glyph_callbacks=[f'0x{x:08X}' for x in glyph],numeric_format=string(0x4B7B80),delimiter_bytes=elf.data[elf.offset(0x4B7B78):elf.offset(0x4B7B78)+8].hex())
(out/'format_tables.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'glyph_decoder_24.asm').write_text(elf.disasm(glyph[1],0x300),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
