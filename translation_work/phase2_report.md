# Phase 2 — Pointeurs et correspondance des cartes

## Résultat confirmé et correction de la phase 1

La table des résumés contient **186 emplacements de cartes**, et non une correspondance directe entre les 180 chaînes contiguës et les 180 premiers fichiers. Le premier rapport extrapolait à tort cette correspondance à partir de `C033`, qui est situé avant le premier décalage. Les données de cette phase remplacent cette conclusion.

La table de pointeurs occupe `0x3185E0..0x3188C7` dans `SLPM_621.12` : 186 mots little-endian de 32 bits, soit 744 octets. Son adresse en mémoire est `0x004175E0`. Chaque emplacement est associé au numéro de carte par le code qui soustrait 1 au numéro, multiplie par 4, puis charge le pointeur. Cette logique est visible aux offsets fichier `0x39C74..0x39CA8`; le relevé annoté est fourni dans `extracted/phase2/table_consumer.asm`.

## Conversion entre offset fichier et adresse PS2

L'exécutable est ELF32 little-endian MIPS. Son segment `PT_LOAD` commence à l'offset fichier `0x1000`, avec l'adresse virtuelle `0x00100000`, une taille fichier `0x3B9204` et une taille mémoire `0x493AAC`. Pour les octets chargés depuis ce segment :

```text
adresse virtuelle = offset fichier + 0x000FF000
offset fichier = adresse virtuelle - 0x000FF000
```

Les pointeurs contiennent des adresses virtuelles, pas des offsets fichier. La table est dans `.data`, les 180 chaînes contiguës dans `.rodata`; la chaîne de `C040` est dans `.sdata`.

La routine consommatrice lit une valeur à l'adresse `0x003E7EE8`, la transforme en index `(valeur − 1) × 4`, consulte la table et passe le texte en registre `a1` à la routine `0x00177F38`. La nature exacte de cette dernière routine et la façon dont la valeur courante est alimentée restent à documenter. L'indexation constitue néanmoins une preuve directe de la structure de la table; elle dépasse la simple concordance des illustrations.

## Correspondance établie

| Carte | Pointeur stocké | Offset du texte | Observation |
|---|---|---|---|
| C001 | `0x00468470` | `0x369470` | premier résumé |
| C033 | `0x004688F8` | `0x3698F8` | remboursement à trois fois la valeur |
| C040 | `0x004B8E08` | `0x3B9E08` | `大洪水!`, hors du bloc contigu |
| C046 | `0x00000000` | aucun | pointeur nul |
| C090 | `0x004686F8` | `0x3696F8` | même texte que C019 |
| C149 | `0x004694A0` | `0x36A4A0` | même texte que C132 |
| C170 | `0x00469888` | `0x36A888` | même texte que C169 |
| C180 | `0x004699A8` | `0x36A9A8` | éruption volcanique |
| C181 | `0x004699B8` | `0x36A9B8` | déplacement vers une banque |
| C182 | `0x004699D0` | `0x36A9D0` | déplacement vers une autre banque |
| C183 / C184 | `0x004699E8` | `0x36A9E8` | texte partagé, fantôme |
| C185 | `0x00469A00` | `0x36AA00` | apparition d'un fantôme |
| C186 | `0x00469A20` | `0x36AA20` | fantômes faisant la fête |

Bilan : 186 emplacements, 185 pointeurs non nuls, **181 adresses de chaînes distinctes**, dont 180 dans le bloc identifié précédemment et une ailleurs. Quatre paires partagent un pointeur : C019/C090, C132/C149, C169/C170 et C183/C184. C046 nécessite une étude du traitement du pointeur nul avant de décider comment la traduire.

Quatre pointeurs supplémentaires après les 186 cartes pointent sur une chaîne vide à `0x004B8E10`, puis une autre table commence. Leur rôle n'est pas établi; ils ne sont pas inclus comme cartes supplémentaires puisque seules 186 textures existent.

