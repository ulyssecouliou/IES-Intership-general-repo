# Prompt de reprise à copier dans Claude

Copier le bloc ci-dessous dans une nouvelle conversation Claude après avoir attaché le dépôt, ou au minimum `CLAUDE.md`, `docs/CLAUDE_REFERENCE.md` et `docs/project/CODEX_TO_CLAUDE_HANDOFF.md`.

```text
Tu reprends le développement d'un produit Python/VEScripts pour IESVE 2025 portant sur la SIA 380/2:2022 et la validation SIA 4010:2023.

Le dépôt source est :
C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo

Avant toute proposition ou modification, lis intégralement et dans cet ordre :
1. CLAUDE.md
2. docs/CLAUDE_REFERENCE.md
3. docs/project/CODEX_TO_CLAUDE_HANDOFF.md

Ensuite :
- inspecte `git status --short` ;
- considère tous les changements présents comme appartenant à l'utilisateur ;
- ne fais aucun reset, checkout destructif, nettoyage massif ou réécriture générale ;
- vérifie le code et les preuves machine-readable plutôt que de te fier aux anciennes documentations ;
- n'invente aucune valeur normative ni aucune API IESVE ;
- ne transforme jamais une preuve manquante ou une absence de critère en PASS ;
- distingue systématiquement test Python local, qualification IESVE réelle, résultat APS enregistré et acceptation officielle.

État immédiat à reprendre : les cas Test 1/600, 640 et 600FF possèdent des modèles, simulations et évaluations APS enregistrés, mais la dernière correction qui impose une ventilation mécanique nulle est postérieure à ces APS. Les résultats existants sont donc des baselines à requalifier, pas des validations finales de cette correction.

Commence par auditer la correction dans ces fichiers :
- swiss_sia/reference_model/sia4010/mvp_bundle.py
- swiss_sia/reference_model/sia4010/test1_runtime_inputs.py
- Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs.py
- swiss_sia/reference_model/sia4010/apachesim_qualification.py
- leurs tests sous tests/

La suite ciblée suivante passait lors de la passation Codex : 31 tests réussis.

Ta première mission est de préparer la requalification réelle du cas 600FF ou 640 dans IESVE, avec ces preuves obligatoires :
1. débit minimal de ventilation mécanique égal à 0 après read-back ;
2. héritage template désactivé ;
3. infiltration prescrite conservée séparément ;
4. ApacheSim exécuté ;
5. nouvel APS extrait ;
6. évaluation et checksums enregistrés dans le ledger central.

Ne modifie pas un paramètre physique pour rapprocher artificiellement le résultat d'une référence. Si un setter VE n'est pas démontré, crée d'abord un probe read-only minimal ou demande à l'utilisateur d'exécuter le probe dans VEScripts.

Après l'audit, réponds avec :
- ce que le code garantit réellement ;
- le risque restant ;
- le prochain script exact à exécuter dans VE ;
- les lignes de sortie attendues ;
- le fichier JSON à me renvoyer si le run échoue.
```

## Variante si Claude n'a pas accès au dossier local

Joindre au minimum :

1. `CLAUDE.md`
2. `docs/CLAUDE_REFERENCE.md`
3. `docs/project/CODEX_TO_CLAUDE_HANDOFF.md`
4. les quatre fichiers Python centraux cités dans le prompt ;
5. les trois tests ciblés ;
6. `sia4010_evidence/autonomy/sia4010_case_evidence.json` ;
7. le dernier rapport JSON du projet VE concerné.

Ne pas joindre toute la conversation Codex sauf besoin ponctuel : la passation structurée et les artefacts actuels sont plus fiables et beaucoup moins coûteux en contexte.

