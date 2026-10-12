# Phase 7 — Rules et sous-menus

## Résultat

La nouvelle copie de test est **`phase7/revision3/patched/SLPM_621.12`**.
Elle contient les traductions de phase6/revision3, plus :

- Les **62 chaînes de la table d'explication des règles**, toutes traduites.
- **124 autres chaînes d'interface**, dont plusieurs regroupent des choix de menu.

Ces 124 chaînes ne signifient pas 124 sous-menus complets. Le lot couvre des choix
et messages liés aux adversaires, cartes, tournois, quêtes, réglages, données,
cartes mémoire, personnages entraînés, transferts, saisie de nom et records.
Il ajoute aussi `START: quit` dans le mode Rules. La traduction complète de tous
les écrans du jeu n'est pas achevée : tutoriel contextuel, dialogues de personnages,
casinos, nombreux détails de partie et textes graphiques restent notamment japonais.

## Localisation et format des règles : faits confirmés

Les règles se trouvent dans l'ELF principal, pas dans les textures des cartes :

- Chaînes CP932 de `0x36CB48` à `0x36D7A0`, terminées par NUL.
- Table de 62 pointeurs 32 bits à `0x319230..0x319327`, adresse virtuelle `0x418230`.
- Le consommateur à `0x1B59E8..0x1B5A0C` prend le numéro de texte, le multiplie
  par quatre, charge le pointeur de cette table et appelle le renderer `0x139390`.
- La même routine sélectionne une police de **24 pixels** à `0x1B59C8`, règle la
  fenêtre avec une largeur de **336 pixels**, puis un espacement de **28 pixels**.
- Il s'agit d'un affichage direct : ne pas utiliser les délimiteurs `『...』` du
  formateur d'effets des cartes dans ces explications.

Le script `scripts/analyze_rules.py` a effectué une extraction bornée, recherché
les pointeurs et sauvegardé les quelques fenêtres de désassemblage pertinentes
dans `extracted/phase7/`. Aucune décompilation complète n'a été lancée.

Le parcours explique l'objectif du jeu, les déplacements, les cartes et les suits,
le salaire, les achats et frais des shops, les investissements, les districts et
stocks, les vacant plots, la minimap, les total assets et la victoire. Les petites
chaînes montrant successivement quatre boutiques et le courtier/la banque restent
séparées : ni table ni ordre des événements n'ont été modifiés.

## Traduction et contraintes de place

Les 62 textes sont adaptés à **trois lignes de 14 caractères ASCII maximum**,
sans dépasser les octets de chaque allocation d'origine. Aucun nouveau changement
de police ou de code n'a été ajouté. L'ajustement des listes de menu hérité de
phase5/revision3 est conservé.

Les phrases sont condensées lorsque nécessaire, tout en conservant les mécanismes.
Par exemple : `Get four suits / and visit the / bank for pay.` et `Total assets:
/ cash + shares / + shop values.` Ici `/` indique une séparation de lignes dans
le rapport : ce caractère n'est pas écrit dans le binaire.

Les noms personnels restent majoritairement japonais et le catalogue utilise
`Hikaru` sans inventer une romanisation de son nom de famille. Le terme `trainee`
désigne les personnages créés et entraînés. Les boutons sont appelés Circle,
Cross et START, indépendamment des touches clavier isolées configurées pour le test.

Pour les menus sélectionnés, les types, flags et ordre des paramètres printf
(`%s`, `%d`, `%6d`) sont conservés. Les ressources qui contiennent plusieurs
choix conservent leur nombre de lignes. Le budget de 18 caractères par ligne
pour ces autres écrans est une estimation de sélection, pas une validation
universelle de la largeur de chaque fenêtre. Les noms et autres paramètres
dynamiques peuvent encore nécessiter des ajustements après captures.

## Fichiers de travail

- `translations/rules_en.json` : les 62 traductions des règles, par offset.
- `translations/submenus_en.json` : les 124 autres traductions de ce lot.
- `phase7/revision3/rules_translation.csv` : source japonaise, anglais,
  emplacements, capacités et tailles.
