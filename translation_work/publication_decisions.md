# Publication decisions — 2026-10-12

Confirmed by the project owner:

- Target: `ryosama/itadaki-street-3-ps2-english-translation`.
- Prepare a separate, clean publication directory; preserve this local workspace.
- Publish both user-edited English title PNGs.
- Preserve useful scripts, translation catalogs, technical reports and history so another contributor can resume easily.
- Do not add a license.
- v12 was tested successfully by the owner with PCSX2 **v2.8.2**.
- The English README must include original and patched ISO SHA256 and CRC32 checksums, patch instructions using Floating IPS (https://github.com/Sir-Walrus/Flips), and screenshot slots for title, main menu, Tutor Mode and Free Play.
- Do not publish ISO files, BIOS, emulator data, saves or unmodified extracted game binaries. Do not distribute the `Apply*` patch launchers.
- Prepare contributor instructions in `AGENTS.md`, with a detailed project-state document and resumption instructions.
- Push to GitHub after preparing the repository, as authorized by the owner.

## Current priority

**v13 is complete for the agreed phase and was approved by the owner after testing** ("la v13 marche tres bien"). The owner now authorizes GitHub preparation and publication. Use the six supplied PNGs in `translation_work/screenshots` for the README. Preserve the earlier v12 validation separately; v13 has its own successful owner test.

## Verified v12 checksums

Original ISO SHA256: `6e8e471f9b6aef1af78b9cf99407ffd9adaa2c51a871f622dd84db140404dcab`

Original ISO CRC32: `0c2d5525`

Patched v12 ISO SHA256: `5814028813690091e0a04bbb5772160a51d23262a8e75e8a9d64b789c4ad01df`

Patched v12 ISO CRC32: `b010ee9c`

Future releases must use their own independently verified target checksums, not the v12 values.
