"""Translate the captured menu on a COPY, retaining phase-4 card tests.

Standard library only. Fixed allocations, no pointer changes. One documented
menu-font instruction changes the menu-list font size from 20 to 16.
Outputs include original bytes for exact rollback and a reviewable CSV.
Some labels are shared with other menus; all aligned references are recorded.
The short player labels respect the original tiny byte allocations.
"""
import csv
import hashlib
import io
import struct
from pathlib import Path
from build_test_patch import EXPECTED_SHA, write_new_or_identical, encode_json
from inspect_mips import Elf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'translation_work/phase5/revision3'


def main():
    original = (ROOT / 'decompile/SLPM_621.12').read_bytes()
    assert hashlib.sha256(original).hexdigest() == EXPECTED_SHA
    base = (ROOT / 'translation_work/phase4/patched/SLPM_621.12').read_bytes()
    assert hashlib.sha256(base).hexdigest() == 'e4c1917834ca50c6b2ab4326a01bd096e1df5a91c9b6d63b44aef5e8835f685d'
    jobs = []
    tables = [
        ('main_label', 0x300CF8,
         ['フリープレイ\n', '家庭教師モード\n', 'トーナメント\n', '育成モード\n',
          'いただきクエスト\n', 'データをみる\n', 'ルール説明\n', 'ゲームをおわる'],
         ['Free Play\n', 'Tutor Mode\n', 'Tournament\n', 'Training\n',
          'Quest\n', 'Records\n', 'Rules\n', 'Quit Game']),
        ('player_label', 0x2FF6E0, ['ひとり\n', 'ふたり\n', 'さんにん\n', 'よにん\n'],
         ['1P\n', '2P\n', '3P\n', '4P\n']),
        ('data_label', 0x2FFECC, ['記録を見る\n', '記録を消す\n', 'データロード\n', 'データセーブ'],
         ['View\n', 'Erase\n', 'Load\n', 'Save']),
        ('main_description', 0x31AA20,
         ['みんなで 対戦もできる\nゲームモードです。',
          '家庭教師の先生に\nいろいろ 教えてもらえる\nゲームモードです。',
          'ひとりで 遊ぶ\n勝ち抜き形式の\nゲームモードです。',
          'キャラクターを 育てて遊べる\nゲームモードです。',
          'いろいろな 場面からの\nクリアを めざす\nゲームモードです。',
          'いままでの ゲーム成績を\n見ることが できます。',
          'いただきストリートの\nゲームの説明を\n聞くことが できます。',
          'いただきストリートを\nおわります。'],
         ['Play a game\nwith friends\nor the CPU.',
          'Learn to play\nwith your tutor.',
          'Play solo in\na knockout\ntournament.',
          'Train your\ncharacter\nas you play.',
          'Clear goals in\nvaried starting\nsituations.',
          'View your past\nresults.',
          'Learn the rules\nof Itadaki\nStreet.',
          'End the game.']),
    ]
    for kind, table, expected, translated in tables:
        for i, (old, new) in enumerate(zip(expected, translated)):
            ptr = struct.unpack_from('<I', original, table+i*4)[0]
            assert ptr != 0
            jobs.append((kind, ptr-0xFF000, old, new))
    # Direct menu strings, not the dynamic Chance-message formatter.
    for old, new in [
        ('何人で 遊びますか?', 'Players?'),
        ('いただきストリートへ\nようこそ。', 'Welcome to\nItadaki Street.'),
        ('今日は どのモードで\n遊びますか?', 'Choose a mode.'),
        ('どれにしますか？', 'Which option?'),
    ]:
        needle = old.encode('cp932')+b'\0'
        off = original.find(needle)
        assert off > 0 and original.find(needle, off+1) == -1
        jobs.append(('prompt', off, old, new))
    patched = bytearray(base)
    records, allowed = [], set()
    for kind, off, old, new in jobs:
        before = old.encode('cp932')+b'\0'
        encoded = new.encode('ascii')+b'\0'
        assert original[off:off+len(before)] == before
        assert base[off:off+len(before)] == before
        assert len(encoded) <= len(before), (old, len(encoded), len(before))
        region = set(range(off, off+len(before)))
        assert not region & allowed
        allowed |= region
        after = encoded.ljust(len(before), b'\0')
        patched[off:off+len(before)] = after
        refs = [i for i in range(0, len(original)-3, 4)
                if original[i:i+4] == struct.pack('<I', off+0xFF000)]
        records.append(dict(kind=kind, offset=off, offset_hex=f'0x{off:08X}',
                            virtual_address=off+0xFF000, japanese=old, english=new,
                            capacity_including_nul=len(before), used_including_nul=len(encoded),
                            original_hex=before.hex(), patched_hex=after.hex(),
                            pointer_offsets=refs))
    # Menu-building helper sets a2=20 before 0x139428 selects a font object.
    # The existing 16-pixel font is selected instead; glyph data is untouched.
    font_off = 0xC11C8
    font_before = struct.pack('<I', 0x24060014)
    font_after = struct.pack('<I', 0x24060010)
    assert original[font_off:font_off+4] == base[font_off:font_off+4] == font_before
    patched[font_off:font_off+4] = font_after
    allowed.update(range(font_off, font_off+4))
    changed = [i for i, (a,b) in enumerate(zip(base,patched)) if a != b]
    assert all(i in allowed for i in changed)
    restored = bytearray(patched)
    for rec in records:
        raw = bytes.fromhex(rec['original_hex'])
        restored[rec['offset']:rec['offset']+len(raw)] = raw
    restored[font_off:font_off+4] = font_before
    assert bytes(restored) == base
    assert all(i == font_off or not 0x1000 <= i < 0x139594 for i in changed)
    assert patched[0x3185E0:0x3188C8] == original[0x3185E0:0x3188C8]
    manifest = dict(source_sha256=EXPECTED_SHA, base_sha256=hashlib.sha256(base).hexdigest(),
                    patched_sha256=hashlib.sha256(patched).hexdigest(), size=len(patched),
                    menu_patch_count=len(records), menu_changed_byte_count=len(changed),
                    changed_offsets_relative_to_phase4=changed, patches=records,
                    code_changed=True, pointers_changed=False, runtime_verified=False,
                    font_patch=dict(offset=font_off, virtual_address=0x1C01C8,
                                    original_hex=font_before.hex(), patched_hex=font_after.hex(),
                                    original='addiu a2,zero,20', patched='addiu a2,zero,16',
                                    scope='menu-building helper 0x1C015C; may affect its other menu groups'))
    write_new_or_identical(OUT / 'patched/SLPM_621.12', bytes(patched))
    write_new_or_identical(OUT / 'menu_patch_manifest.json', encode_json(manifest))
    buf = io.StringIO(newline='')
    fields = ['kind','offset_hex','japanese','english','capacity_including_nul','used_including_nul']
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(records)
    write_new_or_identical(OUT / 'menu_translation.csv', buf.getvalue().encode('utf-8-sig'))
    elf = Elf(ROOT / 'decompile/SLPM_621.12')
    write_new_or_identical(OUT / 'argc_boot_selection.asm', elf.disasm(0x100148,0x80).encode())
    print(f'{len(records)} menu strings; {len(changed)} changed bytes relative to phase 4')
    print(f'ELF SHA256: {manifest["patched_sha256"]}')


if __name__ == '__main__':
    main()
