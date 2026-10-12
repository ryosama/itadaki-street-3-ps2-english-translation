# Phase 4 — Patch anglais expérimental sur copie de l'ELF

## Résultat

Une copie modifiée de `SLPM_621.12` est disponible dans `phase4/patched/SLPM_621.12`. Elle contient trois résumés anglais et un message détaillé avec paramètres dynamiques. Il s'agit d'un test technique limité, pas d'une traduction complète ou validée en jeu.

L'ELF original, les textures et les ISO restent inchangés. Aucun fichier source n'a été remplacé et aucune ISO n'a été reconstruite.

## Modifications

| Ressource | Offset fichier | Texte de test |
|---|---|---|
| C001 | `0x369470` | `Change` / `course!` |
| C002 | `0x369488` | `Roll` / `again!` |
| C033 | `0x3698F8` | `Sell at` / `3x value` |
| Message détaillé de revenu | `0x36AD30` | `P『 gets 』G『G!』` |

Les barres dans les résumés représentent des sauts de ligne `0x0A`. Les phrases sont volontairement courtes pour ce premier test. Elles occupent respectivement 15, 12 et 17 octets avec le NUL final, dans des allocations d'origine de 21, 15 et 29 octets.

Le modèle détaillé occupe 19 octets avec le NUL final, dans une allocation d'origine de 21 octets. Il préserve les commandes P (joueur) et G (entier). Les délimiteurs `『…』` protègent les segments littéraux; le texte attendu après expansion a la forme « nom gets montantG! ». Les noms continuent à provenir des données du jeu et peuvent donc rester japonais.

Ce message est partagé par les événements qui utilisent ce même modèle. Il ne constitue pas une quatrième carte traduite et n'est pas réservé à C001, C002 ou C033.

Chaque résumé comporte deux lignes de huit caractères au plus. À avance fixe de 24 pixels, les lignes les plus longues atteignent respectivement 168, 144 et 192 pixels. Ce sont des estimations statiques, pas une validation des marges à l'écran.

## Méthode de patch

Le script vérifie le SHA-256 du fichier source et les textes attendus, encode les remplacements en CP932, conserve chaque allocation existante et remplit l'espace restant avec des zéros. Il n'utilise pas les octets d'alignement voisins et ne déplace aucune section ou chaîne.

La table des 186 pointeurs, y compris les entrées partagées et le pointeur nul de C046, reste identique. Tous les autres résumés restent japonais. Le code, les structures ELF et les données en dehors des quatre plages sont inchangés.

`scripts/build_test_patch.py` n'écrase pas une sortie existante différente. Une seconde exécution identique vérifie et réutilise les mêmes sorties.

## Vérifications

- ELF de même taille : 3 923 328 octets.
- Exactement 81 octets différents, tous dans les quatre allocations autorisées.
- Relecture des 186 emplacements : trois résumés modifiés, tous les autres textes et pointeurs inchangés.
- Signature des paramètres dynamiques du message détaillé identique avant et après patch.
- Reconstitution en mémoire du fichier original à partir des octets conservés dans le manifeste, avec comparaison exacte du fichier entier.
- Exemple de stress du message détaillé : nom ASCII hypothétique de 64 octets et entier signé `-2147483648`, soit 84 octets après expansion, NUL compris. Ces valeurs servent de scénario de test et ne représentent pas des maxima démontrés du jeu.

SHA-256 source : `d6d1ad76f990c1af99e6c3c1431092e375c308d80be99b2f5bfe8c51a5f545e5`.

SHA-256 copie patchée : `e4c1917834ca50c6b2ab4326a01bd096e1df5a91c9b6d63b44aef5e8835f685d`.

## Fichiers produits

- `phase4/patched/SLPM_621.12` : ELF de test.
- `phase4/patch_manifest.json` : textes avant/après, offsets, octets originaux, octets patchés, différences et hashes.
- `phase4/patched_card_text.json` : catalogue relu depuis l'ELF patché.
- `phase4/verification.json` : vérification indépendante et références observées vers les textes testés.
- `scripts/build_test_patch.py` : construction reproductible.
- `scripts/verify_test_patch.py` : comparaison et vérification de restauration en mémoire.

Depuis la racine du projet, avec le Python local déjà identifié :

```powershell
python -X utf8 translation_work/scripts/build_test_patch.py
python -X utf8 translation_work/scripts/verify_test_patch.py
```

## Test PCSX2 : démarrage effectué, rendu des cartes restant

