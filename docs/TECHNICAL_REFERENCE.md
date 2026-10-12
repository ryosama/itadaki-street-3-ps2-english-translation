# Technical reference

All offsets below are **original ELF file offsets** unless labelled as virtual
addresses. Use exact source hashes; do not assume they apply to another revision.

## Original and integrated resources

- Original ELF `SLPM_621.12`: 3,923,328 bytes, SHA256
  `d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5`.
- v13 ELF SHA256:
  `5421225c2712dd1fedfc69e1fe1659031a4bd4b601ccccab30167aeb493d8504`.
- ELF extent in verified ISO: byte 268,288 (sector 131). Text-region comparison
  normally guards `0x1000..0x139594`. One inherited phase-5 instruction at `0xC11C8`
  changes `14000624` to `10000624` (ASCII pitch 20 to 16 on that font path).
  v13 itself adds no instruction changes.
- For the string/data regions studied, VA = file offset + `0xFF000`. The ELF reader
  in `inspect_mips.py` uses PT_LOAD segments; prefer that over a universal assumption.

## CARD .TI textures versus text

There are **186** `CARD/Cxxx.TI` textures, each **66,608 bytes**. Confirmed format:
48-byte header, 1,024-byte RGBA CLUT, 65,536 linear 8-bit indices, 256x256 image.
Indices use the PS2 CSM1 CLUT permutation (swap index bits 3 and 4); alpha is 0..128,
scaled to 0..255 for PNG. Original card illustrations contain embedded Japanese,
but descriptions/summaries are separately stored in the ELF.

Summary pointer table: `0x3185E0..0x3188C8`, 186 slots, 185 non-null and 181 unique
strings. C046 is null. Shared pairs: 19/90, 132/149, 169/170, 183/184.
Detail table: 143 pairs at `0x3188D8`, 8-byte stride, pointer at +4, 140 unique texts.
Later analysis refined earlier counts: use the latest inventories, not early totals.

`translation_work/extracted/card_text_ja.json` contains source transcription/mapping.
Extraction: `extract_ti.py`, `extract_card_text.py`, `extract_format_tables.py`.

## Text encoding and commands

Japanese strings are typically CP932, NUL-terminated. English generally stays ASCII,
but detailed Chance/general message formatter paths include special control letters:
`P/p` player, `G/g` integer, `S/s` shop, `E/e` district, and `A/B/C` digit selectors.
Literal English letters can otherwise be mistaken for commands.

`message_format.py` tokenizes and protects literal text with CP932 `『』` markers.
Preserve command signatures, case and selectors; do not strip those markers from
compiled card text. Some dialogue uses additional `/cN` color controls and printf
arguments; keep their signatures/order/type. No global byte-pattern replacement.

**Ordinary UI and Tutor pages use direct rendering:** do not indiscriminately quote
ASCII with `『』`. Trace the draw path before choosing a compiler. Use newline and
menu option counts appropriate to the actual caller, not just the byte capacity.

## Tutor tables and layout

Female table starts `0x31DE58`, male `0x321698`. Each has 720 events x 20-byte records,
five 4-byte page pointers per record; combined range ends `0x324ED8`. Inventory:
`translation_work/phase9/revision1/tutor_table_inventory.json` (1,825 non-null pages).
Table-reader VA `0x1B48A0`; direct draw through `0x1219A8`/`0x1219F0` to `0x139390`.
For that tutorial window, measured font=24, width=336, line pitch=28: use at most
14 characters per explicit line and four lines. Rules/main-selector windows differ.
The shared controller-identification menu prompt at `0x360988` is not a Tutor-table page.

PS2 Lucky payout is **20%** in the investigated source; do not import the DS game's
25% rule. Selling ten or more shares can lower the price. Trust PS2 source evidence
over superficially similar DS/Wii guides for numeric mechanics.

## Opponent selection

Twelve standard profiles start `0x3182E8`, 32-byte records of eight pointers:
display name, age, description, home, job, hobby, rank, short name. Extra/special
records follow through `0x318528`. The table is unchanged in v13.
Source strings: `0x368898..0x368D38` and `0x3B9C88..0x3B9D98`.
Draw VA around `0x1CA548`; 20-pixel profile font object `0x23C2B0`, initialized
at `0x10103C..0x101054`. The compiled v13 checks profile rows including prefixes
and age against a conservative 17-character budget before the portrait.
Some strings use checked zero alignment padding up to the next 8-byte boundary;
never treat arbitrary gaps as safe capacity. Full meanings and abbreviations are
documented in `translation_work/phase13/analysis_report.md`.

## MAP and title resources

Thirty-three `STAGE/MAPxxx.BIN` files are integrated. District start is recorded at
header +0x20, cases start at +0x30. District/case records are 48 bytes, name 32 bytes
plus 16 bytes of numeric metadata. Map title occupies `0x40..0x60`. Preserve all
metadata; names are padded NUL fields. District labels are shortened for stock UI.
Candyland `MAP003.BIN` has 28 translated case names starting `0x1B0`, stride 48;
other maps still have many Japanese property names.
ELF map descriptors start `0x1C6F00`, name32 + metadata12 (stride44). Source differences
between descriptor and map titles (e.g. Left/Right Half) were intentionally preserved.

`SYS/TAI01.TI`: 329,808 bytes, 80-byte header, two PSMT8 images:

| Image | Size | CLUT offset | Index offset | Index bytes |
| --- | --- | --- | --- | --- |
| 0 | 512x512 | 80 | 1,104 | 262,144 |
| 1 | 256x256 | 263,248 | 264,272 | 65,536 |

`reinject_title_png.py` accepts noninterlaced indexed/RGB/RGBA PNGs with at most
256 RGBA colors per image and preserves the header/resource size. The two approved
PNGs reproduce v13 exactly with zero alpha-rounding error. Never replace existing
transparent white RGB merely because an image viewer makes it look suspicious.

## Remaining SYSTEM atlas text

`SYS/SYSTEM.TI`: 898,032 bytes, 103 palette and 15 image descriptors, header1,904.
It mixes formats; the title-only reinjector does **not** handle it generically.
PSMT8 image10 is 512x256, palette `0xA47B0`, pixels `0xA4BB0`; its Japanese red
participation badge is around x=100..163, y=98..130. `extract_phase13_system.py`
exports observed PSMT8 images9/10/14, validating palette-directory offsets. Further
subimage/CLUT relationships and a reversible atlas reinjector need investigation.
Do not pass this mixed container through a whole-title TI converter.

## ISO and BPS safety

ISO9660 directory records establish file extents; no ISO-wide search/replacement.
All integrated file sizes/extents remain unchanged. BPS1 uses SourceRead and
TargetRead with CRC32 footer; source and target have full SHA256 checks as well.
The standalone recipe records source resource/span hashes and target file hashes.
Streaming reconstruction computes the target without writing an ISO, then an
independent BPS decoder validates it again. This does not replace runtime testing.
