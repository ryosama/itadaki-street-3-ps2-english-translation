# Project state — v13, 2026-10-12

## Confirmed baseline

The owner reports that **v13 works very well**. Tested emulator: **PCSX2 v2.8.2**.
The v12 title art also passed owner testing. No exhaustive whole-game test or
physical PS2 test has been performed.

Latest patch: `patches/v13/Itadaki_Street_3_English_v13.bps`.
Authoritative integrated recipe: `data/v13_recipe.json`.
Authoritative clean-clone builder: `tools/build_current.py`.

The recipe consolidates 1,064 ELF text allocations plus the earlier font-pitch
instruction edit. It reconstructs all 35 changed ISO files: ELF, 33 MAPs and one
two-image title TI. It includes span hashes and English payloads, not whole
original game resources. Recipe contents are integrated; historical catalogs
may additionally contain unintegrated/rejected drafts.

## Milestones (historical, not fabricated Git commits)

| Phases | Result |
| --- | --- |
| 1–3 | CARD inventory; TI extraction; CP932/card pointer and custom-formatter analysis |
| 4–5 | First safe text copies; main menu and ASCII-pitch adjustment |
| 6–7 | Broad Chance texts, save UI, Rules and submenus |
| 8 | Gameplay menu/dialogue translations; cumulative ISO BPS |
| 9–10 | Selected male/female Tutor pages; district/map names; Candyland shops; layout corrections |
| 11 | First owner-edited English title PNG reinjected |
| 12 | Second owner-edited English title PNG reinjected; owner-tested |
| 13 | 119 additional strings: twelve opponent profiles, statistics, empty slots, controller-identification prompt; owner-tested |

There was no local Git history during those phases. Reports, source scripts,
catalogs and sanitized snapshots preserve the actual history; do not pretend
that the current import commits represent individual historical development dates.

## Known next targets

1. Opponent-selection red participation badge and other selected graphic labels
   in mixed `SYS/SYSTEM.TI`; image 10 is identified, editor not implemented.
2. Remaining Tutor dialogue: 149 translated out of 1,825 non-null table pages,
   plus separate translated menu explanations. Preserve event/page/gender mapping.
3. Remaining character dialogue, shop names and Training/Quest/UI text. Use owner
   screenshots and exact source matches; do not blindly replace all Japanese.

The supplied README screenshots include earlier build/save-state text and visible
remaining Japanese. They illustrate features, not a completion audit.

## Important files

- `docs/TECHNICAL_REFERENCE.md`: formats, offsets, control tokens and layout rules.
- `docs/DEVELOPMENT.md`: standalone reconstruction and future-version workflow.
- `docs/RESUME_PROMPT.md`: copyable prompt for another Codex session.
- `translation_work/*report.md`, `analysis_report.md`, `format_notes.md`: historical
  analysis; most are French. Their old test status/path references are historical.
- `translation_work/phase13/analysis_report.md`: opponent translations and their
  full meanings; its original runtime-pending status is superseded by the owner's
  later approval recorded in this document.
- `history/`: sanitized phase manifests (no full raw title-resource dumps).
- `translation_work/translations/`: human-readable translation drafts/catalogs.
- `assets/title/`: the two approved user-edited English images; keep PNG hashes.

## Publication policy

Owner: ryosama. Public target:
`ryosama/itadaki-street-3-ps2-english-translation`.
Preserve the original working archive locally. Publish useful source/history,
approved title art and screenshots, and a cumulative BPS release; never ISO, BIOS,
game binaries, emulator data, private saves or Apply launchers. No license selected.

For hashes use the current README and `patches/v13/release_manifest.json`.
Do not reuse v12 hashes for v13 or future releases.
