# Exécution accélérée SIA 4010 — runbook du 11 août 2026

## Résultat disponible immédiatement

La chaîne Test 1 dispose maintenant d'un Fast Start qui :

1. identifie le cas depuis le nom du dossier ;
2. copie le transport climatique DRYCOLD et son audit sans écraser un fichier différent ;
3. produit le bundle et le scénario source-tracés ;
4. crée ou reprend le modèle ;
5. qualifie les entrées runtime ;
6. lance ApacheSim ;
7. extrait et évalue l'APS ;
8. enregistre les preuves dans le ledger central.

Projets VE vierges préparés :

- `C:\Users\ulysse.couliou\Documents\switzerland\SIA4010_TEST1_640_DISPOSABLE\try.mdl`
- `C:\Users\ulysse.couliou\Documents\switzerland\SIA4010_TEST1_600FF_DISPOSABLE\try.mdl`
- `C:\Users\ulysse.couliou\Documents\switzerland\SIA4010_TEST1_900_DISPOSABLE\try.mdl`
- `C:\Users\ulysse.couliou\Documents\switzerland\SIA4010_TEST1_940_DISPOSABLE\try.mdl`
- `C:\Users\ulysse.couliou\Documents\switzerland\SIA4010_TEST1_900FF_DISPOSABLE\try.mdl`

## Procédure pour chaque cas Test 1

1. Fermer le projet VE précédent.
2. Ouvrir le fichier `try.mdl` du dossier du cas.
3. Dans VEScripts, exécuter :
   `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo\Run_VE_SIA4010_Test1_Fast_Start.py`
4. Ne pas relancer immédiatement si VE affiche une erreur. Copier toute la sortie du terminal et le chemin du dernier rapport JSON.
5. Lorsque le script demande de sauvegarder, sauvegarder le projet actif.
6. Exécuter ensuite `Run_VE_SIA4010_Test1_Campaign_Status.py` pour identifier le prochain cas incomplet.

Ordre conseillé : `640`, `600FF`, `900`, `940`, `900FF`. Le cas `600` possède déjà une simulation et une évaluation APS enregistrées ; le relancer seulement pour une non-régression intentionnelle.

Les résultats des six cas ISO restent `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` tant qu'aucune bande officielle d'acceptation n'est démontrée. Cela ne doit pas être transformé en PASS.

## Stratégie hybride pour Tests 2 à 7

Exécuter `Run_VE_SIA4010_Hybrid_Readiness.py` depuis le hub. Le rapport distingue :

- `DIRECT_VESCRIPT` ;
- `READY_FOR_REAL_VE_QUALIFICATION` ;
- `READY_FROM_QUALIFIED_TEMPLATE` ;
- `BLOCKED_TEMPLATE_REQUIRED`.

Pour enregistrer une base complexe :

1. Ouvrir et sauvegarder le projet VE contenant le réseau exact.
2. Exécuter `Run_VE_SIA4010_Capture_Active_Template.py`.
3. Réviser le candidat contre les sources officielles.
4. Créer un manifeste à partir de `config/sia4010_template_qualification.example.json`.
5. Créer dans le projet opérateur `sia4010_template_bindings.json` à partir de l'exemple fourni.
6. Relancer la readiness.
7. Utiliser `Run_VE_SIA4010_Create_Disposable_From_Template.py` pour créer chaque copie de cas.

Un projet client ZOER, SWISSG ou un modèle seulement similaire ne peut pas être enregistré comme template officiel sans revue complète de sa géométrie, de ses systèmes, de ses contrôles, de sa météo et de ses sorties.

## Limite incontournable ce soir

Les sources officielles fournissent l'IFC du bâtiment d'exemple, mais aucun projet VE ApacheHVAC qualifié pour les Tests 4 à 7. La bibliothèque `iesve` installée n'a pas encore démontré la création complète de ces topologies. Ces tests ne peuvent donc devenir exécutables que lorsque les réseaux VE exacts ont été construits ou fournis puis capturés et revus.

