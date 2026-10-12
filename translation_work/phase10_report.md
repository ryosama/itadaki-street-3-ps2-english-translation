# Phase10 — suite Tutor, noms de cartes, Lucky et écran-titre

## Analyse des captures

Les **28PNG** de `phase10/screenshots_before_translation` ont été examinés. Les rapprochements japonais/offsets et les événements Tutor correspondants sont dans `phase10/analysis/screenshot_matches.json` et `paired_tutor_pages.json`. Une correspondance de sous-chaîne peut inclure des pages non montrées ; la sélection traduite est explicitée par le catalogue et le manifest.

Les dialogues montrent cette fois **Sayaka**. Les pages visibles concernent les parcours et les quatre marques, le début de partie, les conseils de destination, l'achat de magasins sans propriétaire, les réglages et la caseLucky. Leurs variantes masculines ont aussi été traduites. Quelques pages voisines (bateaux et refus de conseils) sont incluses.

**53pages supplémentaires**, donc149sur1825pages non nulles relevées en phase9. Ce n'est pas une traduction complète du mode Tutor. Toutes les nouvelles pages ont au plus quatre lignes de14caractères et tiennent dans leur chaîne d'origine. L'explication Lucky conserve **20%**, conformément au japonais de ce jeu, sans importer les25%de la versionDS.

## Noms de cartes : pourquoi ils étaient encore japonais

Les titres dans les menus ne sont pas lus uniquement depuis les champs desMAP. Une table de descripteurs embarqués dans l'ELF contient aussi les noms, par exemple :

| Offset ELF | Original | Anglais compact |
| --- | --- | --- |
| `0x1C6F58` | おかしのくに | Candyland |
| `0x1C6F84` | マーメイドシティ | Mermaid City |
| `0x1C6FDC` | レインフォレスト | Rainforest |
| `0x1C7008` | ムーンライトクルーズ | Moon Cruise |
| `0x1C7034` | 回転寿司 | Sushi Loop |
| `0x1C70B8` | クロス | Cross |
| `0x1C6F2C` | ソフィーの洞窟 | Sophie Cave |
| `0x1C70E4` | まちゅぴちゅ | Machu Picchu |
| `0x1C6FB0` | スペースカフェ | Space Cafe |

Les descripteurs sont espacés de44octets, avec un champ de nom de32octets suivi de12octets de valeurs. Le champ nul et son padding ont été vérifiés avant utilisation ; les12octets suivants restent inchangés. C'est une région de données, hors de la région d'instructions contrôlée. **31champs ELF** sont traduits, ainsi que les titres dans les33MAP. Aucune relocation.

Le format `Street %s\n` à `0x35FEF0` devient **`Map %s\n`**, pour dégager de la place aux noms anglais. Les noms sont parfois raccourcis plutôt qu'agrandis. Les divergences originales entre noms embarqués et nomsMAP sont conservées sémantiquement : par exemple Right Half dans l'ELF, Left Half dans MAP001. Leur signification exacte entre variantes de cartes reste à analyser.

## Textes d'interface signalés

Capture19:01:32 : les valeurs séparées `ひとり` et `ぜんぶ` sont traduites en1etAll. Elles sont distinctes des intitulés Goal/Busts/Casino déjà anglais. Les occurrences de noms de personnages sélectionnées et non encore modifiées sont romanisées, sans substitution de fragments dans tous les dialogues.

Capture19:04:36 : `目標`, `しゅうかい`, `ごうけい`, `みせかず`, `かぶかず` et le format `%2dしゅうめ` correspondent à des variantes du grand tableau de patrimoine. Elles deviennent Goal/Lap/Net/Shops/Stocks et Lap%2d ; les formats numériques restent inchangés.

Capture19:05:51 : le texte à `0x36C6D8` devient **Lucky chance! / Share in other / players' fees.** Les variantes Lucky à `0x34CEC0` et `0x305E20` sont traduites. Les champs des casesLucky/Closed/suits deMAP003 sont également en anglais.

Les sélecteurs de son et de vitesse encore trop larges dans les captures utilisent maintenant **ST** et **Med**, et ceux d'échanges **ON/OFF**. Les autres intitulés courts des phases précédentes sont conservés. Cela représente23allocations d'interface dans cette phase, y compris corrections d'anglais existant.