**Actualisation phase 5 :** le rechargement initial après introduction est contourné par `-gameargs "0 0"`, sans patch du code de démarrage. Le menu anglais a été affiché avec cette méthode ; voir `phase5_report.md`. La copie finale de test est maintenant `phase5/revision3/patched/SLPM_621.12`. Les observations ci-dessous restent l'historique du premier lancement de phase 4.

Le 11 octobre 2026, le chemin fourni par l'utilisateur a permis de trouver PCSX2 2.8.2 : `D:\programme\PCSX2 v2\pcsx2-qt.exe`. Son aide locale confirme les options `-elf`, `-datapath`, `-logfile` et `-fastboot`. Le lancement avec l'ISO original monté et l'ELF patché est désormais établi par le journal, sans reconstruction d'ISO.

Le premier lancement a montré que le marqueur `portable.txt` de l'installation prend priorité sur `-datapath`. Ce processus a été arrêté. Les hashes du BIOS et des deux cartes mémoire d'origine sont restés identiques ; la configuration habituelle `inis/PCSX2.ini` a toutefois été réécrite par PCSX2. Aucun rétablissement approximatif de cette configuration n'a été tenté. Le journal de cette tentative est conservé dans `phase4/pcsx2_runtime.log`.

Pour le second lancement, les binaires et ressources du programme ont été copiés dans `phase4/pcsx2_runtime`, sans le marqueur portable ni les données de compte. Le BIOS sélectionné, ses fichiers MEC/NVM et les deux cartes mémoire ont été copiés dans `phase4/pcsx2_data`. Les cheats, patches et sauvegardes automatiques à l'arrêt sont désactivés. PCSX2 ajoute un sous-dossier `PCSX2` au chemin fourni par `-datapath` ; la configuration est donc dans `pcsx2_data/PCSX2/inis/PCSX2.ini`. Les chemins effectifs ont été vérifiés avec `-testconfig` avant le second démarrage.

Le journal `phase4/pcsx2_isolated_runtime.log` confirme l'ouverture de `idataki3.original.iso`, l'exécution de `host:SLPM_621.12`, CRC `36BA4938`, point d'entrée `0x00100008`, et l'utilisation des dossiers BIOS et cartes mémoire isolés. La fenêtre du processus répond et porte le titre japonais du jeu. Ces observations confirment le démarrage de l'ELF et des modules du jeu, mais pas la progression d'une partie ni le rendu des cartes traduites. Aucune capture visuelle n'a encore été validée.

Scripts supplémentaires : `prepare_pcsx2_test.py` prépare les copies (ne remplace jamais les copies BIOS/cartes mémoire existantes, mais régénère la configuration de test), `launch_pcsx2_test.ps1` ouvre la fenêtre interactive et `verify_pcsx2_test.py` vérifie les hashes et les preuves de démarrage. Le dernier produit `phase4/pcsx2_runtime_verification.json`. Pour relancer, fermer d'abord PCSX2 puis exécuter `translation_work/scripts/launch_pcsx2_test.ps1` depuis PowerShell.

Une fois le lancement établi, vérifier :

**Limite confirmée du remplacement au démarrage :** le journal montre le chargement de `cdrom0:\MOVIE.ELF;1` vers 17 secondes et le démarrage de la vidéo d'introduction vers 25 secondes. À `103,3339` secondes, il confirme l'exécution de `cdrom0:\SLPM_621.12;1`, CRC `211DEAD7`, au lieu du CRC initial `36BA4938` de la copie patchée. Le programme principal original est donc rechargé depuis le disque après l'introduction : le patch de démarrage n'est plus actif pour cette session. Le rendu anglais n'est pas validé. La prochaine action prioritaire consiste à examiner de manière ciblée le passage à `MOVIE.ELF` et son retour, puis tester un contournement de l'introduction ou un redémarrage vers la copie patchée sans altérer les originaux. Aucun contournement, patch de code ou cheat mémoire n'a été appliqué à ce stade.

1. le démarrage et le chargement des ressources;
2. les lettres ASCII, les deux lignes et les marges sur C001, C002 et C033;
3. un événement utilisant le message de revenu, avec un nom et un montant variables;
4. l'absence de commandes ou délimiteurs visibles dans le message détaillé;
5. les cartes non modifiées et le comportement de C046.

La méthode pour provoquer les cartes de test n'est pas encore établie. Aucun forçage mémoire ni cheat n'a été installé. En l'absence de test dynamique, cette phase confirme la cohérence binaire et le formatage préparé, mais pas le bon rendu dans PCSX2.
