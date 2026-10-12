# Analyse des cartes Chance d'Itadaki Street 3 (PS2)

> Mise à jour après la phase 2 : la table réelle contient 186 emplacements et 181 textes distincts, dont un texte hors du bloc contigu et un emplacement nul (C046). Les 180 chaînes contiguës ne correspondent pas directement à C001–C180. Voir `phase2_report.md` et `extracted/phase2/card_mapping.json` pour la correspondance corrigée.

## Portée et sécurité

L'analyse a été effectuée en lecture seule sur les ISO et les ressources extraites. Aucun fichier d'origine n'a été modifié, renommé ou supprimé. Toutes les nouvelles sorties se trouvent sous `translation_work`. Aucune dépendance ni opération réseau n'a été utilisée, aucune décompilation complète et aucune reconstruction d'ISO n'ont été lancées.

## 1. Inventaire du projet

### Images disque et exécutables

- `idataki3.iso` — 575 420 416 octets.
- `idataki3.original.iso` — 575 420 416 octets.
- Les deux ISO sont identiques bit à bit : SHA-256 `6e8e471f9b6aef1af78b9cf99407ffd9adaa2c51a871f622dd84db140404dcab`.
- Exécutable principal PS2 : `decompile/SLPM_621.12` — 3 923 328 octets.
- Exécutable secondaire : `decompile/MOVIE.ELF` — 1 535 968 octets.

### Dossiers de ressources

Les principaux dossiers extraits sont `CARD`, `CASINO`, `CHARA`, `CHRA2`, `MINI`, `MODULES`, `MOVIE`, `PARTS`, `SOUND`, `STAGE` et `SYS`. Des dossiers `CARD - Copie` et `SYS - Copie` existent aussi et semblent être des copies de travail antérieures; ils ne font pas partie de l'inventaire source retenu.

### Dossier CARD

- Chemin source : `decompile/CARD`.
- 186 fichiers, exclusivement `C001.TI` à `C186.TI`, sans trou dans la numérotation.
- Taille totale : 12 389 088 octets.
- Chaque fichier mesure 66 608 octets.
- 165 contenus SHA-256 uniques; 21 fichiers sont des répétitions supplémentaires de contenus déjà présents.
- Groupes de doublons :

  - `C003/C057`
  - `C005/C141/C142/C143/C144/C169/C170/C171/C172/C173/C174/C178/C179`
  - `C016/C031`
  - `C053/C181/C182`
  - `C065/C067`
  - `C083/C088`
  - `C095/C119/C175`
  - `C183/C184`

L'inventaire complet avec taille, SHA-256, premier doublon correspondant et structure détectée est dans `card_inventory.csv`.

`decompile/CARD - Copie` contient 186 fichiers `.data` identiques aux `.TI` source (mêmes hashes), plus un ancien `C033.png` de 178 × 128. Cet élément a servi de contrôle indépendant du décodage, mais n'est pas traité comme une ressource originale du jeu.

Les chemins ASCII `cdrom0:/card/c001.ti` etc. sont référencés dans les deux exécutables, ce qui confirme que le jeu charge individuellement les images du dossier `CARD`.

## 2. Analyse binaire du format TI

Des fichiers répartis dans la série et aux contenus différents ont été comparés (`C001`, `C005`, `C033`, `C186`), puis les propriétés structurelles ont été contrôlées sur les 186 fichiers.

Tous partagent un en-tête identique de 48 octets. Il est suivi d'une palette RGBA de 1 024 octets puis de 65 536 indices 8 bits. La structure totale est donc :

| Zone | Offset | Taille | Interprétation |
|---|---:|---:|---|
| En-tête propriétaire | `0x0000` | `0x30` | descripteur de texture |
| CLUT | `0x0030` | `0x400` | 256 couleurs × RGBA |
| Pixels | `0x0430` | `0x10000` | 256 × 256 indices 8 bits |

Les dimensions 256 × 256 sont cohérentes avec les valeurs `0x0100` de l'en-tête. Les pixels sont linéaires. La palette utilise la permutation CSM1 classique des CLUT PSMT8 PS2; sans elle, les formes sont reconnaissables mais les couleurs sont fausses. L'alpha PS2 `0x80` doit être étendu à l'alpha PNG 255.

Le fichier ne porte aucune signature connue. Il s'agit vraisemblablement d'un format de texture propriétaire très simple, compatible conceptuellement avec PSMT8, et non d'un TIM2 standard.

Les aperçus validés sont :

- `extracted/C001.png` — dé directionnel correspondant à « changer de direction ».
- `extracted/C033.png` — pancarte `FOR SALE ×3`, correspondant au résumé japonais de la carte 33.
- `extracted/C186.png` — formes de poissons stylisées; rôle exact encore inconnu.

## 3. Localisation du japonais

### Résultat principal

Les textes descriptifs ne sont pas incorporés dans les textures. Ils sont stockés dans l'exécutable principal `SLPM_621.12` en CP932, variante Windows du Shift-JIS, sous forme de chaînes NUL-terminées.

