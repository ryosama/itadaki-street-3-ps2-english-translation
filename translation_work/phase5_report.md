# Phase 5 — Menu anglais et conservation de l'ELF de test

## Périmètre

Analyse des trois captures fournies dans `captures d'écran/menu principal`, traduction expérimentale du menu, puis test dans PCSX2 2.8.2. Tous les nouveaux fichiers sont sous `translation_work`. Les ISO, ressources extraites et captures fournies ne sont ni remplacés ni reconstruits. Les trois résumés Chance et le message de revenu de la phase 4 sont conservés dans cette copie.

## 1. Retour d'introduction : solution sans patch de code de démarrage

Le lancement de phase 4 exécute d'abord l'ELF patché, puis `MOVIE.ELF`, qui recharge `cdrom0:\SLPM_621.12;1` depuis l'ISO original. Le remplacement `-elf` ne persiste pas à travers ce retour.

L'analyse ciblée du programme principal montre une alternative existante :

- `0x100098..0x1000A8` transmet le nombre d'arguments à la fonction principale `0x100148`.
- `0x100154` conserve ce nombre dans `s1`.
- `0x1001B4..0x1001C0` compare `s1` à 3. Si égal, le programme sélectionne l'état initial 17 (`0x11`) plutôt que 10 (`0x0A`).
- Le pointeur d'arguments n'est pas conservé dans ce chemin de la fonction principale. Le test utilise deux chaînes neutres `0 0`, pas des pointeurs ou données de sauvegarde inventés.

La commande `-gameargs "0 0"`, ajoutée au lancement avec `-elf`, fait emprunter cette voie existante. Le journal confirme `Supplying launch argument(s) '0 0'` et l'exécution de l'ELF hôte. Le premier test atteint directement l'écran-titre et le menu anglais sans charger `MOVIE.ELF`. Le message d'accueil anglais prouve également que la copie modifiée reste active au menu. Aucune instruction du démarrage n'a été modifiée.

Cette méthode est un protocole de test PCSX2, pas une solution finale pour un disque traduit : un disque de test traduit devra contenir l'ELF traduit au chemin que recharge la vidéo. Aucune ISO n'est reconstruite à cette étape. Les vidéos éventuellement accessibles plus tard peuvent encore recharger l'ELF original.

## 2. Localisation confirmée des textes du menu

Les libellés des captures sont des chaînes CP932 terminées par NUL dans l'ELF principal, pas du japonais peint dans le décor.

| Ensemble | Table, offset fichier | Organisation |
|---|---|---|
| 8 choix du menu principal | `0x300CF8` | pointeurs 32 bits, NUL terminal à `0x300D18` |
| 4 nombres de joueurs | `0x2FF6E0` | pointeurs vers quatre chaînes |
| 4 opérations sur les données | `0x2FFECC` | pointeurs, NUL terminal à `0x2FFEDC` |
| 8 descriptions de modes | `0x31AA20` | un pointeur par choix du menu principal |

Le mapping de ce programme est `adresse virtuelle = offset fichier + 0xFF000` pour ces ressources. Les libellés principaux commencent à `0x360670`, les descriptions à `0x370E50`.

Le constructeur de liste vers `0x1C01EC` parcourt les pointeurs, concatène les chaînes dans un tampon de 128 octets par groupe, puis transmet la liste à `0x139390`. La nouvelle liste principale conserve ses sept sauts de ligne et reste plus courte en octets que la liste d'origine. Les descriptions passent également par `0x1BCDF0 → 0x139390`. Ce chemin ne passe pas par le formateur dynamique des cartes Chance : les libellés anglais ne sont donc **pas** entourés de `『…』`.

Le moteur de fenêtre gère aussi des commandes avec `/`. Les textes proposés n'utilisent pas ce caractère. Les limites des tampons et les références partagées sont conservées dans le manifeste.

## 3. Traductions de test

| Japonais | Anglais des révisions 2 et 3 |
|---|---|
| フリープレイ | Free Play |
| 家庭教師モード | Tutor Mode |
| トーナメント | Tournament |
| 育成モード | Training |
| いただきクエスト | Quest |
| データをみる | Records |
| ルール説明 | Rules |
| ゲームをおわる | Quit Game |