Les28champs de cases/propriétés de Candyland sont traités : banque, magasins, marques, Closed etLucky ; les noms commerciaux incluent Sherbet Works, Muffin Tours, Waffle Cafe, etc. Certains champs étaient déjà traduits ou inchangés (`?`). Les noms de propriétés des autres cartes restent principalement japonais.

## Écran-titre extrait pour Photoshop

L'image19:00:16correspond visuellement à **SYS/TAI01.TI**, normal, et nonTAI02.TIqui porte le marquage de version d'essai. Le fichier est un conteneur de deux textures :

- principal512×512, palette256RGBA, pixels8bits ;
- complément256×256, deuxième palette indépendante256RGBA, pixels8bits.

En-tête80octets ; organisation exacte `80 + 1024 + 262144 + 1024 + 65536 = 329808`. Offset palette0=80, pixels0=1104 ; palette1=263248, pixels1=264272. Pixels linéaires, permutation de palette CSM1. Les alpha natifs sont0/128dans la première palette et128dans la seconde.

Le titre est **un assemblage de morceaux**, pas une capture plate. Le bouton Press Start se trouve aussi dans l'atlas principal et est dessiné ailleurs. Les PNG destinés à Photoshop sont :

- `phase10/title_assets/editing/title_main_512.png` ;
- `phase10/title_assets/editing/title_tiles_256.png`.

Le guide `phase10/title_assets/PHOTOSHOP_FR.md` explique dimensions, palette, transparence et export. Les PNG indexés sont utiles pour conserver la limite256couleurs ; versionsRGBA également fournies danspreviews. Les fichiers bruts de palette et d'indices, l'en-tête et les hashes sont archivés.

L'importateur `scripts/reinject_title_png.py` lit du PNG non entrelacé RGB/RGBA8bits ou indexé1/2/4/8bits, filtrePNG0–4, vérifie lesCRC et refuse plus de256couleursRGBA au lieu de fabriquer un résultat approximatif. Il peut reconstruire une palette et les indices tout en conservant l'en-tête et l'autre texture. Une copie de base séparée permet de modifier successivement les deux images.

**Tests effectués :** deux retoursPNG→TIidentiques octet par octet à l'original, pour les exportsRGBA et indexés ; deux retouches synthétiques d'un pixel avec redécodage RGB exact ; réimportation successive des deuxPNGnon retouchés via l'optionbase. Le hash deTAI01reconstitué est celui de l'original : `deecc401d6a4e4ae369d65d0cd4543ce3e3c6a2758ca2c90c4028500cc205301`.

**Limite :** aucune retouche utilisateur n'a encore été intégrée au jeu, et aucun testPCXS2des images retouchées n'a été fait. Après retour des PNG, il faudra produire une nouvelle copieTIet ajouterSYS/TAI01.TIau patchISO. La v10ne modifie pas l'écran-titre.

## Livraison et vérification

Version finale : **phase10/revision2**. La revision1est une copie intermédiaire conservée ; elle n'est pas la version publiée. Scriptsbuild_phase10_patch.pyetrelease_phase10.pyreproduisent la copie et le BPS cumulatif.

Patch : **`release/english_v10/Itadaki_Street_3_English_v10.bps`**,42132octets, à appliquer à l'ISOjaponais original, pas à la v9.

Vérification indépendante : rollbackELFàv9, code inchangé, rollbackdechaqueMAPàl'original, contenu original comparé aux extentISO9660, BPSdécodé séparément et reconstruction exacte des34fichiers autorisés, SHA-256/CRC32source et cible virtuelle : **PASS**. L'applicateur fourni a aussi été lancé enmodeVerifyOnly.

ELF cible SHA-256 : `a388e2810de478dc3da6df6ba8fa9e30ae360dc89a72e1405b51573281275515`.

ISO cible virtuelle SHA-256 : `6e79e49d0d71597bee5a22768dd6b9472b870ea151648c2cfbebc67595f21d61`.

**Aucun original n'a été modifié, aucune ISO nouvelle écrite, aucune installation ni opération réseau effectuée. PCSX2 n'a pas été manipulé.** Les nouvelles traductions demandent un contrôle visuel après application de la v10et démarrage frais.
