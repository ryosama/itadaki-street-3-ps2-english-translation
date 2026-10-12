# Phase 3 — Affichage, formatage et cas C046

## Résultats

L'analyse ciblée des routines MIPS confirme le traitement du pointeur nul de C046, le chemin d'affichage des résumés et un langage de substitution propre aux messages détaillés. Les fichiers originaux ont uniquement été lus; aucune traduction ou ISO de test n'a été produite.

Les adresses ci-dessous sont des **adresses virtuelles PS2**. Pour cet exécutable, l'offset fichier correspondant est `VA − 0xFF000`.

## 1. Résumés et pointeur nul

Le chemin d'affichage des résumés est :

```text
table 0x4175E0, index (carte − 1)
  → pointeur texte en a1
  → 0x177F38 (couleur + position)
  → 0x178038 (parcours et dessin des caractères)
```

La routine `0x177F38` conserve le texte, règle la couleur via `0x177E88`, appelle la méthode de positionnement du descripteur de police, puis saute vers `0x178038`. Dans cette dernière :

- `0x1780E0` : `beq s1,zero,0x178348`, avant toute lecture de caractère;
- `0x1780F0` : première lecture `lb` du texte, uniquement si le pointeur n'est pas nul;
- `0x178348..0x178374` : restauration des registres et retour.

**Conclusion confirmée :** un pointeur nul produit aucun dessin de texte dans ce chemin. C046 n'exige donc pas d'inventer une chaîne pour éviter un accès nul. Cela ne prouve ni que cette carte est inutilisée, ni ce que fait son effet de jeu; son traitement dans la logique des cartes reste à vérifier séparément.

La routine parcourt les caractères jusqu'au NUL. Elle traite explicitement `0x0A` comme un retour à la ligne : remise à zéro relative de X, puis avancement de Y selon l'interligne. Elle traite l'espace ASCII `0x20` et l'espace japonais `0x8140` sans dessiner de glyphe.

Il n'y a pas de découpage automatique des lignes ni de test de largeur dans cette boucle. La traduction doit prévoir ses propres sauts de ligne. Un éventuel clipping ailleurs dans le pipeline n'a pas été exclu.

## 2. Police et lettres anglaises

Le résumé utilise l'objet de police à `0x23C320`. Son initialisation à `0x101058..0x101070` lui passe une largeur et une hauteur de 24. Le constructeur `0x178510` installe la table de méthodes `0x4570B0` et sélectionne la variante 24 × 24.

Le décodage des glyphes passe par `0x178600`, qui consulte les fonctions à `0x30CDC8`. Pour la variante 24 × 24, la fonction sélectionnée est `0x177AB0`. Celle-ci appelle `0x177988` pour convertir les caractères en indices de glyphes.

Dans `0x177988`, les caractères à un octet non négatifs donnent l'indice `octet − 32`. Les ASCII imprimables `0x20..0x7E` disposent donc d'un chemin de sélection dans la police. Ce résultat confirme le support du codage ASCII dans le moteur; la présence visuelle de tous les glyphes dans les textures de police doit encore être contrôlée.

Deux tables d'espacement signées sont présentes à `0x457320` et `0x457380`. Leur usage est conditionné par l'octet `objet + 0x54`. Si cette option est active, le renderer ajuste X avant et après le dessin selon une échelle divisée par 24. Les 95 métriques ASCII sont extraites dans `ascii_metrics.csv`.

Cette option vaut zéro lors de l'initialisation; le mode initial est donc à avance fixe, correspondant à la largeur du caractère. Un changement ultérieur reste possible. Les métriques proportionnelles ne doivent pas être appliquées systématiquement à tous les écrans sans vérifier ce drapeau au moment de l'affichage.

Le résumé est positionné avec `x = s3 − 96`, `y = 216` dans l'appel à `0x138CA4`. La largeur maximale de la zone, l'interligne effectif et le clipping ne sont pas encore mesurés dans PCSX2. La présence habituelle de trois lignes dans les résumés sources est une observation, pas une limite codée démontrée.

## 3. Messages détaillés : table distincte

Les appels à `0x1A12AC` et `0x1A1354` montrent une autre table à `0x4178D8` (offset fichier `0x3188D8`) : les entrées font **8 octets**, pas 4. Pour un identifiant de message :

- le mot à `entrée + 4` est le pointeur vers le modèle de texte;
- le mot à `entrée + 0` est passé comme second argument à une routine de présentation; son rôle exact n'est pas identifié;
- le modèle est transformé par `0x136FD0`, puis présenté via `0x1A0B40`.

Les identifiants de messages détaillés ne sont donc pas directement les numéros des cartes. Une carte peut déclencher plusieurs messages partagés.

## 4. Langage de substitution confirmé

`0x136FD0` prépare des données temporaires, appelle `0x136E98`, puis cette routine appelle le formateur **`0x136AC0`**. Les tables de saut à `0x44DA30` et `0x44DA70` déterminent les états et les commandes. Leur extraction est dans `format_tables.json`.

En mode normal, les lettres suivantes sont des commandes et ne sont pas copiées littéralement :

