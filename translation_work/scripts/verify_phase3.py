"""Check key static conclusions against original ELF words and dispatch tables."""
import json
import hashlib
from pathlib import Path
from inspect_mips import Elf
from message_format import tokenize

elf=Elf('decompile/SLPM_621.12')
assert hashlib.sha256(elf.data).hexdigest()=='d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5'
assert elf.word(0x1780E0)==0x12200099  # null guard before text dereference
assert elf.word(0x1780F0)==0x82220000  # first byte load
assert elf.word(0x178374)==0x27BD00F0 # null target returns through epilogue
assert elf.word(0x4175E0+45*4)==0     # C046 is the null slot
tables=json.loads(Path('translation_work/extracted/phase3/format_tables.json').read_text(encoding='utf-8'))
letters={r['character'] for r in tables['character_dispatch'] if r['code']}
assert letters==set('ABCEGPSegps')
assert elf.data[elf.offset(0x4B7B78):elf.offset(0x4B7B78)+6]==bytes.fromhex('817700008178')
assert tables['numeric_format']['text']=='%d'
audit=json.loads(Path('translation_work/extracted/phase3/detail_token_audit.json').read_text(encoding='utf-8'))
assert len(audit)==119 and not any('error' in r for r in audit)
assert tokenize('G『G』')==[{'kind':'integer','index':0,'command':'G'},{'kind':'literal','text':'G'}]
print('OK: source hash, C046 null path, 11 command letters, delimiters and 119 message audits checked.')