## Texte et paramètres

Les résumés se décodent strictement en CP932, sont terminés par NUL et contiennent des sauts de ligne `0x0A`. Aucun décodeur propriétaire n'est nécessaire pour obtenir leur japonais.

Une extraction partielle de **119 chaînes détaillées** dans `0x36AA48..0x36BFFF` figure dans `references.json`, avec leurs octets hexadécimaux. La dernière chaîne incomplète est exclue. Ce bornage ne définit pas la fin de tous les messages du jeu : il sert à étudier une zone directement adjacente sans analyser tout l'exécutable.

Les messages détaillés comprennent des motifs tels que `Pさん`, `G『G』`, `g『G』`, `Eの`, `Sの` et `%%`. Il est probable que certaines lettres représentent des variables (joueur, montants, district, boutique), mais leur fonction n'est pas prouvée par la seule présence de ces motifs. Le double `%` évoque aussi un traitement de formatage. Aucune traduction ou substitution automatique de ces marqueurs n'a été entreprise.

## Conséquences pour la réinjection

1. Pour remplacer un texte à une nouvelle adresse, mettre à jour **toutes les entrées qui partagent son pointeur**, ou décider explicitement de les séparer.
2. Les 181 adresses de textes peuvent être traitées indépendamment des 186 numéros de cartes. Le catalogue fournit les deux niveaux.
3. Pour une première expérience de réécriture en place, utiliser comme limite sûre `byte_length + 1` (NUL compris). Les zéros observés après le NUL sont exportés sous `nul_and_padding_capacity`, mais ne constituent pas à eux seuls une preuve que cet espace est libre de toute autre référence.
4. Une relocalisation exige une nouvelle adresse virtuelle valide dans un segment chargé. Une simple insertion d'octets dans l'ELF déplacerait sections et données; elle ne doit pas être utilisée sans adaptation des structures ELF.
5. Le pointeur nul de C046, la police et les paramètres dynamiques doivent être compris avant un patch général.

## Fichiers et reproduction

- `scripts/analyze_card_references.ps1` : analyse ELF et recherche de références, en lecture seule, via PowerShell et un petit scanner C# local compilé en mémoire.
- `extracted/phase2/references.json` : segment chargé, 180 chaînes contiguës, références brutes, candidats MIPS et 119 messages détaillés.
- `extracted/phase2/summary_pointers.csv` : occurrences brutes des adresses des 180 chaînes. Une occurrence non alignée dans le code est un candidat fortuit et n'est pas utilisée pour définir la table.
- `extracted/phase2/card_mapping.json` et `.csv` : correspondance des 186 cartes déduite de la table réelle.
- `scripts/extract_card_text.py` et `extracted/card_text_ja.json` : corrigés pour représenter 186 emplacements, avec texte nul pour C046.

Reproduction :

```powershell
.\translation_work\scripts\analyze_card_references.ps1
```

Validation effectuée avec Python 3.12 déjà installé localement, trouvé sans réseau par `uv --no-cache python find --offline`. L'extraction Python corrigée et l'analyse PowerShell/C# concordent pour les 186 entrées sur les numéros, emplacements des pointeurs, adresses virtuelles, offsets des textes, longueurs, textes et statuts. Le script `scripts/verify_phase2.py` contrôle également les quatre paires partagées et les cas C040/C046. SHA-256 de l'ELF analysé : `d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5`.

Les fichiers d'origine ont uniquement été lus. Aucune ISO n'a été reconstruite et aucune traduction n'a été réinjectée.

## Prochain travail ciblé

Suivre la routine `0x00177F38` et les appels des messages détaillés pour documenter le formatage, vérifier le traitement du pointeur nul de C046, puis mesurer les glyphes latins et l'espace disponible dans PCSX2. Le déplacement des chaînes pourra alors être préparé sur une copie de l'ELF avec une correspondance fiable pour toutes les cartes.
