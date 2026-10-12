"""Tokenize the confirmed 0x136AC0 message-format state machine.

Standard library, read-only sources. This models normal/literal modes and
the 11 ASCII command letters; it does not execute game callbacks or patch ELF.
"""
import json
from pathlib import Path

COMMANDS = {'P':('player',0),'p':('player',1),'G':('integer',0),'g':('integer',1),
            'S':('shop',0),'s':('shop',1),'E':('district',0),'e':('district',1)}
OPEN='『'.encode('cp932')
CLOSE='』'.encode('cp932')

def tokenize(text):
    raw=text.encode('cp932')
    out=[];literal=False;i=0;buffer=bytearray()
    def flush():
        if buffer:
            out.append(dict(kind='literal',text=buffer.decode('cp932')))
            buffer.clear()
    while i<len(raw):
        if not literal and raw[i:i+2]==OPEN:
            flush();literal=True;i+=2;continue
        if literal and raw[i:i+2]==CLOSE:
            flush();literal=False;i+=2;continue
        byte=raw[i]
        ch=chr(byte)
        if not literal and ch in COMMANDS:
            flush();kind,index=COMMANDS[ch]
            out.append(dict(kind=kind,index=index,command=ch));i+=1;continue
        if not literal and ch in 'ABC':
            flush()
            if i+1>=len(raw) or not 48<=raw[i+1]<=57:
                raise ValueError(f'{ch} expects a decimal selector byte at offset {i+1}')
            out.append(dict(kind='selector',index=ord(ch)-ord('A'),value=raw[i+1]-48,command=ch))
            i+=2;continue
        size=2 if byte>=128 else 1
        if i+size>len(raw): raise ValueError('truncated two-byte character')
        buffer.extend(raw[i:i+size]);i+=size
    flush()
    if literal: raise ValueError('unterminated literal region')
    return out

def escape_literal(text):
    """Quote a literal segment for the detailed formatter, not summary renderer."""
    if '『' in text or '』' in text: raise ValueError('nested delimiter not supported')
    text.encode('cp932')
    return '『'+text+'』'

def main():
    root=Path('translation_work')
    src=json.loads((root/'extracted/phase2/references.json').read_text(encoding='utf-8-sig'))
    records=[]
    for r in src['detail_strings_partial']:
        record=dict(file_offset=r['offset'],virtual_address=r['vaddr'],text_ja=r['text'])
        try: record['tokens']=tokenize(r['text'])
        except ValueError as exc: record['error']=str(exc)
        records.append(record)
    dest=root/'extracted/phase3/detail_token_audit.json'
    dest.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Audited {len(records)} bounded messages; errors={sum("error" in r for r in records)}')
    assert tokenize('G『G』')[0]['kind']=='integer'
    assert tokenize('G『G』')[1]['text']=='G'
    assert tokenize(escape_literal('Pay 30G'))==[dict(kind='literal',text='Pay 30G')]
    assert tokenize('%%')==[dict(kind='literal',text='%%')]
    assert tokenize('A2P')[0]['value']==2
    print('Literal escaping, numeric marker, selector and percent checks OK')

if __name__=='__main__': main()
