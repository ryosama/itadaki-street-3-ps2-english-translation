"""Targeted read-only search: menu strings and executable transitions (stdlib)."""
import json
import struct
import sys
from pathlib import Path
from inspect_mips import Elf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'translation_work/extracted/phase5'
TERMS = ['フリープレイ', '家庭教師モード', 'トーナメント', '育成モード',
         'いただきクエスト', 'データをみる', 'ルール説明', 'ゲームをおわる',
         'ひとり', 'ふたり', 'さんにん', 'よにん', '記録を見る', '記録を消す',
         'データロード', 'データセーブ', '何人で', 'どれに',
         'みんなで', 'MOVIE.ELF', 'SLPM_621.12']


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for name in ('SLPM_621.12', 'MOVIE.ELF'):
        elf = Elf(ROOT / 'decompile' / name)
        data = elf.data
        matches = []
        targets = {}
        for term in TERMS:
            needle = term.encode('cp932')
            pos = 0
            while (pos := data.find(needle, pos)) >= 0:
                start = data.rfind(b'\0', max(0, pos-500), pos) + 1
                end = data.find(b'\0', pos)
                try:
                    value = data[start:end].decode('cp932')
                except UnicodeDecodeError:
                    value = data[start:end].decode('cp932', errors='replace')
                va = start + 0xff000
                pointers = [off for off in range(0, len(data)-3, 4)
                            if data[off:off+4] == struct.pack('<I', va)]
                item = dict(term=term, match_offset=pos, offset=start, va=va,
                            text=value, pointer_offsets=pointers)
                matches.append(item)
                targets[va] = value
                pos += len(needle)
        hits = []
        # Existing main .text bounds only; no full game decompilation.
        if name == 'SLPM_621.12':
            for off in (0x300cf8, 0x2ff6e0, 0x2ffecc, 0x31aa20):
                targets[off+0xff000] = f'table_file_{off:08X}'
            for pc in range(0x100000, 0x238594, 4):
                w = elf.word(pc)
                if w >> 26 != 15:
                    continue
                reg, upper = (w >> 16) & 31, (w & 65535) << 16
                for step in range(1, 13):
                    q = pc + step * 4
                    z = elf.word(q)
                    op, rs, rt = z >> 26, (z >> 21) & 31, (z >> 16) & 31
                    if rs == reg and op in (9,13,32,33,35,36,37,40,41,43):
                        low = z & 65535
                        value = upper | low if op == 13 else (upper + (low if low < 32768 else low-65536)) & 0xffffffff
                        if value in targets:
                            hits.append(dict(lui_va=pc, use_va=q, target=value, text=targets[value]))
                            (OUT / f'{name}_{q:08X}.asm').write_text(elf.disasm(max(0x100000, pc-0x80), 0x200), encoding='utf-8')
                    if rt == reg and op in (9,13,15,32,33,35,36,37):
                        break
                    if op == 0 and (z >> 11) & 31 == reg and z & 63 in (0,2,3,9,33,35,36,37,43,45):
                        break
                    if op in (2,3):
                        break
        results.append(dict(file=name, strings=matches, address_candidates=hits))
    (OUT / 'targeted_analysis.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    for result in results:
        print(result['file'])
        for item in result['strings']:
            print(f"{item['offset']:08X} VA={item['va']:08X} refs={[hex(x) for x in item['pointer_offsets']]} {item['text']!r}")
        print('Code candidates:', result['address_candidates'])


if __name__ == '__main__':
    main()
