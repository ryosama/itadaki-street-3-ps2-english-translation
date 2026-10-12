# Development and reproducibility

## Clean-clone baseline reconstruction

Requirements: Git, **Python 3.12+**, and your original SLPM-62112 ISO with the exact
README checksum. No Python packages, original extracted files or old phase builds
are needed. PCSX2 and BIOS are needed only for your separate runtime testing.

```powershell
git clone https://github.com/ryosama/itadaki-street-3-ps2-english-translation.git
cd itadaki-street-3-ps2-english-translation
python -X utf8 tools/build_current.py --iso 'C:\path\to\original.iso'
python -X utf8 tools/audit_publication.py
```

`work/v13/` receives read-only-input copies in `original/`, reconstructed resources
in `patched/`, a BPS and `verification.json`. These private binaries are ignored.
The builder never writes an ISO and refuses a different existing output. It checks
the full source SHA256/CRC32, every source resource/span, sizes, overlapping edits,
title PNG hashes and alpha transport, target resource hashes, full virtual ISO
checksums, exact published BPS hash and an independent BPS decoding pass.

The canonical recipe and the two edited title PNGs reconstruct v13 exactly. The
35 ISO extents are recorded from the verified source ISO; the full ISO and each
file hash prevent use of an unrelated image with coincident offsets.

For playing, apply the BPS with Flips to a **separate ISO**, as described in the
README. No custom ISO patch-applier script is distributed.

## Source versus integrated translation

`translation_work/translations/` contains editable human-readable proposals.
`data/v13_recipe.json` is the authoritative compiled, integrated snapshot: strings
include `english`, `encoded_text`, offset, capacity, original span SHA256 and phase
provenance. Map fields use `encoded_text`; the title is rebuilt from approved PNGs.

Editing a proposal catalog alone does **not** alter the compiled snapshot. The
baseline builder deliberately fails if compiled text, PNGs or target hashes change:
it is a v13 reproducibility check, not a permissive future-version editor.

## Producing a future version

1. Reproduce v13 first. Preserve its recipe, BPS and hashes; create a new versioned
   recipe and ignored output directory rather than rewriting the tested baseline.
2. Match new screenshots to the **original** strings and draw path. Use targeted
   analysis tools, not a full decompile. The baseline `work/v13/original` contains
   the 35 patched file sources; other resources can be read separately from your
   private extracted ISO. Never commit those inputs.
3. Translate and record full/compact English. Validate NUL-inclusive capacity,
   pointers, format/control signatures and the measured UI's width/line limits.
   Compile special card commands using the existing formatter helper. Ordinary UI
   and Tutor text must not receive card-specific quoting.
4. Extend a versioned builder using the baseline reconstruction helpers; record
   new target hashes only after comparing all edits with their exact allowed spans.
   Maintain original-ISO source hashes and cumulative recipes. Do not merely disable
   the v13 mismatch checks and call the result verified.
5. Independently decode and hash the new BPS, verify exact resource reconstruction,
   preserve unchanged code/metadata/titles, and retain local rollback information.
6. Test a freshly booted patched ISO in PCSX2. Exercise all affected options/events,
   varying player names and numeric values where formatting changes. Record actual
   emulator version and distinguish this from binary-only validation.
7. Update project state, changelog, coverage/limitations, screenshots if relevant,
   and original/target/patch hashes. Audit tracked files before a new tag/release.

## Historical tools and reports

Sources in `translation_work/scripts/` retain the original project-relative paths
(`decompile/`, `idataki3.original.iso`, chronological phase outputs). They are useful
references for extraction, command handling and the original patch logic, but their
phase builders need local intermediate artifacts and are **not** a clean-clone
rebuild sequence. Legacy release scripts may refer to private Apply helpers that
were deliberately not published. Use `tools/build_current.py` for the baseline.

Reports/manifests retain their historical validation statuses. The owner-approved
v13 status in `PROJECT_STATE.md` supersedes the older runtime-pending notes.

## Release packaging

```powershell
python -X utf8 tools/package_release.py
```

The deterministic ZIP under ignored `work/release/` contains only the BPS, English
instructions, release manifest and SHA256 checksums. Upload that ZIP, the standalone
BPS and external `SHA256SUMS.txt` to the v13 GitHub release. Never zip the complete
working folder. A future version needs a versioned packager and updated hashes.

## Issue reports and contributions

Provide version, mode, map, exact action, expected meaning and a screenshot. Include
offset/capacity evidence and command-preservation tests when changing binary text.
Do not upload ISO/BIOS/runtime files, private memory cards, savestates or raw game
resources. No project license has been selected; do not introduce one automatically.
