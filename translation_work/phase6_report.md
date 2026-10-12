# Phase 6 — Traduction anglaise élargie

État historique : la version de test courante est désormais décrite dans
`phase7_report.md`, et le lanceur commun charge phase7/revision3.

## Résultat actuel

Version à tester : `phase6/revision3/patched/SLPM_621.12`, et non les versions
situées dans `phase6/patched/`, `phase6/revision2/` ou les anciennes phases 4/5.

| Contenu | Entrées traduites dans la copie | Brouillons non intégrés |
| --- | ---: | ---: |
| Résumés des cartes Chance | 177 sur 185 textes non nuls | 8 |
| Messages d'effets et dialogues associés | 129 sur 140 textes distincts | 11 |
| Messages de sauvegarde/chargement | 30 sur 30 sélectionnés | 0 |
| Menu principal et premières sélections, hérités de phase 5 | 28 | — |
| Sous-menu d'entraînement : six libellés et une description | 2 chaînes, 7 textes visibles | 0 |

Les 177 résumés couvrent des numéros de cartes, pas 177 chaînes distinctes :
quatre paires utilisent le même texte. Les 129 messages détaillés couvrent
132 entrées d'une table de 143 entrées, dont certaines partagent un pointeur.
Cette phase écrit 334 emplacements distincts. Ces nombres ne constituent pas
un pourcentage de traduction de tout le jeu : dialogues, tutoriel, casinos,
nombreux autres menus et textes graphiques restent notamment à traiter.

Tous les résumés non nuls ont une proposition anglaise complète dans le catalogue,
y compris ceux qui ne peuvent pas encore être intégrés. La carte C046 possède
un pointeur nul : aucun texte n'a été inventé pour elle.

## Livrables

- `translations/cards_en.json` : 185 traductions complètes et premières versions courtes.
- `translations/details_en.json` : 119 traductions de messages extraits précédemment.
- `translations/details_extra_en.json` : 21 autres messages retrouvés dans la table.
- `translations/save_ui_en.json` : 30 messages de sauvegarde/chargement.
- `translations/training_ui_en.json` : un groupe de six choix et une description,
  repérés directement dans la fenêtre PCSX2.
- `translations/compact_overrides_en.json` : formulations abrégées supplémentaires.
- `phase6/revision3/translation_catalog.csv` et `.json` : japonais source, anglais
  complet, anglais proposé pour l'affichage, offset, capacités, état et motifs de rejet.
- `phase6/revision3/translation_manifest.json` : chaque plage modifiée, octets
  d'origine, octets de la version de base et octets remplacés ; permet un retour exact.
- `phase6/revision3/binary_verification.json` : contrôles indépendants, résultat PASS.
- `scripts/build_translation_batch.py` et `verify_translation_batch.py` : génération
  reproductible et vérification, bibliothèque standard Python uniquement.
- `scripts/launch_translation_test.ps1` : lancement PCSX2 isolé avec cette copie.

Les scripts refusent d'écraser un artefact existant avec un contenu différent.
Pour une nouvelle révision, choisir un autre dossier de sortie et adapter le
vérificateur/lanceur et son empreinte attendue.

## Méthode et protection du jeu

Le texte est remplacé dans une copie de l'exécutable principal, en conservant
strictement les allocations d'origine, terminaison NUL comprise. Aucun déplacement
de chaîne, changement de pointeur, modification des textures TI ou reconstruction
d'ISO n'a été effectué. La version de base est la phase5/revision3 : ses traductions
de menu et son unique ajustement de police 20→16 pixels sont conservés. Cette
phase n'ajoute aucune modification de code exécutable.

Pour les messages d'effets, le formateur du jeu traite certaines lettres ASCII
comme des commandes. Les parties anglaises littérales sont donc entourées des
délimiteurs japonais `『...』`, qui ne doivent pas apparaître à l'écran. Les
paramètres `{P}`, `{p}`, `{G}`, `{g}`, `{S}`, `{E}` du catalogue sont transformés
en commandes du jeu. Le vérificateur prouve leur conservation dans le même ordre
et reconstitue exactement le texte anglais à partir des tokens. Les `%%` d'origine
sont conservés. Les messages de sauvegarde utilisent des chaînes simples, dont
les paramètres printf éventuels `%d` sont conservés en nombre, type et ordre.

La table des effets contient 143 couples de mots de 32 bits à partir de
`0x3188D8` : un mot de présentation puis un pointeur. Les 119 chaînes du premier
audit n'étaient pas une liste de 119 identifiants consécutifs de cette table !
Des pointeurs partagés décalent la correspondance. Le catalogue final enregistre
les vrais `detail_table_ids` de chaque offset. Aucun texte n'a été associé à une
carte en se fondant uniquement sur sa position dans l'audit.

La région de sauvegarde examinée est limitée à `0x359128..0x3597FF`. Le reste de
l'ELF n'a pas été traduit par remplacement automatique de chaînes japonaises.
Un repérage borné de chaînes d'autres menus a été effectué, sans modification
des tables de saisie de caractères ni des noms de personnages.

## Choix de traduction et limites

