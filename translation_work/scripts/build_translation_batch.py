"""Build a bounded, reversible English test ELF, using only the standard library.

Run from the project root. Reads originals and previous test copy; writes only
new phase6 outputs. Refuses unexpected source hashes, oversized strings, changed
formatter commands, overlap, pointer changes, or different existing outputs.
No relocation, ISO rebuilding, emulator/save changes or source edits.
Translation/layout decisions are recorded individually, including rejected drafts.
"""
from __future__ import annotations
import csv
import io
import json
import re
import struct
from collections import Counter
from pathlib import Path
from build_test_patch import EXPECTED_SHA, digest, encode_json, write_new_or_identical
from message_format import tokenize, escape_literal

ROOT = Path('translation_work')
SOURCE = Path('decompile/SLPM_621.12')
BASE = ROOT/'phase5/revision3/patched/SLPM_621.12'
BASE_SHA = '7ca5c38cfb1c629a91abbe3a78e4d2f54fbad0bacd8c5e62ba702d3cfbb0501c'
OUT = ROOT/'phase6/revision3'
PRINTF = re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs])')
PLACEHOLDER = re.compile(r'\{([PpGgSsEe])\}')

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def signature(text):
    return [t for t in tokenize(text) if t['kind'] != 'literal']

def encode_template(template):
    """Protect reserved formatter letters in every literal English fragment."""
    output=[]
    cursor=0
    for match in PLACEHOLDER.finditer(template):
        fragment=template[cursor:match.start()]
        if fragment:
            output.append(escape_literal(fragment))
        output.append(match.group(1))
        cursor=match.end()
    if template[cursor:]:
        output.append(escape_literal(template[cursor:]))
    return ''.join(output)

