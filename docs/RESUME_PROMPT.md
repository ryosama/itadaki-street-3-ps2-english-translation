# Copyable resumption prompt

```text
Continue the English translation of Itadaki Street 3 for PS2 (SLPM-62112).
Read AGENTS.md, docs/PROJECT_STATE.md, docs/DEVELOPMENT.md and the relevant
sections of docs/TECHNICAL_REFERENCE.md before binary-format work.

The tested baseline is v13, approved by the owner with PCSX2 v2.8.2. It is
partial, not a fully translated game. Reproduce it from my original ISO with
tools/build_current.py before changing anything. The standalone recipe is
data/v13_recipe.json; historical catalogs may contain unintegrated drafts.

Preserve both English title images, the Rules/Chance translations, maps and
opponent profiles. Never change the original ISO/resources or private saves.
Put all generated game binaries under ignored work/. Use the standard library
and do not install tools or control my PCSX2 session without a reason/approval.

Next likely targets are the red participation badge in SYSTEM.TI, remaining
Tutor pages and other untranslated gameplay/Training/Quest text. Start from
the screenshots or specific target I provide. Ask if the intended scope is
unclear. Keep English faithful to THIS PS2 game's mechanics; DS/Wii references
must not override PS2 numerical rules.

Preserve string capacity, pointer tables, printf arguments and special commands.
Do not apply Chance-card quoting to plain UI/Tutor strings. Document abbreviated
meanings. Verify changed spans, rollback, resources, full virtual-ISO SHA256/CRC32
and the cumulative BPS independently. Clearly separate binary tests from actual
runtime testing. Produce a new version without overwriting v13. Use Flips for
player patch application; do not add Apply scripts or a license.
```