La copie finale de test est la **révision 3**, dans `phase5/revision3/patched/SLPM_621.12`. Son sous-menu des données utilise `View`, `Erase`, `Load`, `Save` ; les deux derniers ont été raccourcis pour la largeur disponible. Le contexte « Records » précise ce qui est consulté ou effacé. Les petits libellés joueurs deviennent `1P`, `2P`, `3P`, `4P` pour tenir dans les allocations d'origine. L'invite finale est `Players?`, raccourcie parce que `How many players?` atteignait le bord droit dans le test de révision 2. Les lettres P ici sont littérales, contrairement au formateur des messages Chance.

Les huit descriptions sont traduites ainsi que l'accueil et trois invites, soit **28 chaînes**. Les traductions sont dans `phase5/revision3/menu_translation.csv`. « Training » reste une dénomination à affiner après examen du mode de développement des personnages ; « Tutor Mode » préserve la notion de professeur particulier, plutôt que de présenter arbitrairement ce mode comme un simple tutoriel.

Certains libellés joueurs sont partagés avec d'autres listes : par exemple `ひとり\n` est aussi référencé à `0x2FED78`. Les changements s'appliquent donc aux références partageant exactement la même chaîne. Toutes les références de pointeurs alignées trouvées sont consignées, sans prétendre couvrir toutes les références indirectes.

L'invite `どれにしますか？` à `0x363710` est traduite en `Which option?`, mais son association exacte au sous-menu des données de la capture doit être vérifiée à l'écran. Les messages système de chargement, les écrans de sélection suivants, les confirmations d'effacement et l'ensemble des règles ne sont pas encore traduits.

## 4. Mise en page : première version rejetée, révision 2

La première copie dans `phase5/patched` démontre le rendu ASCII mais fait déborder `Tutor Mode`, `Tournament` et surtout `Itadaki Quest` du menu. Elle est conservée comme expérience, **pas comme version validée**.

La révision 2 utilise des descriptions de trois lignes courtes lorsque nécessaire et le libellé `Quest`. Elle change un seul sélecteur de police dans une copie du code :

| Offset fichier | Adresse virtuelle | Avant | Après |
|---|---|---|---|
| `0xC11C8` | `0x1C01C8` | `addiu a2,zero,20` (`0x24060014`) | `addiu a2,zero,16` (`0x24060010`) |

Ce paramètre est transmis à `0x139428`, stocké dans l'objet de fenêtre à `+0x128`, puis sélectionne la police 16 dans `0x1394DC..0x139510`, au lieu de la police 20. Il ne modifie ni les textures de police ni le renderer ASCII global. Ce constructeur est générique et contient d'autres groupes de menus : son changement de police peut aussi toucher les listes construites par ce même helper. Ces autres listes devront être contrôlées avant une traduction distribuable.

Les descriptions gardent la police d'origine et sont reformatées en lignes courtes ; le support ASCII est visuellement confirmé par le message d'accueil du premier test. Le mode proportionnel global n'a pas été activé.

## 5. Vérification binaire et artefacts

Les révisions 2 et 3 contiennent chacune exactement **663 octets différents de la copie phase 4**, dont un seul octet dans le code pour le sélecteur de police. Aucun pointeur n'est déplacé. Les 28 plages de chaînes conservent leur capacité initiale et sont complétées par des NUL. Les quatre patches de phase 4 restent identiques. La révision 3 ne change que trois chaînes de la révision 2 : l'invite joueurs, Load et Save ; le menu principal, ses huit descriptions, les labels joueurs et le sélecteur de police sont identiques aux octets de la version observée à l'écran.

`verify_menu_patch.py` relit les textes, contrôle les références, vérifie le diff intégral et reconstruit en mémoire l'ELF original à partir des octets conservés dans les deux manifestes. Résultat : reconstruction exacte, aucun changement non autorisé dans le diff.