Un bloc continu de 180 résumés commence à `0x369470`. La phase 2 a retrouvé la table de 186 pointeurs à `0x3185E0`, nécessaire pour associer correctement ces textes aux cartes. Exemples :

| Carte | Offset | Japonais (résumé) |
|---|---:|---|
| C001 | `0x369470` | `方向てんかん\nできる!` |
| C002 | `0x369488` | `もう1回すすむ!` |
| C033 | `0x3698F8` | `3倍で\nはらいもどし\nチャンス!` |
| C186 | `0x36AA20` | `ゴーストたちが\n陽気に\nさわぎだした!` |

L'extraction complète est dans `extracted/card_text_ja.json`. Chaque entrée conserve l'offset, la longueur encodée et l'espace alloué incluant le NUL final.

Des messages détaillés liés aux effets commencent ensuite vers `0x36AA48`. Leur association n'est pas strictement une chaîne par carte et ils comprennent des codes de substitution. La traduction future devra couvrir à la fois les 180 résumés et ces messages d'exécution.

### C181 à C186

La phase 2 a confirmé les entrées C181 à C186 dans la table de pointeurs : les deux premières concernent des déplacements vers des banques, et les quatre suivantes des événements de fantômes. C183 et C184 partagent leur texte.

## 4. Prototypes produits

### `scripts/extract_ti.py`

Extracteur Python standard-library qui :

- valide la taille attendue;
- sépare en-tête, palette et indices;
- applique la permutation CLUT PS2;
- convertit l'alpha PS2;
- écrit un PNG RGBA 256 × 256;
- peut écrire un JSON de métadonnées utile à une future réinjection;
- n'ouvre jamais la source en écriture.

Exemple d'utilisation quand un interpréteur Python réel est disponible :

```powershell
python translation_work/scripts/extract_ti.py decompile/CARD/C033.TI `
  -o translation_work/extracted/C033_test.png `
  --metadata translation_work/extracted/C033_test.json
```

Le lanceur `python.exe` présent dans cet environnement est actuellement un alias Windows Store inaccessible. Le décodage a donc été validé par une implémentation équivalente PowerShell/.NET, qui a produit les trois PNG. Le script Python n'a pas nécessité l'installation d'une dépendance.

### `scripts/extract_card_text.py`

Extracteur CP932 standard-library corrigé en phase 2 pour les 186 emplacements réels. Il produit un JSON comprenant les offsets, pointeurs et longueurs. Un interpréteur Python 3.12 local a été trouvé via `uv --no-cache python find --offline` en phase 2; le script corrigé a été exécuté et comparé au scanner PowerShell/C#.

## 5. Faisabilité de la traduction et méthode proposée

### Extraction

1. Extraire les 186 emplacements réels : 185 pointeurs non nuls, 181 textes distincts, puis cataloguer séparément les messages détaillés associés aux effets.
2. Conserver pour chaque chaîne : offset actuel, octets CP932, longueur, références/pointeurs et codes de contrôle.
3. Extraire toutes les textures en PNG seulement lorsqu'une retouche d'élément graphique est nécessaire. Les illustrations sans texte japonais n'ont pas besoin d'être modifiées.

### Traduction anglaise

1. Traduire naturellement les mécaniques de jeu, avec un glossaire stable (`shop`, `stock`, `district`, `salary`, etc.).
2. Préserver les paramètres et codes de contrôle.
3. Adapter chaque résumé à trois lignes au maximum lorsque l'interface l'exige, après mesure en jeu.
4. Tester d'abord quelques cartes représentatives : texte court, texte long, nombres variables et choix interactifs.

### Réinjection

Une simple réécriture en place ne sera possible que si la chaîne anglaise encodée tient dans l'allocation existante et si le moteur possède les glyphes nécessaires. Pour les textes plus longs, la méthode robuste sera :

1. identifier la table de pointeurs ou les instructions qui référencent les chaînes;
2. placer une nouvelle table anglaise dans une zone libre ou étendre proprement une section de l'ELF;
3. mettre à jour les références et préserver l'alignement;
4. vérifier la police latine et les largeurs de glyphes;
5. valider chaque paramètre dynamique.

Pour une texture retouchée, il faudra limiter le PNG à 256 couleurs, écrire les indices linéaires, appliquer la permutation CLUT inverse, convertir l'alpha vers `0..0x80`, puis reconstituer exactement `0x10430` octets en conservant l'en-tête.

### ISO et PCSX2 (phase future uniquement)

1. Travailler depuis une copie dédiée des fichiers extraits, jamais depuis `idataki3.original.iso`.
2. Remplacer uniquement les ressources validées et l'exécutable patché.
3. Reconstruire une ISO de test en conservant l'ordre/les propriétés du système de fichiers nécessaires au jeu.
4. Comparer les manifestes et vérifier que l'ISO originale reste inchangée.
5. Tester dans PCSX2 avec journalisation : chargement, choix de carte, résumé, déroulement de l'effet, retours à la ligne et valeurs dynamiques.

## 6. Limites de la première analyse (état historique)

