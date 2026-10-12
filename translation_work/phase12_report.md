# Phase12 — intégration du complément anglais de l'écran-titre

## Travail effectué

Le PNG utilisateur `phase10/title_assets/editing/title_tiles_256_english.png` a été examiné visuellement puis réinjecté dans une nouvelle copie de `SYS/TAI01.TI`, texture1. La copie de base est celle de la v11 : l'image principale anglaise est donc conservée, sans repartir du titre japonais.

Les255couleursRGBA du PNG, ses dimensions256×256 et son encodage sont compatibles avec la texture existante. L'importateur reconstruit la paletteCLUT et les indices, sans quantification RGB supplémentaire. Le redécodage complet restitue **exactement le PNG fourni**, alpha compris.

## Contrôles confirmés

- TailleTI329808octets inchangée ; en-tête80octets identique à l'original.
- Tous les octets0–263247sont identiques à la v11 : première palette et image principale conservées.
- La deuxième palette occupe1024octets à263248 ; les65536indices commencent à264272. Seules ces régions changent par rapport à la v11.
- L'ELF et les33MAP sont copiés avec comparaison exacte de leursSHA-256 à la v11.
- Manifest cumulatif avec quatre régions du titre réversibles jusqu'auTIjaponais original.
- BPSdécodé par l'applicateur séparé : reconstruction exacte des35fichiers et modifications uniquement dans leurs extentISO9660.
- ContrôlesSHA-256/CRC32 de l'ISOsource et de la cible virtuelle : PASS.

## Livrables

- `phase12/revision1/patched/SYS/TAI01.TI` et `TAI01.json` : nouveau titre et manifest d'import.
- `phase12/revision1/title_tiles_redecoded_256.png` : aperçu provenant de la texture réellement réinjectée.
- `phase12/revision1/phase12_manifest.json` et `binary_and_bps_verification.json` : provenance et contrôles.
- `release/english_v12/Itadaki_Street_3_English_v12.bps` : patch cumulatif de362851octets.
- `release/english_v12/README_FR.md` et lanceur d'application.

Le patch s'applique à **l'ISO japonais original**, pas à l'ISOv11. L'ISO anglaise cible virtuelle a leSHA-256 `5814028813690091e0a04bbb5772160a51d23262a8e75e8a9d64b789c4ad01df`.

Le titreTI a leSHA-256 `9b00315dd39d405d70c8bb129c94a8e78eda914a57c007057bd3d165dded98c2`.

Scripts reproductibles : `reinject_title_png.py` avec `--image 1` et `--base` sur la copie v11, puis `build_phase12_patch.py` et `release_phase12.py`. Le lanceur commun de test pointe maintenant vers la v12.

## Limites et préservation

L'utilisateur signale un test réussi de la v11 ; **la v12 n'a pas été lancée dans PCSX2 durant cette étape**. Vérifier après démarrage frais la pastille With TUTOR!, la jointure du chiffre3 et le boutonPressStart.

Aucun original, PNG utilisateur, ISO ou résultat antérieur n'a été modifié. Aucune ISO nouvelle n'a été créée pendant la préparation : le lanceur d'application ou Flips créera une copie distincte. Aucun réseau ni dépendance installé. Aucun texte supplémentaire traduit.
