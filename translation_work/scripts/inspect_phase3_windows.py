"""Save bounded evidence windows and font-object data for phase 3."""
import json
import struct
from pathlib import Path
from inspect_mips import Elf

elf=Elf('decompile/SLPM_621.12')
out=Path('translation_work/extracted/phase3')
out.mkdir(parents=True,exist_ok=True)
windows={
    'summary_renderer':(0x177F38,0x440),
    'summary_consumer':(0x138980,0x350),
    'font_init_caller':(0x101010,0x130),
    'nearby_text_wrappers':(0x1785C0,0x640),
    'card_dispatch_candidate':(0x18F740,0xA00),
    'font_constructor':(0x178510,0x78),
    'detail_consumer':(0x1A1260,0x154),
    'detail_format_wrapper':(0x136E98,0x194),
    'detail_formatter':(0x136AC0,0x3D8),
}
for name,(start,size) in windows.items():
    (out/f'{name}.asm').write_text(elf.disasm(start,size),encoding='utf-8')
data=elf.data
obj=0x23C320
vtable=0x4570B0 # Installee par 0x17853C..0x178548; objet initialement nul.
print(f'font_object={obj:08X} vtable={vtable:08X}')
result={'font_object_va':obj,'vtable_va':vtable,'object_words':[],'vtable_words':[]}
for offset in range(0,96,4):result['object_words'].append(dict(offset=offset,value=elf.word(obj+offset)))
if vtable:
    for offset in range(0,64,4):result['vtable_words'].append(dict(offset=offset,value=elf.word(vtable+offset)))
    decode_target=elf.word(vtable+12)
    print(f'decode_callback={decode_target:08X}')
    (out/'font_decode_callback.asm').write_text(elf.disasm(decode_target,0x340),encoding='utf-8')
(out/'font_object.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
