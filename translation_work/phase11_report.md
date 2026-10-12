# Phase11 — intégration de l'écran-titre anglais

## Résultat

Le fichier utilisateur `phase10/title_assets/editing/title_main_512_english.png` a été inspecté puis réinjecté dans une **nouvelle copie** de `SYS/TAI01.TI`, texture0. Les traductions de l'exécutable et des 33 MAP de la v10 sont conservées octet par octet. La v11 n'ajoute aucun texte ni modification de code.

Le titre possède toujours deux textures. Seule la principale de512×512est remplacée. La texture complémentaire de256×256, sa palette et l'en-tête sont inchangés. En conséquence, la pastille japonaise visible dans l'autre texture et les crédits laissés dans l'image utilisateur restent japonais.

## Contrôles de l'image réellement effectués

- PNG512×512,256couleursRGBA distinctes : compatible avec l'allocation existante.
- Palette et indices recréés avec permutationCSM1 ; dimensions/descripteurs conservés.
- Redécodage de la texture réinjectée : **pixelsRGBA identiques au PNG utilisateur**, erreur alpha0.
- Octets0–79duTIinchangés ; taille329808inchangée.
- Octets263248à la fin duTIinchangés : deuxième palette et image préservées.
- LePNG utilisateur et tous les originaux ont seulement été lus.

La copie est à `phase11/revision1/patched/SYS/TAI01.TI`. Le manifest d'import est à côté. Un aperçu redécodé depuis leTIréinjecté est disponible dans `phase11/revision1/title_redecoded_512.png`.

## Patch ISO cumulatif

`release/english_v11/Itadaki_Street_3_English_v11.bps`, **303433octets**, s'applique à l'ISO japonais original. Il comprend l'exécutable anglaisv10, les33MAPanglaisv10et le nouveau titre. La taille et l'organisation de l'ISO sont conservées.

Le packager a été généralisé pour lire les répertoiresISO9660STAGEetSYS. Il vérifie chaque ressource extraite contre son contenu exact dans l'ISO avant de préparer les différences. Le titre ajoute deux régions réversibles : palette1024octets et plan d'indices262144octets ; tout le reste demeure original.

L'applicateurBPSséparé reconstruit la cible virtuelle, vérifie lesSHA-256/CRC32et reconstitue les35fichiers : résultat **PASS**. Toutes les actionsBPSd'écriture sont dans les extent des fichiers autorisés. L'ELF et lesMAP de la v11 sont comparés aux hashes de la v10, et le titre est réversible jusqu'à l'original.

ISO cible virtuelle SHA-256 : `cf49b0e2be9311a489e1639da3ee948be1431e6e55c16682289a5e373b931ecf`.

TitreTI SHA-256 : `700d7912fb5feb208f70add273b80e2194173fb0d0cfc14596660ef968795fe0`.

## Reproduction et limites

Scripts : `reinject_title_png.py`, `build_phase11_patch.py`, `release_phase11.py`. Le lanceur commun pointe vers la v11et exige l'ISOpatchée correspondante.

L'utilisateur peut appliquer le patch avec Flips ou `release/english_v11/Apply_English_Patch.cmd`. L'outil crée une sortie séparée ; il ne modifie pas l'ISOsource.

**Aucune ISO de sortie n'a été créée pendant cette étape. PCSX2 n'a pas été lancé ni contrôlé.** Le rendu à l'écran du nouveau titre reste à vérifier, notamment la jointure du chiffre3, la transparence et le boutonPressStart. Aucun réseau ni dépendance installée.
