# Phase 13 — Free Play opponent selection (English v13)

Date: 2026-10-12. Final build: `phase13/revision3`.

## Outcome and validation status

Reviewed all 14 owner-provided v12 screenshots. Added **119 fixed-address string replacements**: 81 opponent/profile strings and 38 surrounding UI strings. All 12 standard opponents now have ASCII-only profile rows and short names. Already-English Ayumi, Rei and Itaro strings are inherited from v12.

The cumulative BPS includes all earlier translations, 33 patched MAP resources and both user-edited English title images. No original ISO or extracted resource was modified. No output ISO was written. Independent BPS verification reconstructed and hashed the complete virtual target, checked all 35 file extents and passed.

**Runtime validation of v13 is still pending.** The owner's successful PCSX2 **v2.8.2** test applies to v12, not v13. No emulator was launched in this phase.

## Screenshot review

Filename prefix: `Itadaki Street 3 - Okuman Chouja ni Shiteageru! Kateikyoushi-tsuki_SLPM-62112_20261012`. All files are in `screenshots_before_translation`.

| Filename time suffix | Visible content | Treatment |
| --- | --- | --- |
| 201718 | Ask the player to identify their name with their own controller | Translated, four lines of at most 14 characters |
| 201729 | Tsurara | Profile, age, hometown, job, hobby and statistics |
| 201732 | Ayumi Imai | Same |
| 201734 | Itaro | Same; preserve already-English name |
| 201736 | Rei Kirisaki | Same |
| 201739 | Gandhara Yoko | Same |
| 201741 | Shimonji Fukujiro | Same |
| 201747 | Maki Kuroudo | Same |
| 201750 | Tutankhamen | Same |
| 201752 | Economic monster Kabura | Same |
| 201754 | Nekobro | Same |
| 201757 | Ikesuya Sabakichi | Same |
| 201800 | Saionji Sakurako | Same |
| 201814 | Unregistered player/trainee slots and statistics | Empty, place, games, points, win rate, rank and finishing positions |

The red **参加** badge is a texture, not one of these strings. It is **not translated in v13**. See the dedicated finding below.

## Confirmed binary findings

- The standard profile table starts at ELF file offset `0x3182E8`. Records are 32 bytes: eight little-endian pointers, in order: display name, age, description, hometown, occupation, hobby, rank, short name. Twelve standard records occupy `0x3182E8..0x318468`; additional placeholder/special records follow. The full `0x3182E8..0x318528` table is unchanged.
- Virtual addresses of these strings equal file offset plus `0xFF000`.
- Text lives in CP932 NUL-terminated strings near `0x368898..0x368D38` and `0x3B9C88..0x3B9D98`. References and original/current text are recorded in `analysis/opponent_inventory.json`.
- The targeted renderer at `0x1CA548` indexes the table with a 32-byte stride. It formats the header using `%s　　%s` and separate description/home/job/hobby lines. `analysis/profile_renderer.txt` records the relevant instructions. This is a normal formatted UI rendering path, not the special Chance-card `A/B/C` command parser: ASCII text is not wrapped in CP932 quote markers.
- The shared profile font object at VA `0x23C2B0` is initialized to 20-by-20 at `0x10103C..0x101054`. The portrait bounds inferred from the captures and draw coordinates leave approximately 350 pixels from text x=88. English rows are conservatively capped at 17 characters, including prefixes and the header's age. Exact rows are recorded in `revision3/profile_layout_checks.json`. Actual clipping/appearance still requires a runtime check.
- Each replacement fits its original string allocation. A few longer names reuse verified zero alignment padding, only up to the next 8-byte boundary; adjacent text and binary fields are not consumed. Existing aligned data pointers into those padding bytes are rejected. No pointers are relocated, no instructions change and the new manifest supports exact rollback to v12.
- All printf argument signatures and color commands are preserved. Profile rank letters and stored gameplay statistics are unchanged.

## Translation choices and full meanings

Short English is necessary because this screen uses separate, single-line fields. Full meanings are preserved here for future refinement, while the Japanese source remains in the inventories/manifests.