- Aucun désassemblage du chargeur de textures ni de la logique des cartes n'a été effectué.
- La table de pointeurs des chaînes a depuis été identifiée en phase 2 à `0x3185E0`.
- Les messages détaillés n'ont pas encore été associés individuellement aux 180 cartes.
- La disponibilité et la métrique des glyphes anglais n'ont pas encore été testées.
- Aucun encodeur/réinjecteur `.TI` et aucune ISO de test n'ont été produits à ce stade.

## Suivi des phases ultérieures

Les résultats détaillés sont dans `phase2_report.md`, `phase3_report.md`, `phase4_report.md`, `phase5_report.md` et `phase6_report.md`. La table des 186 cartes, les commandes de formatage et le renderer ASCII ont été étudiés de manière ciblée. Un patch de quatre chaînes Chance sur copie a été créé puis conservé dans une copie intégrant 28 traductions de menu.

La phase 5 démontre dans PCSX2 le menu principal anglais et les choix joueurs, avec captures natives dans `extracted/phase5`. Le lancement avec `-gameargs "0 0"` évite l'introduction et le rechargement initial de l'ELF original. La police des listes de menu est réduite de 20 à 16 dans un unique sélecteur de la copie de code pour éviter les débordements. Aucun ISO, fichier extrait source, BIOS ou carte mémoire d'origine n'a changé de hash. La copie finale de cette phase était `phase5/revision3/patched/SLPM_621.12` ; trois derniers raccourcissements restaient à revoir à l'écran, comme le sous-menu des données. Les cartes Chance anglaises elles-mêmes n'ont pas encore été affichées en jeu.

La phase 6 étend réellement la traduction : 177 résumés de cartes intégrés sur 185 textes non nuls, 129 messages d'effets distincts sur 140, 30 messages de sauvegarde/chargement et le sous-menu d'entraînement (six choix et une description). Les 28 textes précédents sont conservés. La version actuelle est **`phase6/revision3/patched/SLPM_621.12`**, à charger avec `scripts/launch_translation_test.ps1`, sans modifier l'ISO. Catalogue japonais/anglais et états individuels : `phase6/revision3/translation_catalog.csv`. Les contrôles binaires indépendants et le retour exact à l'original passent ; 19 brouillons restent non intégrés. La révision 2 de ce lot a atteint le menu principal anglais dans PCSX2 (`extracted/phase6/main_menu.png`) ; la révision 3 ajoute deux chaînes de sous-menu et n'a pas encore été contrôlée visuellement. Les cartes et les effets restent à vérifier en situation.

## 1. Ce que nous savons du format `.TI`.

Mise à jour phase 7 : **la copie actuelle est `phase7/revision3/patched/SLPM_621.12`**.
Elle conserve la phase 6 et ajoute les 62 chaînes de Rules, plus 124 autres chaînes
de sous-menus et messages d'interface. Le lanceur commun charge cette version.
Voir `phase7_report.md` et `phase7/revision3/rules_translation.csv`. Les règles
anglaises ont effectivement été observées dans PCSX2 sur la première version de
phase7 ; les 62 textes sont inchangés dans revision3. Tous les sous-menus n'ont
pas encore été vérifiés visuellement.

Le format des cartes est une texture propriétaire non compressée de 256 × 256 pixels, indexée 8 bits, avec en-tête de 48 octets, CLUT RGBA de 256 couleurs à `0x30` et pixels linéaires à `0x430`. La CLUT suit la permutation PS2 CSM1 et l'alpha PS2 plafonne à `0x80`. L'extraction PNG est réalisable et démontrée.

## 2. Où se trouvent probablement les textes japonais.

Les textes sont dans `SLPM_621.12`, en CP932 : 180 chaînes contiguës à partir de `0x369470`, plus le texte de C040 à `0x3B9E08`. Leur correspondance réelle aux 186 cartes est donnée par les pointeurs à `0x3185E0`. C046 a un pointeur nul. Les messages détaillés sont également dans cet exécutable. Les `.TI` contiennent surtout des illustrations.

## 3. Si l'extraction et la modification semblent réalisables.

Oui. L'extraction des images et des 186 emplacements de résumés est démontrée. Les pointeurs et une partie du formatage sont identifiés ; des réécritures anglaises en place sur copies passent les vérifications binaires. Le rendu anglais est démontré pour le menu, mais reste à vérifier pour les cartes Chance et leurs messages dynamiques. La réinjection graphique reste à tester par un aller-retour exact.

## 4. Les trois prochaines actions techniques recommandées, classées par priorité.

1. Afficher dans PCSX2 C001, C002, C033 et un événement de revenu en conservant la copie patchée ; vérifier les marges et substitutions dynamiques.
2. Valider le sous-menu des données et les dernières chaînes raccourcies, puis étendre le catalogue de menus et affiner la typographie sans affecter les autres écrans.
3. Développer un aller-retour PNG → `.TI` strictement vérifié sur copie, puis préparer, seulement lors d'une phase autorisée de reconstruction, une ISO de test distincte.

