# Notes sur le format `.TI` des cartes

## Faits confirmés

- Les 186 fichiers `decompile/CARD/C001.TI` à `C186.TI` font tous 66 608 octets (`0x10430`).
- Tous possèdent le même en-tête binaire de 48 octets (`0x30`) :

  ```text
  00000000  10 00 00 00 01 00 01 00 30 00 00 00 00 00 00 00
  00000010  00 23 00 00 00 00 01 00 00 00 00 00 00 00 00 00
  00000020  04 23 00 01 00 01 01 00 00 04 00 00 00 00 00 00
  ```

- À `0x30` se trouvent 256 entrées de palette de 4 octets, soit `0x400` octets.
- À `0x430` se trouvent exactement 65 536 indices de palette, soit une surface de 256 × 256 pixels à 8 bits par pixel.
- Les dimensions 256 (`0x0100`) apparaissent deux fois dans l'en-tête, aux offsets `0x22` et `0x24` (lecture little-endian sur 16 bits).
- Les pixels sont rangés ligne par ligne. Aucun désentrelacement (« unswizzle ») des pixels n'est nécessaire.
- La palette nécessite la permutation CLUT CSM1 habituelle des textures PS2 8 bits :

  ```text
  mapped = (index & 0xE7) | ((index & 0x08) << 1) | ((index & 0x10) >> 1)
  ```

- Les composantes sont stockées dans l'ordre R, G, B, A. L'alpha PS2 va de `0x00` à `0x80`; pour un PNG, `0x80` correspond à 255.
- Le décodage produit des illustrations nettes. `C033` représente une vente/remboursement à trois fois la valeur, en accord exact avec le 33e résumé japonais trouvé dans l'exécutable.
- Aucun marqueur TIM2 (`TIM2`), PNG, BMP, gzip ou LZSS n'apparaît comme signature du conteneur. Ce n'est pas un fichier TIM2 standard.

Décomposition exacte : `0x30 + 0x400 + 0x10000 = 0x10430`.

## Hypothèses très probables

- Le champ `0x0100` aux offsets `0x22` et `0x24` représente bien largeur et hauteur. Le rendu et la taille du plan de pixels le confirment, même si le code de chargement n'a pas été désassemblé.
- Le format graphique sous-jacent est l'équivalent de `PSMT8` avec CLUT 32 bits. Les données et la permutation correspondent à ce modèle, mais l'identifiant de format à `0x20` n'a pas encore été relié formellement à une structure interne nommée.
- Les octets `0x00..0x2F` forment un petit descripteur propriétaire destiné au chargeur du jeu plutôt qu'un conteneur multi-ressources.
- La partie utile des illustrations occupe le coin supérieur gauche; le reste de la texture est transparent. Par exemple, l'image utile de `C033` correspond à 178 × 128 pixels.

## Hypothèses rejetées ou affaiblies

- **Texte principal incorporé à l'image : rejeté.** Les PNG montrent une illustration, tandis que les résumés japonais sont présents en CP932 dans `SLPM_621.12`. Quelques lettres ou chiffres décoratifs peuvent néanmoins faire partie du dessin (par exemple `FOR SALE` et `×3` dans `C033`).
- **Données compressées : rejeté.** La taille correspond exactement à l'en-tête, la palette et le plan d'indices non compressé; le décodage direct fonctionne.
- **Conteneur de plusieurs ressources : rejeté pour les fichiers étudiés.** Un seul descripteur, une seule palette et un seul plan de pixels sont présents.
- **Swizzle des pixels PS2 : rejeté.** L'ordre linéaire donne directement l'image correcte. La permutation CLUT reste nécessaire.
- **TIM2 standard : rejeté.** Pas de signature `TIM2`, et l'organisation de l'en-tête diffère.

## Texte japonais

- Une table de 180 résumés de cartes, NUL-terminés et encodés CP932/Shift-JIS, commence à l'offset fichier `0x369470` dans `decompile/SLPM_621.12` et se termine avant `0x36AA48`.
- Correction de phase 2 : ces 180 chaînes ne correspondent pas directement à C001–C180. Une table de 186 pointeurs à l'offset `0x3185E0` définit la correspondance réelle; elle réutilise quatre chaînes, inclut le texte de C040 hors du bloc et un pointeur nul pour C046. Voir `phase2_report.md`.
- Les textes détaillés affichés après l'effet continuent au-delà de cette table, dans le même exécutable. Ils contiennent des paramètres propriétaires visibles comme `P`, `G`, `g`, `E` ou `S`; ils ne doivent pas être traduits naïvement avant compréhension du moteur de formatage.
- C181 à C186 ont leurs entrées dans la table de pointeurs réelle : banques pour C181/C182, fantômes pour C183–C186. Certains doublons graphiques concordent avec des effets apparentés (`C181/C182 = C053`, `C183 = C184`).
- Aucun texte japonais structuré exploitable n'a été identifié dans les `.TI`; les octets de palette et d'indices peuvent fortuitement former des séquences valides en Shift-JIS.

## Points inconnus

Mise à jour phase 3 : voir `phase3_report.md`. Le renderer gère le pointeur nul de C046; le formateur des messages détaillés et ses commandes sont identifiés. Les délimiteurs `『…』` permettent des segments littéraux. La signification exacte des sélecteurs A/B/C et les contraintes de tampons et d'affichage restent à valider.

- Signification exacte de chaque champ de l'en-tête de 48 octets.
- Traitement du pointeur nul de C046 et fonctionnement précis de la routine d'affichage; la table de pointeurs est désormais identifiée.
- Contraintes du moteur sur la longueur, les sauts de ligne, les glyphes latins et les codes de substitution.
- Procédure inverse complète PNG → palette/indexation `.TI`, qui nécessitera quantification à 256 couleurs, permutation CLUT inverse et conservation stricte de l'en-tête.

