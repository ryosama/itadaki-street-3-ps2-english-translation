# Contributor and Codex instructions

This is a partial English fan translation of Japanese PS2 Itadaki Street 3,
SLPM-62112. Read `docs/PROJECT_STATE.md` and `docs/DEVELOPMENT.md` when resuming
translation work; use `docs/TECHNICAL_REFERENCE.md` for binary-format changes.

- Original ISO, extracted game resources, BIOS and saves are read-only inputs.
- Write private originals/patched copies only under ignored `work/`. Never commit
  ISO, ELF, MAP/TI binaries, BIOS, emulator runtime/configuration, saves or secrets.
- Use Python standard library; do not install dependencies or access the network
  without a task-specific reason. Never control a running user's PCSX2 session.
- v13 is the owner-tested baseline (PCSX2 2.8.2). Preserve its two English title
  PNGs, map edits, Rules and Chance translations. Do not claim full translation.
- Fixed-size replacements only unless relocation is explicitly researched and
  authorized. Preserve pointer tables, data layout, printf signatures and commands.
- Chance detailed messages use a custom formatter: protect literal reserved
  letters with CP932 `『』` via `message_format.py`. Ordinary UI and Tutor pages
  use direct rendering: do NOT add those quote markers indiscriminately.
- Keep English natural and mechanically correct, but respect the actual font,
  window width and line count. Record abbreviated/full meanings and uncertainties.
- The standalone `tools/build_current.py` reproduces v13 without prior artifacts.
  Historical builders are references, not the clean-clone entry point.
- Keep releases cumulative against the checksum-verified original ISO. Verify
  every changed resource, full virtual-target SHA256/CRC32 and the BPS independently.
  Binary verification and owner runtime testing are separate facts.
- Use new versioned work outputs; never overwrite originals or different existing
  work. Document changed offsets/capacities and exact rollback information locally.
- Player patch application uses Floating IPS, not custom Apply launchers.
- Do not add a license: the owner explicitly selected none.
