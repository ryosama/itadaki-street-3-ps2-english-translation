# Phase8 — intégration et patch ISO

Les **145 traductions préparées** dans la revue des captures sont intégrées à une nouvelle copie de `SLPM_621.12`, avec huit brouillons trop longs raccourcis et plusieurs fragments partagés ajustés ensemble. Dix chaînes supplémentaires sont traduites : Yes/No, cinq lignes du sélecteur Top Ten, deux compteurs Lessons, un format de numéro de tour et le nom générique Shop. Total phase8 : **155 allocations**.

Base conservée : phase7/revision3, incluant les précédentes traductions de menus, Rules et Chance. Seule correction sur une allocation déjà traduite : `Itadaki Maps` devient `Ita Maps`. Les chaînes non traduites de la revue ne sont pas automatiquement modifiées : ce patch n'est pas une traduction complète.

## Livrables

- `phase8/revision1/patched/SLPM_621.12` : nouvel exécutable anglais.
- `phase8/revision1/gameplay_patch_manifest.json` : octets exacts avant/après et formulations finales.
- `phase8/revision1/gameplay_translations.csv` : traductions intégrées.
- `phase8/revision1/binary_and_bps_verification.json` : vérification indépendante PASS.
- `release/english_v8/Itadaki_Street_3_English_v8.bps` : patch cumulatif de l'ISO, **24487 octets**.
- `release/english_v8/Apply_English_Patch.cmd` : application en double-clic, via PowerShell et Python existant.
- `release/english_v8/README_FR.md` : instructions et limites.

## Vérifications réellement effectuées

155 allocations non superposées, taille ELF identique, variables printf et couleurs conservées, 147 références de pointeur alignées inchangées, code identique à la phase7 et retour complet à l'ELF japonais par les manifests des phases8/7/6/5/4 : **PASS**.

Le répertoire ISO9660 de `idataki3.original.iso` a été lu pour localiser l'exécutable. Son contenu correspond exactement à l'exécutable extrait original. Le BPS reconstruit exactement l'ELF anglais et n'apporte aucune modification hors de son emplacement, secteur131/offset268288. La taille ISO demeure575420416. Les SHA-256 et CRC32 de la source, du patch et de la cible virtuelle ont été vérifiés par un applicateur distinct du générateur : **PASS**.

SHA-256 ELF anglais : `44284f55ee99f13d734346785c1fffee2ce3689e722c9ac264744038ae5fe1d2`.

SHA-256 ISO anglaise virtuelle : `79f97748c46f1f4f19cdcd050777ca97b9b95bc159d12048d683d763e6c22871`.

**Aucune ISO de sortie n'a été créée pendant cette étape.** Le double-clic crée une nouvelle ISO séparée ; il ne reconstruit pas le système de fichiers et ne modifie pas l'original. Aucun lancement ni manipulation de PCSX2, aucune suppression de ressource et aucune dépendance installée. Une consultation de la spécification BPS a permis de vérifier le format du patch.

## À vérifier en jeu

Les nouveaux textes n'ont pas été testés visuellement. Les mots courts `Stk`, `Net`, `Opt`, `St` sont provisoires. Tester les six choix du menu de tour, leurs variantes désactivées, le choix Yes/No, achat, investissement, vente de stocks, échanges et statistiques. Vérifier à la fois débordements, sélection et valeurs affichées. La capacité en octets n'est pas une garantie de largeur à l'écran.
