"""Read-only inventory of opponent strings, pointer references and UI candidates.

Run from the project root. Writes only translation_work/phase13/analysis.
Uses CP932 and little-endian 32-bit ELF data pointers, no full decompilation.
"""
import json
import struct
from pathlib import Path
from build_test_patch import encode_json, write_new_or_identical

ROOT = Path('translation_work')
ORIGINAL = Path('decompile/SLPM_621.12')

def main():
    data = ORIGINAL.read_bytes()
    base = (ROOT/'phase12/revision1/patched/SLPM_621.12').read_bytes()
    rows = []
    for lo, hi in [(0x368898, 0x368D38), (0x3B9C88, 0x3B9D98)]:
        pos = lo
        while pos < hi:
            end = data.index(b'\0', pos, hi)
            raw = data[pos:end]
            try:
                text = raw.decode('cp932')
            except UnicodeError:
                text = ''
            if text and all(c.isprintable() or c in '\n\u3000' for c in text):
                pointer = struct.pack('<I', pos + 0xFF000)
                refs = [i for i in range(0x139594, len(data)-3, 4) if data[i:i+4] == pointer]
                rows.append(dict(offset=hex(pos), size=end-pos+1, japanese=text,
                                 current=base[pos:end].split(b'\0')[0].decode('cp932'),
                                 references=[hex(i) for i in refs]))
                print(hex(pos), end-pos+1, repr(text), 'refs', ','.join(hex(i) for i in refs))
            pos = end+1
    needles = ['あなたの', '未登録', '強さランク', '出身', '仕事', '趣味', '勝率', 'ランク',
               '優勝', '総合', '試合数', '勝ち点', '参加', '%s才', '%sくん', '%sさん']
    hits = []
    for needle in needles:
        raw = needle.encode('cp932'); pos = 0
        while (off := data.find(raw, pos)) >= 0:
            pos = off+1
            if off < 0x139594:
                continue
            start = data.rfind(b'\0', max(0,off-160), off)+1
            end = data.find(b'\0',off)
            try:
                text = data[start:end].decode('cp932')
            except UnicodeError:
                continue
            if all(c.isprintable() or c in '\n\u3000' for c in text):
                hit = dict(needle=needle, offset=hex(start), size=end-start+1, japanese=text,
                           current=base[start:end].split(b'\0')[0].decode('cp932',errors='replace'))
                if hit not in hits:
                    hits.append(hit)
                    print('UI',hex(start),end-start+1,repr(text),repr(hit['current']))
    write_new_or_identical(ROOT/'phase13/analysis/opponent_inventory.json',encode_json(rows))
    write_new_or_identical(ROOT/'phase13/analysis/ui_candidates.json',encode_json(hits))

if __name__ == '__main__':
    main()