- ELF original : `d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5`.
- ELF révision 2 : `9c7b68f64649e32da01ae14c0a47e09dfc7c5a7be2b9519101496162ea658826`.
- ELF final de test, révision 3 : `7ca5c38cfb1c629a91abbe3a78e4d2f54fbad0bacd8c5e62ba702d3cfbb0501c`.
- Taille inchangée : 3 923 328 octets.

Fichiers principaux :

- `scripts/analyze_phase5.py` : recherche ciblée et fenêtres MIPS ; `extracted/phase5/targeted_analysis.json` conserve les résultats.
- `scripts/build_menu_patch.py` : construction reproductible de la révision 3 ; les expériences antérieures restent conservées.
- `scripts/verify_menu_patch.py` : vérification indépendante et restauration en mémoire.
- `scripts/launch_menu_test.ps1` : lancement PCSX2 isolé, arguments `0 0`, ELF révision 3 et ISO original.
- `scripts/send_pcsx2_test_key.ps1` : une entrée à la fois, uniquement si la fenêtre appartient au programme de test isolé ; aucune interaction avec les menus d'effacement.
- `scripts/collect_menu_capture.py` : copie sans retouche des captures PNG natives de PCSX2.
- `phase5/revision3/menu_patch_manifest.json`, `menu_translation.csv`, `binary_verification.json`, `argc_boot_selection.asm`.
- `phase5/pcsx2_menu_runtime.log` : première version ; `phase5/revision2/pcsx2_menu_runtime.log` : version corrigée.

Le dossier de données isolé préparé en phase 4 est réutilisé. La configuration de test ajoute les touches clavier : Entrée = Start, L = confirmation/Circle, K = retour/Cross, flèches = navigation, F8 = capture. Elle ne change pas les commandes de l'installation habituelle. Les copies BIOS/cartes mémoire déjà présentes ne sont pas écrasées par la préparation.

## 6. Validation dynamique et limites

La première version confirme le démarrage direct sans introduction, le message d'accueil anglais et la présence des huit labels anglais ; elle démontre aussi les débordements qui motivent la révision 2.

La révision 2 a été effectivement exécutée et ses captures natives PCSX2 ont été relues :

| Capture sous `extracted/phase5` | Observation confirmée |
|---|---|
| `menu_prompt_en.png` | huit labels anglais dans la fenêtre et `Choose a mode.` |
| `main_menu_en.png` | curseur Free Play, huit labels sans débordement visible, description anglaise sur trois lignes |
| `players_menu_en_revision2.png` | fenêtre `1P` à `4P`, invite anglaise, mais invite longue proche du bord droit |

Le journal révision 2 contient un seul chargement d'ELF hôte, avec les arguments `0 0`, et aucun chargement de `MOVIE.ELF` ou retour à l'ELF original pendant la session observée. La session s'est ensuite fermée ; la cause de cette fermeture n'est pas établie par l'analyse. Aucun sous-menu d'effacement ou de sauvegarde n'a été confirmé/exécuté par le script de test.

**Non validés visuellement :** sous-menu des données, sept autres descriptions de modes, effets du sélecteur de police sur les autres groupes, et les trois chaînes raccourcies en révision 3. La révision 3 est vérifiée binairement mais n'a pas été relancée. Ne pas présenter les 28 chaînes comme toutes testées à l'écran. Pour relancer manuellement depuis la racine : `& .\translation_work\scripts\launch_menu_test.ps1`.

Les cartes Chance C001, C002, C033 et le message dynamique de revenu restent à afficher effectivement en jeu. Leur présence intacte dans l'ELF ne constitue pas une validation de leur affichage ou de leur effet. Aucun forçage de tirage ni cheat mémoire n'est installé.

## Prochaines actions, par priorité

1. Afficher les cartes Chance de test dans cette session conservant l'ELF modifié ; vérifier glyphes, marges, sauts de ligne et substitutions de joueur/montant.
2. Étendre l'inventaire des menus aux messages de chargement et confirmations, puis améliorer les libellés joueurs et la typographie avec des pointeurs relocalisés si nécessaire, en contrôlant les références partagées.
3. Après validation du contenu et de tous les retours d'exécutables, préparer une ISO de test distincte avec l'ELF traduit au chemin original. Cette reconstruction n'est pas effectuée ici.
