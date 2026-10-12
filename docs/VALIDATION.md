# v13 publication validation — 2026-10-12

- Owner reports v13 works very well; PCSX2 version **2.8.2**.
- Original source ISO SHA256/CRC32 and all 35 original resources match the expected revision.
- Standalone public recipe reconstructs every v13 resource and the **byte-identical** BPS.
- Repeated reconstruction passes without replacing different work outputs.
- A fresh local Git clone, containing no old intermediate files, independently
  reproduces the same BPS using only the original ISO. This validates the handoff.
- The independent streaming BPS decoder matches the full virtual-target SHA256/CRC32.
- The owner's actual patched v13 ISO was also hashed read-only: its SHA256 and
  CRC32 match the virtual target and the README. No ISO was uploaded.
- Three source-only unit tests pass: recipe geometry/capacities, title PNG dimensions/
  color counts, and synthetic BPS decoding/corruption plus overwrite refusal.
- Publication audit passes: original/patched game binaries, ISO, BIOS, PCSX2 data,
  saves, credentials and Apply launchers are excluded; relative documentation links,
  title PNG hashes and BPS hash are checked.
- Release ZIP roundtrip and member allowlist pass. It contains only BPS, English
  instructions, manifest and checksums; no full working directory or game image.

The tests do not establish full translation coverage or physical PS2 compatibility.
Historical reports retain their original pending-test statuses; the later owner
approval is recorded in `PROJECT_STATE.md` and the current release manifest.