- `phase7/revision3/rules_patch_manifest.json` : octets avant/après et références.
- `phase7/revision3/binary_verification.json` : vérification indépendante PASS.
- `scripts/build_rules_patch.py` : produit la copie, bibliothèque standard seulement.
- `scripts/verify_rules_patch.py` : contrôle chaque plage et le retour à l'original.
- `scripts/launch_translation_test.ps1` : charge désormais **phase7/revision3**.
- `extracted/phase7/rules_01.png` et `rules_shop_fees.png` : captures natives
  PCSX2 de la première révision de phase7, sans retouche.

Les versions précédentes sont conservées ; aucun artefact n'est silencieusement
écrasé par les générateurs. Ne pas charger l'ancienne phase7 directement à la
place de sa révision3 : les anciennes versions ne contiennent pas tous les
raccourcissements et corrections de présentation du lot final.

## Vérifications

Les contrôles indépendants confirment :

- Même taille : **3 923 328 octets**.
- **6 406 octets** différents de la base phase6/revision3, exclusivement dans
  les 186 allocations de chaînes déclarées.
- Table des règles et toutes les références aux chaînes inchangées.
- Aucun changement de la section de code par rapport à la version de base.
- Paramètres printf conservés ; chaînes anglaises lisibles depuis la copie.
- Retour à phase6/revision3, puis à l'original japonais, exact octet pour octet.
- SHA-256 de la copie :
  `9b297f21d71c86719ca7f2a3e37d53fff765a17103841e144e2e703404e981c1`.

Le binaire original et les ISO ne sont ni ouverts en écriture ni reconstruits.
Les dernières empreintes des ISO ont été confirmées dans la phase6 et à nouveau
dans l'audit final de cette phase. Aucun outil supplémentaire n'a été installé.

### Contrôle réel dans PCSX2

Après fermeture par l'utilisateur de l'ancienne session, la première version de
phase7 a été lancée avec l'émulateur isolé et l'ELF hôte. Le mode Rules affiche
bien les nouvelles explications anglaises. Deux captures inspectées confirment
notamment l'introduction et les frais de visite des shops sur trois lignes,
sans débordement visible de ces textes.

Ce contrôle ne signifie pas que les 62 textes ou les 124 autres chaînes ont tous
été inspectés visuellement. La révision2 conserve exactement les mêmes 62 textes
des règles ; elle ajoute l'indication de sortie et raccourcit la confirmation
du choix de Hikaru. L'anglais de ces deux dernières chaînes reste à vérifier.

La révision2 a également été lancée. Son écran de choix des adversaires a révélé
qu'un en-tête sur deux lignes dépassait son bandeau, contrairement aux fenêtres
de dialogue qui acceptent plusieurs lignes. **La révision3 corrige ce point** :
`Pick opponents.` et les autres en-têtes de sélection sont désormais sur une
seule ligne. Le générateur interdit un retour à la ligne pour ces 14 en-têtes.
Leur présentation finale n'a pas encore été revue dans PCSX2. Les 62 textes de
Rules sont identiques dans les trois versions de phase7.

La session éventuellement encore ouverte est celle de la révision2 : fermer
PCSX2 et relancer avec le script commun pour prendre en compte les corrections.

## Tester la version actuelle

Fermer toute session PCSX2 ancienne, puis depuis la racine du projet :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\translation_work\scripts\launch_translation_test.ps1
```

Lancer Rules. Le même lanceur monte l'ISO originale en lecture et charge la copie
de l'ELF via `-elf`, avec `-gameargs "0 0"`. Ne pas remplacer l'ISO ni simplement
l'ouvrir seule : cela chargerait l'exécutable japonais. Les contrôles du test
sont Entrée = START, L = Circle, K = Cross, flèches = navigation.

## Suite recommandée

1. Parcourir entièrement Rules et contrôler les fenêtres de chaque groupe de
   sous-menus, en particulier celles qui insèrent des noms longs.
2. Capturer les écrans encore japonais avec leur chemin de navigation : cela
   permet de distinguer les chaînes de menus, dialogues et textes intégrés aux images.
3. Étendre la traduction par lots identifiés, en conservant la vérification des
   paramètres et des allocations, avant toute reconstruction future d'ISO.