| Lettre | Action confirmée | Interprétation du contenu |
|---|---|---|
| `A`, `B`, `C` | consomme l'octet suivant et écrit sa valeur moins 48 dans un des trois emplacements de sélection | indices de sélection; le prototype exige un chiffre ASCII |
| `P`, `p` | copie une chaîne obtenue par `0x14AAA0` à partir de deux valeurs de paramètres | noms de joueurs, très probable d'après les objets et les textes |
| `G`, `g` | formate un entier avec `%d` à partir de deux valeurs de paramètres | montants/nombres, confirmé |
| `S`, `s` | copie une chaîne obtenue par `0x144AD8`, via une table à pas de 160 octets | noms de boutiques, très probable |
| `E`, `e` | copie une chaîne obtenue par `0x147338`, via une table à pas de 520 octets | noms de districts, très probable |

Les majuscules et minuscules sélectionnent les emplacements 0 et 1 de chaque paire. La signification précise des trois valeurs de sélection A/B/C dans les dialogues doit encore être suivie dans les consommateurs.

### Écriture littérale

Le formateur reconnaît les octets CP932 :

- `81 77` (`『`) : passe en mode littéral;
- `81 78` (`』`) : revient au mode normal.

Les délimiteurs sont consommés et ne sont pas envoyés au renderer. Dans le mode littéral, les lettres réservées sont copiées sans substitution.

Exemple source déjà présent : `G『G』` produit la valeur numérique du paramètre G suivie de la lettre G. Le second G est littéral parce qu'il est protégé par les délimiteurs.

**Conséquence majeure pour l'anglais :** une phrase ordinaire comme `Pay ...` envoyée au formateur déclencherait P et d'autres lettres réservées. Pour les messages détaillés, chaque segment de prose anglaise doit être protégé avec `『…』`, en laissant les paramètres dynamiques en dehors. Ce mécanisme ne doit pas être appliqué aux résumés : ils passent directement au renderer et afficheraient les délimiteurs.

Le `%` ne possède aucune entrée spéciale dans la table de commandes. Les `%%` observés ne sont donc pas une preuve de formatage printf de tout le modèle. La seule utilisation de `%d` démontrée ici concerne la conversion des paramètres G/g. L'origine et le traitement éventuel de `%%` ailleurs dans le pipeline restent à vérifier avant de les normaliser.

### Longueur après substitution

La boucle copie les modèles et leurs substitutions dans le tampon de sortie sans contrôle explicite de capacité dans la routine étudiée. Le consommateur observé réserve 304 octets de pile; le tampon est passé depuis `sp` et les premières sauvegardes de registres commencent à `sp + 256`. Un résultat atteignant ces sauvegardes serait dangereux. Ce constat ne donne pas une capacité universelle garantie de 256 octets pour tous les appels, mais impose de contrôler la longueur **après expansion**, y compris le NUL et les noms et nombres maximaux.

## 5. Outils et validation

- `scripts/inspect_mips.py` : décodeur ciblé standard-library. Les instructions inconnues restent `.word`; il ne prétend pas remplacer un désassembleur R5900 complet. Il prend en compte le résultat dans `rd` de MULT/MULTU propre au R5900.
- `scripts/analyze_phase3.py` : recherche des références et appels dans `.text`, extraction des métriques ASCII. Les correspondances LUI/immédiat restent des candidats tant que le flux n'est pas examiné.
- `scripts/inspect_phase3_windows.py` : génération reproductible des fenêtres de code étudiées.
- `scripts/extract_format_tables.py` : tables de commandes, états, délimiteurs et variantes de glyphes.
- `scripts/message_format.py` : prototype de tokenisation des modèles et protection des segments littéraux. Il ne remplace pas les callbacks de noms du jeu.

Les **119 messages détaillés extraits en phase 2** ont été analysés sans erreur de tokenisation. Le prototype conserve les commandes et distingue le G numérique du G littéral dans `G『G』`. Les vérifications couvrent aussi l'échappement d'une phrase anglaise, un sélecteur A2 et le traitement littéral de `%%`.

Les observations sont fondées sur le code et les tables du fichier SHA-256 `d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5`. Aucun test dans PCSX2 n'a été effectué pendant cette phase.

## 6. Préparation de la réinjection

Les informations acquises permettent de préparer deux chemins distincts :

1. **Résumés :** anglais CP932/ASCII, NUL final, retours à la ligne explicites et pointeurs partagés conservés. C046 reste nul tant que la logique de carte ne justifie pas de lui attribuer un texte.
2. **Messages détaillés :** prose littérale protégée, paramètres et sélecteurs préservés, correspondance par identifiant de message et longueur d'expansion contrôlée pour chaque tampon appelant.

La prochaine expérience recommandée est un test sur copie de l'ELF avec un résumé court, puis un message détaillé contenant un montant et un nom. Avant la réinjection, il reste à choisir une stratégie de stockage des chaînes plus longues et à mesurer dans PCSX2 la zone disponible et les glyphes. Les scripts actuels n'écrivent aucun patch.