def main():
    original=SOURCE.read_bytes()
    base=BASE.read_bytes()
    assert digest(original)==EXPECTED_SHA, 'unexpected original ELF'
    assert digest(base)==BASE_SHA, 'unexpected baseline ELF'
    assert len(base)==len(original)
    patched=bytearray(base)
    catalog=[]
    patches=[]
    regions=set()
    seen={}
    overrides=read_json(ROOT/'translations/compact_overrides_en.json')

    def add(kind, identifier, offset, english, encoded, issues, full=None):
        end=original.index(b'\0',offset)
        raw=original[offset:end]
        japanese=raw.decode('cp932')
        capacity=len(raw)+1
        payload=encoded.encode('cp932')
        assert b'\0' not in payload
        reasons=list(issues)
        if len(payload)+1>capacity:
            reasons.append('insufficient_bytes')
        entry=dict(kind=kind,id=str(identifier),offset=offset,offset_hex=f'0x{offset:08X}',
                   japanese=japanese,english=english,full_english=full or english,
                   encoded_text=encoded,capacity=capacity,required_bytes=len(payload)+1,
                   review='draft; semantic and in-game layout review required',reasons=reasons)
        if reasons:
            entry['status']='draft_not_integrated'
        else:
            after=payload+b'\0'*(capacity-len(payload))
            if offset in seen:
                assert seen[offset]==after, 'inconsistent shared summary'
                entry['status']='integrated_shared'
            else:
                region=set(range(offset,end+1))
                assert not regions&region, 'overlapping translation ranges'
                regions.update(region)
                seen[offset]=after
                patches.append(dict(kind=kind,id=str(identifier),offset=offset,capacity=capacity,
                                    original_hex=original[offset:end+1].hex(),
                                    before_hex=base[offset:end+1].hex(),after_hex=after.hex(),
                                    english=english,encoded_text=encoded))
                patched[offset:end+1]=after
                entry['status']='integrated'
        catalog.append(entry)

    cards=read_json(ROOT/'translations/cards_en.json')
    records=read_json(ROOT/'extracted/card_text_ja.json')
    assert set(cards)=={str(r['card_number']) for r in records if r['file_offset'] is not None}
    for record in records:
        if record['file_offset'] is None:
            continue
        number=record['card_number']
        full, compact=cards[str(number)]
        compact=overrides['card_summary'].get(str(number),compact)
        lines=compact.split('\n')
        issues=[] if len(lines)<=3 and max(map(len,lines))<=8 else ['summary_layout_budget']
        add('card_summary',number,record['file_offset'],compact,compact,issues,full)

    details=read_json(ROOT/'translations/details_en.json')
    audit=read_json(ROOT/'extracted/phase3/detail_token_audit.json')
    assert len(audit)==119 and set(details)=={str(i) for i in range(119)}
    detail_ids={}
    for table_id in range(143):
        pointer=struct.unpack_from('<I',original,0x3188DC+8*table_id)[0]
        offset=pointer-0xFF000
        assert 0x36AA48<=offset<0x36C330
        detail_ids.setdefault(offset,[]).append(table_id)
    extras=read_json(ROOT/'translations/details_extra_en.json')
    combined=[(str(index),r,details[str(index)]) for index,r in enumerate(audit)]
    for off,template in extras.items():
        offset=int(off,16)
        combined.append((off,dict(file_offset=offset,text_ja=original[offset:original.index(b'\0',offset)].decode('cp932')),template))
    assert {r['file_offset'] for _,r,_ in combined}==set(detail_ids)
    for index,record,template in combined:
        offset=record['file_offset']
        assert offset in detail_ids
        full_template=template
        template=overrides['card_detail'].get(index,template)
        encoded=encode_template(template)
        issues=[]
        if signature(record['text_ja'])!=signature(encoded):
            issues.append('formatter_command_mismatch')
        if record['text_ja'].count('%%')!=template.count('%%'):
            issues.append('percent_escape_mismatch')
        if index in ('10','11','12'):
            issues.append('original_unquoted_G_needs_investigation')
        # Approximate static layout only; actual player/shop names vary.
        widths={'P':8,'p':8,'G':4,'g':4,'S':12,'s':12,'E':8,'e':8}
        estimated=PLACEHOLDER.sub(lambda m:'X'*widths[m.group(1)],template)
        if len(estimated.split('\n'))>3 or max(map(len,estimated.split('\n')))>24:
            issues.append('detail_layout_budget')
        add('card_detail',index,offset,template,encoded,issues,full_template)
        catalog[-1]['detail_table_ids']=detail_ids[offset]

    # Plain save/load UI uses PS2 and MEMORY CARD without custom formatter
    # escaping in the original. Retain printf argument types/order and %%.
    for off,english in read_json(ROOT/'translations/save_ui_en.json').items():
        offset=int(off,16)
        assert 0x359128<=offset<0x359800 and offset%4==0
        old=original[offset:original.index(b'\0',offset)].decode('cp932')
        issues=[]
        if PRINTF.findall(old)!=PRINTF.findall(english):
            issues.append('printf_signature_mismatch')
        if max(map(len,english.split('\n')))>18 or len(english.split('\n'))>5:
            issues.append('ui_layout_budget')
        add('save_load_ui',off,offset,english,english,issues)

    # Seen directly in PCSX2: six newline-separated labels and one description.
    for off,english in read_json(ROOT/'translations/training_ui_en.json').items():
        offset=int(off,16)
        assert offset in (0x3601D8,0x360BB8)
        old=original[offset:original.index(b'\0',offset)].decode('cp932')
        issues=[]
        if offset==0x3601D8:
            if len(english.split('\n'))!=len(old.split('\n')) or max(map(len,english.split('\n')))>6:
                issues.append('training_label_layout')
        elif len(english.split('\n'))>3 or max(map(len,english.split('\n')))>18:
            issues.append('training_description_layout')
        add('training_ui',off,offset,english,english,issues)

    changed=[i for i,(a,b) in enumerate(zip(base,patched)) if a!=b]
    assert changed and all(i in regions for i in changed)
    assert len(patched)==len(original)
    for start,end in ((0x3185E0,0x3188C8),(0x3188D8,0x3188D8+143*8)):
        assert original[start:end]==patched[start:end], 'pointer/type tables changed'
    restored=bytearray(patched)
    for p in patches:
        restored[p['offset']:p['offset']+p['capacity']]=bytes.fromhex(p['before_hex'])
    assert restored==base, 'rollback to baseline failed'
    assert SOURCE.read_bytes()==original and BASE.read_bytes()==base
    counts=Counter((c['kind'],c['status']) for c in catalog)
    stats={kind:dict(total=sum(1 for c in catalog if c['kind']==kind),
                     integrated=sum(1 for c in catalog if c['kind']==kind and c['status'].startswith('integrated')),
                     drafts=sum(1 for c in catalog if c['kind']==kind and c['status']=='draft_not_integrated'))
           for kind in ('card_summary','card_detail','save_load_ui','training_ui')}
    manifest=dict(source=str(SOURCE),base=str(BASE),source_sha256=digest(original),
                  base_sha256=digest(base),patched_sha256=digest(patched),
                  file_size=len(patched),changed_bytes_from_base=len(changed),
                  unique_allocations=len(patches),stats=stats,patches=patches)
    write_new_or_identical(OUT/'patched/SLPM_621.12',bytes(patched))
    write_new_or_identical(OUT/'translation_manifest.json',encode_json(manifest))
    write_new_or_identical(OUT/'translation_catalog.json',encode_json(catalog))
    stream=io.StringIO(newline='')
    fields=['kind','id','offset_hex','status','capacity','required_bytes','japanese',
            'full_english','english','reasons','review']
    writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader()
    for c in catalog:
        writer.writerow({f:('; '.join(c[f]) if f=='reasons' else c[f]) for f in fields})
    write_new_or_identical(OUT/'translation_catalog.csv',stream.getvalue().encode('utf-8-sig'))
    print(json.dumps(dict(stats=stats,sha256=digest(patched),changed_bytes=len(changed)),indent=2))

if __name__=='__main__':
    main()
