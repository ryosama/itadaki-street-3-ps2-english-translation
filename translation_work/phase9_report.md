# Phase9 — Tutor, quartiers et corrections d'interface

## Bilan

Les **31 captures** de `phase9/screenshots_before_translation` ont été examinées. Elles montrent le tuteur masculin **Hikaru Raimon (雷門ひかる)**. L'autre tuteur est **Sayaka Amamiya (雨宮さやか)**. Les introductions, explications de commandes, cartes Chance et conseils visibles ont été rapprochés de leurs chaînes originales ; les pages féminines associées ont aussi été traduites.

La nouvelle version comporte **96 messages Tutor**, **66 allocations d'interface** et **280 champs de quartiers** dans les33MAP, plus le titre de Candyland et un nom de magasin. Des champs génériques de cartes de test sont inclus ; le champ numérique de MAP032 demeure identique. Les280 ne constituent donc pas280 nouveaux noms japonais distincts.

**Le mode Tutor demeure partiellement traduit** : ses deux tables totalisent1825pages non nulles, dont96couvertes ici. Ces96chaînes sont distinctes et incluent tous les dialogues de tuteur identifiés dans les captures. Aucun taux de traduction du jeu entier n'est déduit de ce relevé.

## Tutor : format et chemin d'affichage confirmés

La table féminine commence à l'offset ELF **`0x31DE58`**, la masculine à **`0x321698`**. Chacune comporte **720 événements**, avec cinq emplacements de pages, soit des enregistrements de20octets. Les pages nulles ne sont pas ajoutées ni déplacées. Le bloc total se termine à `0x324ED8`.

Le lecteur **`0x1B48A0`** choisit le tuteur et l'événement. Les instructions autour de `0x1B4954`–`0x1B4968` calculent l'adresse dans la table : bloc de14400octets par tuteur,20octets par événement,4octets par page. Le texte choisi passe par `0x1219A8`, puis le rendu `0x1219F0` charge le pointeur et appelle directement **`0x139390`**.

**Ce chemin ne passe pas par le formateur des effets de cartes `0x136FD0`.** Les lettres anglaises ne doivent pas être protégées par `『...』` sur ces pages : cela ajouterait des caractères inutiles au texte. Les traductions Tutor sont donc en ASCII simple. Les nouveaux textes choisis ne contiennent pas de paramètres dynamiques.

Le panneau est configuré à **336pixels de large**, avec police24et interligne28. Budget conservateur : **14caractères par ligne, quatre lignes**, ainsi que la capacité de la chaîne originale en octets. Certaines explications sont condensées, sans changer les règles essentielles : mouvements selon le dé, quatre marques/suits et banque pour le salaire, baisse potentielle lors de la vente de10actions ou plus, liberté de refus d'une offre. Les hésitations et formulations répétitives sont abrégées pour tenir dans la fenêtre.

Les noms des tuteurs sont romanisés dans les introductions traduites. Les autres occurrences et les conseils non traités restent japonais ; aucune substitution globale de noms propres n'est faite.

## Quartiers : découverte dans STAGE

Les quatre noms vus à18:27:27et18:29:41ne figurent pas dans l'ELF. Ils se trouvent dans **`STAGE/MAP003.BIN`** :

| Offset MAP003 | Japonais | Proposition longue | Affichage compact |
| --- | --- | --- | --- |
| `0xC0` | ストロベリタウン | Strawberry Town / Strawb Town | Strawby |
| `0xF0` | チェリーレイク | Cherry Lake | Cherry |
| `0x120` | ノースメロン | North Melon | N Melon |
| `0x150` | サウスオレンジ | South Orange | S Orange |
| `0x180` | パインブロー | Pine Blow | PineBlow |

Les33fichiersMAP ont le même en-tête version3. Le mot à `0x20` donne le début de la liste des quartiers (`0xC0`), et celui à `0x30` le début des cases/propriétés. Les quartiers sont des **enregistrements de48octets**, avec **32octets de nom** suivis de16octets de métadonnées : indices, association de cases, etc. La nouvelle version ne modifie que le champ de nom, y compris son espace nul ; les métadonnées, offsets, tailles et ordre sont conservés.

Le nom de carte à `0x40` occupe aussi un champ de32octets. Dans MAP003, `おかしのくに` devient Candyland. Le magasin `マフィン観光` à `0x2A0` devient Muffin Tours. Tous les autres noms de magasins ne sont pas traduits.

Les noms anglais de quartiers sont limités à **huit caractères**, de manière conservatrice pour la colonne étroite de la bourse. La forme longue est conservée dans le catalogue ; certains noms sont adaptés ou abrégés. L'unicité est vérifiée **à l'intérieur de chaque carte**. Cela reste une adaptation de traduction à relire, pas une nomenclature officielle de la série.