La traduction complète vise un anglais naturel et conserve les effets économiques :
montants, proportions, nombre de tours, bénéficiaire et action. Les résumés courts
sont condensés pour l'interface et peuvent omettre des éléments de narration ;
le catalogue conserve la version développée. Exemples : `Roll again!`, `Sell at
3x value`, `Get roll / x11G / per foe!`, `Pay 100G / Warp: no / Chance!`.
Dans ces exemples, `/` représente une séparation de lignes, pas un caractère du
fichier modifié.

Les noms propres sont provisoires : notamment Waku-Waku Rope, Holidemon,
Suit Angel, Mermaid Bridge, Moonlight, Huckleberry Market et Thecodont Pottery.
Ils sont basés sur le japonais local, pas sur une nomenclature anglaise officielle
vérifiée. Il faudra harmoniser la terminologie avec les cartes, personnages et
dialogues avant diffusion. Les 140 messages détaillés n'ont pas une correspondance
un-à-un avec les 186 cartes : plusieurs effets/dialogues sont partagés.

Budget de travail pour les résumés : trois lignes de huit caractères ASCII maximum.
Pour les effets : trois lignes, estimation maximale de 24 caractères, avec tailles
nominales pour les paramètres. Pour la sauvegarde : cinq lignes de 18 caractères.
Ce sont des critères de sélection conservateurs, pas une preuve d'affichage sans
débordement. Les noms réels, certains montants et les dimensions de chaque fenêtre
doivent être contrôlés en jeu.

Résumé des éléments non intégrés :

- Cartes 112, 119, 120, 136, 148, 150, 172, 178 : taille en octets ou budget de lignes.
- Messages d'audit 10, 11, 12 : le `G` non protégé du japonais source est interprété
  comme un paramètre par le modèle de formateur ; le changer en unité littérale
  sans vérifier le comportement réel pourrait modifier la sémantique du message.
- Messages d'audit 60, 68, 88, 95, 115, 116 et offsets `0x36C158`, `0x36C1B0` : taille.

Ces chaînes restent identiques à la version de base dans le binaire. Elles ne sont
ni tronquées ni écrites sur les données suivantes.

## Vérifications effectivement effectuées

Le vérificateur indépendant contrôle chaque plage, les octets avant/après, les
paramètres, la lecture anglaise du formateur, les tables de pointeurs complètes et
l'absence de modifications hors des plages autorisées. Le retour en mémoire à la
version phase5 puis à l'original japonais réussit octet pour octet.

- Taille de l'ELF : 3 923 328 octets, inchangée.
- Différences par rapport à phase5/revision3 : 11 446 octets.
- SHA-256 de la copie anglaise :
  `caf7931bcf43c87de8c2363dedd05fff0cbe7fbe720bbdcb80af658d0f687889`.
- SHA-256 original ELF :
  `d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5`.
- Les deux ISO sont inchangées et conservent l'empreinte :
  `6e8e471f9b6aef1af78b9cf99407ffd9adaa2c51a871f622dd84db140404dcab`.

La révision 2 a été démarrée avec PCSX2 isolé : l'écran-titre et le menu principal
anglais sont atteints ; capture native conservée dans `extracted/phase6/main_menu.png`.
La révision 3 ajoute uniquement les deux chaînes du sous-menu d'entraînement,
dont l'affichage anglais reste à vérifier ; ses contrôles binaires passent.
La session laissée ouverte est celle de la révision 2 : fermer PCSX2 puis utiliser
le nouveau lanceur pour charger la révision 3. Le titre
graphique reste japonais, ce qui est attendu car ses textures n'ont pas été
retouchées. Ce démarrage ne valide pas les 177 cartes et 129 effets ; un test de
chaque type de fenêtre et des noms/montants longs reste nécessaire.

## Utiliser la nouvelle version

Depuis la racine du projet dans PowerShell, avec PCSX2 fermé :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\translation_work\scripts\launch_translation_test.ps1
```

Ce lanceur utilise `translation_work/phase4/pcsx2_runtime/pcsx2-qt.exe`, copie
isolée de l'émulateur fourni, et son dossier de configuration/cartes mémoire de
test. Il monte l'ISO originale en lecture et charge l'ELF traduit depuis le disque
Windows avec `-elf`. `-gameargs "0 0"` évite l'introduction qui rechargerait
l'exécutable japonais depuis l'ISO. Les contrôles isolés : Entrée = START,
L = cercle/valider, K = croix, flèches = navigation, F8 = capture.

Il ne faut appliquer aucun de ces fichiers à l'ISO à cette étape. La simple
ouverture de l'ISO seule dans PCSX2 ne charge pas cette nouvelle traduction.
Un éventuel rechargement de l'exécutable depuis le disque plus tard dans le jeu
reste à vérifier.

## Prochaines priorités

1. Tester les cartes et effets représentatifs avec noms/montants longs, puis corriger
   l'anglais compact et les retours à la ligne à partir de captures réelles.
2. Résoudre les 19 brouillons non intégrés : raccourcissement fidèle, investigation
   des trois anciens messages `G`, ou déplacement contrôlé des textes si nécessaire.
3. Identifier les chemins d'affichage des autres menus, règles, casinos et dialogues,
   puis poursuivre par lots bornés avec le même catalogue et les mêmes contrôles.
