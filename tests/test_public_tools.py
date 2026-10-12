"""Tests requiring no game ISO, BIOS, network or installed dependencies."""
import hashlib
import json
import struct
import sys
import io
import unittest
from unittest.mock import Mock
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
import build_current as build

class PublicToolsTests(unittest.TestCase):
    def test_recipe_geometry(self):
        recipe=json.loads((ROOT/'data/v13_recipe.json').read_text(encoding='utf-8'))
        self.assertEqual(len(recipe['files']),35)
        elf=recipe['files'][0]
        self.assertEqual(elf['path'],'SLPM_621.12')
        self.assertEqual(len(elf['records']),1065)
        for file in recipe['files']:
            self.assertGreaterEqual(file['iso_offset'],0)
            self.assertLessEqual(file['iso_offset']+file['size'],recipe['source_size'])
            end=0
            for rec in sorted(file.get('records',[]),key=lambda r:r['offset']):
                self.assertGreaterEqual(rec['offset'],end)
                end=rec['offset']+rec['capacity'];self.assertLessEqual(end,file['size'])
                payload=(bytes.fromhex(rec['payload_hex']) if 'payload_hex' in rec
                         else rec['encoded_text'].encode('cp932')+b'\0')
                self.assertLessEqual(len(payload),rec['capacity'])

    def test_title_dimensions(self):
        for filename,dimensions in [('title_main_512_english.png',(512,512)),
                                    ('title_tiles_256_english.png',(256,256))]:
            w,h,rgba=build.png_rgba(ROOT/'assets/title'/filename)
            self.assertEqual((w,h),dimensions)
            self.assertLessEqual(len({rgba[i:i+4] for i in range(0,len(rgba),4)}),256)

    def test_bps_decoder_and_corruption(self):
        source=b'abcdef';target=b'abXdef'
        recipe=dict(source_size=6,target_size=6,source_crc32=f'{zlib.crc32(source):08x}',
                    target_crc32=f'{zlib.crc32(target):08x}',target_sha256=hashlib.sha256(target).hexdigest())
        patch=bytearray(b'BPS1'+build.number(6)+build.number(6)+build.number(0))
        patch+=build.number(4)+build.number(1)+b'X'+build.number(8)
        patch+=struct.pack('<II',zlib.crc32(source),zlib.crc32(target))
        patch+=struct.pack('<I',zlib.crc32(patch))
        path=Mock()
        path.open.side_effect=lambda mode:io.BytesIO(source)
        build.verify_bps(bytes(patch),path,recipe)
        with self.assertRaises(ValueError):build.verify_bps(bytes(patch[:-1])+b'\0',path,recipe)
        path.exists.return_value=True;path.read_bytes.return_value=source
        with self.assertRaises(FileExistsError):build.write_new_or_identical(path,b'different')

if __name__=='__main__':unittest.main()