## Corrections issues des images

- Capture18:24:20 : `Settings` devient **Options** à `0x3600E0`, un caractère plus court et idiomatique.
- Capture18:27:48 : le sous-menu du patrimoine devient **Net / All** ; `Players` était trop large dans ce panneau.
- Captures18:28:14et18:28:28 : **Text / Trade / Save / Tutor**, plutôt que des libellés longs débordant du panneau. Les aides continuent d'expliquer leur sens.
- Captures18:27:53et18:27:57 : les labels financiers sont raccourcis, avec **$/S/Sh/NW**. Les formats numériques `%7d` restent inchangés. Les compteurs deviennent Shp/Stk avec les mêmes largeurs numériques.
- Le récapitulatif Goal/Busts/Casino utilise moins d'espaces : l'ancien anglais avait conservé une indentation trop longue par rapport aux noms japonais.
- Les unités répétitives japonaises des compteurs d'actions et de magasins sont retirées là où les titres indiquent déjà ce qui est compté.
- Les aides Banque/Spade/Heart/Diamond/Club/Chance et plusieurs cases spéciales sont traduites ; d'autres aides restent japonaises.

Aucune réduction globale de police ni modification de code n'est introduite. **Ces corrections sont préparées et vérifiées binair ement, mais leur rendu n'a pas été vérifié dans une nouvelle session PCSX2.**

## Vocabulaire et source de contexte

La page [Itadaki Street DS — Super Mario Wiki](https://www.mariowiki.com/Itadaki_Street_DS#Areas_and_stock_system), demandée par l'utilisateur, confirme le principe des groupes de magasins associés à des actions, ainsi que les interactions entre investissements, valeur des magasins et cours des actions. Elle est utilisée comme **contexte terminologique**, pas pour importer des règles chiffrées DS dans le jeuPS2. Les seuils chiffrés traduits sont ceux des textes japonais de cet exécutable.

Terminologie : **shops** pour magasins/propriétés commerciales, **stocks/shares** pour actions, **districts** pour quartiers (Area dans les colonnes compactes), **invest** pour増資, **suits** pour les quatre marques, **salary** pour le gain lors du retour à la banque, **net worth/assets** pour patrimoine.

## Patch, contrôles et utilisation

Livrables :

- `phase9/analysis/screenshot_inventory.json`, `visual_matches.json`, `table_discovery.json` : preuves de rapprochement avec les captures.
- `translations/tutors_phase9_en.json`, `districts_phase9_en.json` : sources de traduction réutilisables.
- `phase9/revision1/patched/SLPM_621.12` et `patched/STAGE/MAPxxx.BIN` : copies anglaises.
- `phase9/revision1/translations.csv`, `phase9_manifest.json`, `tutor_table_inventory.json` : traductions, manifest et reste à faire.
- `phase9/revision1/binary_and_bps_verification.json` : contrôles indépendants PASS.
- `release/english_v9/Itadaki_Street_3_English_v9.bps` : patch ISO cumulatif,36753octets.
- `release/english_v9/README_FR.md` et outil d'application.

Le patch s'applique **à l'ISO japonais original**, pas à la v8. Les emplacements de l'ELF et des33MAP sont lus depuis les répertoires ISO9660 et vérifiés contre les fichiers extraits. Le BPS n'écrit qu'à l'intérieur de ces34fichiers, sans changer leur taille ni reconstruire les répertoires.

Les contrôles vérifient le retour de l'ELF à la v8, les capacités, les seules régions autorisées, la conservation du code, le retour de chaque MAP à l'original, le contenu des fichiers dans l'ISO original et la reconstruction exacte des34fichiers depuis le BPS. Les SHA-256/CRC32 de la cible virtuelle sont contrôlés par l'applicateur séparé du générateur.

ELF anglais SHA-256 : `9e54f6208f4571ca649bcdda3fb48d18f23b11aa2af2dedb0bcd141748a2c4cc`.

ISO cible virtuelle SHA-256 : `e42e739509f07a23fee566069938f095391f8d7b15794d0291d6b314de9b7331`.

**Aucune ISO nouvelle n'a été écrite et PCSX2 n'a pas été contrôlé.** Le lanceur d'application créera une copie lorsque l'utilisateur le lancera. Le lanceur de test commun exige maintenant l'ISOv9patchée, car la substitution de l'ELF seul ne charge pas les quartiers anglais.

Priorités suivantes : tester un nouveau démarrage Tutor homme puis femme, vérifier colonnes et nombres ; poursuivre les conseils d'achat/investissement et les événements non traduits ; relire les abréviations des quartiers puis continuer les magasins et biographies.
