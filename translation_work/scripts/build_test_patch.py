"""Create a four-string experimental English ELF copy, standard library only.

Run from the project root. Only translation_work/phase4 outputs are written.
Checks exact original SHA-256, expected strings, capacities, parameter tokens,
nonoverlapping ranges, full binary diff, unchanged pointer table and source hash.
No ISO processing or modifications to original files are performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from extract_card_text import extract
from message_format import tokenize

EXPECTED_SHA = 'd6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5'
SOURCE = Path('decompile/SLPM_621.12')
OUT = Path('translation_work/phase4')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write_new_or_identical(path, data):
    """Do not silently overwrite any existing, different work artifact."""
    if path.exists():
        if path.read_bytes()!=data:
            raise FileExistsError(f'{path} already exists with different contents')
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def encode_json(obj):
    return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def command_signature(text):
    return [t for t in tokenize(text) if t['kind']!='literal']

def build():
    source=SOURCE.resolve()
    root=Path('translation_work').resolve()
    destination=(OUT/'patched/SLPM_621.12').resolve()
    if not destination.is_relative_to(root) or destination==source:
        raise ValueError('output must be a separate translation_work file')
    original=source.read_bytes()
    if digest(original)!=EXPECTED_SHA:
        raise ValueError('unexpected source ELF; no output written')
    records=extract(source)
    replacements=[
        dict(kind='summary',card=1,text='Change\ncourse!'),
        dict(kind='summary',card=2,text='Roll\nagain!'),
        dict(kind='summary',card=33,text='Sell at\n3x value'),
        dict(kind='detail',offset=0x36AD30,text='P『 gets 』G『G!』',expected='Pさん\nG『G』の 収入!'),
    ]
    patched=bytearray(original)
    manifest=[]
    allowed=set()
    for item in replacements:
        if item['kind']=='summary':
            rec=records[item['card']-1]
            start=rec['file_offset']
            if start is None: raise ValueError('cannot overwrite a NULL card slot')
            old_text=rec['text_ja']
        else:
            start=item['offset']
            old_text=item['expected']
        end=original.index(b'\0',start)
        old=original[start:end]
        if old.decode('cp932')!=old_text:
            raise ValueError(f'expected text mismatch at {start:X}')
        replacement=item['text'].encode('cp932')
        if b'\0' in replacement or len(replacement)>len(old):
            raise ValueError(f'replacement exceeds original capacity at {start:X}')
        if item['kind']=='detail':
            if command_signature(old_text)!=command_signature(item['text']):
                raise ValueError('dynamic command signature changed')
        after=replacement+b'\0'*(len(old)+1-len(replacement))
        region=set(range(start,end+1))
        if allowed&region: raise ValueError('overlapping patches')
        allowed.update(region)
        patched[start:end+1]=after
        entry=dict(kind=item['kind'],card_number=item.get('card'),file_offset=start,
                   file_offset_hex=f'0x{start:08X}',virtual_address=start+0xFF000,
                   original_text=old_text,replacement_text=item['text'],original_hex=(old+b'\0').hex(),
                   patched_hex=after.hex(),original_capacity_including_nul=len(old)+1,
                   replacement_bytes_including_nul=len(replacement)+1)
        if item['kind']=='summary':
            entry['line_characters']=[len(line) for line in item['text'].split('\n')]
            entry['fixed_24px_line_width_estimates']=[24*n for n in entry['line_characters']]
        else:
            entry['dynamic_commands']=command_signature(item['text'])
        manifest.append(entry)
    changed=[i for i,(a,b) in enumerate(zip(original,patched)) if a!=b]
    if not changed or any(i not in allowed for i in changed):
        raise ValueError('unexpected binary changes')
    if len(patched)!=len(original): raise ValueError('ELF size changed')
    # Full 186-pointer table and all data outside the four ranges must match.
    if patched[0x3185E0:0x3188C8]!=original[0x3185E0:0x3188C8]:
        raise ValueError('pointer table changed')
    detail=tokenize(replacements[-1]['text'])
    # Stress example only: 64 ASCII name bytes and signed int32 minimum.
    expanded=''.join(t['text'] if t['kind']=='literal' else 'N'*64 if t['kind']=='player' else '-2147483648' for t in detail)
    report=dict(source=str(SOURCE),source_sha256=digest(original),patched_sha256=digest(patched),
                source_size=len(original),patched_size=len(patched),changed_byte_count=len(changed),
                changed_offsets=changed,pointer_table_unchanged=True,patches=manifest,
                detail_simulated_expansion=dict(player_name='N'*64,integer=-2147483648,
                    result=expanded,bytes_including_nul=len(expanded.encode('cp932'))+1,
                    note='Hypothetical stress scenario, not an established game maximum'),
                runtime_verified=False)
    write_new_or_identical(destination,bytes(patched))
    # Re-read produced bytes and verify all decoded summary slots.
    if destination.read_bytes()!=bytes(patched): raise ValueError('output readback failed')
    actual=extract(destination)
    by_card={r['card']:r['text'] for r in replacements if r['kind']=='summary'}
    for before,after in zip(records,actual):
        expected=by_card.get(before['card_number'],before['text_ja'])
        if after['text_ja']!=expected or after['virtual_address']!=before['virtual_address']:
            raise ValueError('summary readback/pointer mismatch')
    if digest(source.read_bytes())!=EXPECTED_SHA: raise ValueError('source changed during build')
    write_new_or_identical(OUT/'patch_manifest.json',encode_json(report))
    write_new_or_identical(OUT/'patched_card_text.json',encode_json(actual))
    print(f'Created/verified {destination}')
    print(f'{len(manifest)} strings, {len(changed)} changed bytes, {len(patched)} total bytes; source and all pointers unchanged.')
    print(f'Patched SHA-256: {digest(patched)}')
    return report

if __name__=='__main__': build()
