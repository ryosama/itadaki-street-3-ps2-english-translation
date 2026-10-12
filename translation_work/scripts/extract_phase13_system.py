"""Read-only export of three confirmed PSMT8 images in mixed SYSTEM.TI.

Image 10 contains the red Japanese participation badge at approximately
x=100..163, y=98..130. Other SYSTEM.TI formats are deliberately not decoded.
Descriptors and CLUT adjacency are validated against the container directory.
No original resources are written; stdlib PNG output, reusable for analysis.
"""
import struct
from pathlib import Path
from extract_ti import decode_linear
from extract_title_assets import rgba_png
from build_test_patch import digest, encode_json, write_new_or_identical

def main():
    source = Path('decompile/SYS/SYSTEM.TI')
    data = source.read_bytes()
    palettes, images = struct.unpack_from('<HH',data,4)
    header = struct.unpack_from('<I',data,8)[0]
    assert (palettes,images,header,len(data)) == (103,15,1904,898032)
    palette_offsets = {header+struct.unpack_from('<I',data,16+16*i+8)[0] for i in range(palettes)}
    records = []
    out = Path('translation_work/phase13/analysis')
    for index in (9,10,14):
        desc = 16+16*palettes+16*index
        w,h,fmt = struct.unpack_from('<HHH',data,desc+2)
        pixels = header+struct.unpack_from('<I',data,desc+8)[0]
        pal = pixels-1024
        assert fmt == 1 and pal in palette_offsets and pixels+w*h <= len(data)
        colors = [tuple(data[pal+4*j:pal+4*j+4]) for j in range(256)]
        png = rgba_png(w,h,decode_linear(colors,data[pixels:pixels+w*h]))
        filename = f'SYSTEM_{index:02}.png'
        write_new_or_identical(out/filename,png)
        records.append(dict(image=index,width=w,height=h,palette_offset=pal,pixel_offset=pixels,
                            pixel_bytes=w*h,descriptor_hex=data[desc:desc+16].hex(),
                            palette_hex=data[pal:pixels].hex(),png=filename,png_sha256=digest(png)))
    write_new_or_identical(out/'system_psmt8_inventory.json',encode_json(dict(
        source=str(source),source_sha256=digest(data),header_bytes=header,images=records,
        layout='linear PSMT8, CSM1 CLUT, alpha 0..128',
        other_formats_not_decoded=True,reinjection_not_implemented=True)))
    print('Exported SYSTEM images 9, 10 and 14; originals unchanged.')

if __name__ == '__main__':
    main()
