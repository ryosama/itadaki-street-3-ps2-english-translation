"""Independent whole-file diff and rollback check for the phase 4 ELF copy."""
import hashlib
import json
import struct
from pathlib import Path
from message_format import tokenize

root=Path('translation_work/phase4')
manifest=json.loads((root/'patch_manifest.json').read_text(encoding='utf-8'))
source=Path(manifest['source']).read_bytes()
patched=(root/'patched/SLPM_621.12').read_bytes()
assert len(source)==len(patched)==manifest['source_size']
assert hashlib.sha256(source).hexdigest()==manifest['source_sha256']
assert hashlib.sha256(patched).hexdigest()==manifest['patched_sha256']
restored=bytearray(patched)
ranges=set()
reference_info=[]
for patch in manifest['patches']:
    old=bytes.fromhex(patch['original_hex'])
    new=bytes.fromhex(patch['patched_hex'])
    start=patch['file_offset']
    assert len(old)==len(new)==patch['original_capacity_including_nul']
    assert source[start:start+len(old)]==old
    assert patched[start:start+len(new)]==new
    assert new.endswith(b'\0')
    assert not ranges.intersection(range(start,start+len(old)))
    ranges.update(range(start,start+len(old)))
    restored[start:start+len(old)]=old
    refs=[o for o in range(0x13CB00,0x34A1DC,4) if struct.unpack_from('<I',source,o)[0]==patch['virtual_address']]
    entry=dict(kind=patch['kind'],file_offset_hex=patch['file_offset_hex'],pointer_references_in_data=[f'0x{o:08X}' for o in refs])
    if patch['kind']=='detail':
        original_tokens=[t for t in tokenize(patch['original_text']) if t['kind']!='literal']
        patched_tokens=[t for t in tokenize(patch['replacement_text']) if t['kind']!='literal']
        assert original_tokens==patched_tokens==patch['dynamic_commands']
        # Table endpoint remains unknown: these are candidate IDs based on known stride.
        entry['candidate_detail_ids']=[(o-4-0x3188D8)//8 for o in refs if o>=0x3188DC and (o-4-0x3188D8)%8==0]
    reference_info.append(entry)
changed=[i for i,(a,b) in enumerate(zip(source,patched)) if a!=b]
assert changed==manifest['changed_offsets']
assert len(changed)==manifest['changed_byte_count']==81
assert all(i in ranges for i in changed)
assert bytes(restored)==source  # Every patched byte can be restored from the manifest.
assert patched[0x3185E0:0x3188C8]==source[0x3185E0:0x3188C8]
result=dict(binary_diff_verified=True,restoration_verified=True,runtime_verified=False,pointer_references=reference_info)
(root/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