- **Sakurako Saionji**: wealthy young lady raised in Britain; from Denenchofu; university student; flower arranging and horseback riding. Header shortened to `Sakurako`; hobby to `Flowers/ride`.
- **Tsurara**: a female ninja who travelled through time; from Iga; part-time fast-food worker; espionage.
- **Ayumi Imai**: a genius who skipped school grades; from Sapporo; final-year high-school student; collects teddy bears. `HS senior` describes her school year, not her age.
- **Rei Kirisaki**: Japan's top surgeon; from Yokohama (`Yokoh.`); female doctor; enjoys cutting things up.
- **Gandhara Yoko**: head of the secret/hidden Gandhara astrology school; from the Himalayas; fortune-teller; Indian dancing. Header `G. Yoko`, description `Astrology master` omit school details to fit.
- **Shimonji Fukujiro**: becomes stronger when he transforms; from Fukuoka; self-proclaimed hero of justice; transforming and patrolling. Header `F. Shimonji`; short name `Shimonji`.
- **Maki Kuroudo**: a stage actor hiding intense emotions behind a mask; from Kyoto; kyogen actor; makes Noh masks. `Masked actor` loses the emotional nuance; the source and full meaning remain documented here.
- **Tutankhamen**: an ancient man revived from his coffin; from Egypt; mummy; collects scarabs. Short name `Tutan`. Romanization is a project choice, not a claim of an official English name.
- **Itaro**: robot built five years ago specifically for Itadaki Street; from the Tanegashima Itadaki Street laboratory; occupation Itadaki Street; hobby Dragon Quest. `Tanega. lab` abbreviates the full laboratory name.
- **Kabura**: economic monster; scientific name `Economikabukainodon` (displayed as `Economikabuk...`); from 5,000 metres underground; economic activity; eats economic newspapers. `Eats papers` retains the joke but omits the newspaper type.
- **Nekobro**: three cat brothers with distinct personalities; from beneath a bridge (`Bridge`); cat gatherings; agitational speeches.
- **Sabakichi Ikesuya**: human-speaking mackerel; from waters near Niigata (`Niigata`); chef; enka music. Header `Sabakichi`, short name `Saba`. The screenshot is needed to read the short-name custom glyph correctly; a plain CP932 decode yields `サバ仝`.

Shared labels: `Home`, `Job`, `Like` (hobby), `Wins` (first-place finishes), `W/R` (win ratio, retaining the original decimal rather than converting to a percent), `Rank`, `Place`, `Games`, `Points`, `2nd`, `3rd`, `4th`, `Empty`. `W/R` is deliberately short to avoid the separate rank field at the right.

## Remaining texture text: participation badge

The badge **参加** (participating/selected) is visibly present in `analysis/SYSTEM_10.png`, around x=100..163, y=98..130. This is image 10 of `decompile/SYS/SYSTEM.TI` (512x256, observed PSMT8 descriptor, linear indices, CSM1 palette). Palette offset `0xA47B0`, pixels offset `0xA4BB0`; metadata and PNG hashes are in `analysis/system_psmt8_inventory.json`.

`scripts/extract_phase13_system.py` reproducibly exports images 9, 10 and 14. Other mixed SYSTEM formats are intentionally not decoded. No SYSTEM.TI reinjection or badge redraw has been performed. A future edit must preserve all unrelated atlas pixels, other images, palettes, resource size, descriptor IDs and subimage coordinates. Suggested badge label: `IN` or `JOIN`, subject to its small pixel budget.

This atlas also contains other Japanese graphic labels; exporting it does not translate them. v13 does **not** make the entire game English. Most of the 1,825 Tutor pages and many other dialogues/property names remain outside this phase.

## Reproduction and checks

From project root, using Python 3.12 or compatible Python 3:

```powershell
python -X utf8 translation_work/scripts/analyze_phase13.py
python -X utf8 translation_work/scripts/extract_phase13_system.py
python -X utf8 translation_work/scripts/build_phase13_patch.py
python -X utf8 translation_work/scripts/release_phase13.py
```

Scripts use only the standard library and create separate outputs. They require the existing v12 build and original local inputs. Generated output is accepted only if new or byte-identical. `revision1`, `revision2` and `draft_release_revision2` are local development drafts, not the final release.

Final verification: `revision3/binary_and_bps_verification.json` — **PASS**. The release independently checks source ISO contents, file allocations, reversible resource records, allowed changes, complete virtual-target SHA256/CRC32 and all reconstructed file hashes. The title and MAP copies are byte-identical to v12. The launcher `scripts/launch_translation_test.ps1` now expects v13; it was not executed.

## Patch and ISO checksums

Patch: `translation_work/release/english_v13/Itadaki_Street_3_English_v13.bps` (364,799 bytes).

Patch SHA256: `f485955a9257b69fa9e303787227b443bc0773aeb046662298836bfdeb1d442d`.

Original ISO SHA256: `6e8e471f9b6aef1af78b9cf99407ffd9adaa2c51a871f622dd84db140404dcab`.

Original ISO CRC32: `0c2d5525`.

Patched v13 ISO SHA256: `742a75cda5279e2ca8a460e28d001c0460e1ed20e9dec976f582d46fb9377403`.

Patched v13 ISO CRC32: `fbf40d28`.

Both ISO sizes: 575,420,416 bytes. Target checksums are calculated from independently reconstructed virtual output, not an ISO written to disk.

Apply the cumulative v13 BPS with Floating IPS to a separate copy of the **original, unpatched ISO**, never to v12. Save to a new ISO. Do not restore a v12 savestate to validate changed memory-resident strings; boot the new ISO and use normal memory-card saves if needed.

## Next actions, in order

1. Owner runtime test in PCSX2 v2.8.2: cycle all twelve opponents, check long profile rows and the bottom statistics with nonzero values, visit empty and existing trainee slots, and confirm the controller-identification prompt.
2. Translate the identified participation badge and other selected atlas labels with a dedicated, reversible mixed-SYSTEM.TI editor; keep raw atlas originals local.
3. Once the owner approves the desired release version, prepare the clean GitHub project according to `publication_decisions.md`. Do not publish drafts, ISO/BIOS/emulator files or legacy Apply launchers. No GitHub publication has occurred during phase 13.
