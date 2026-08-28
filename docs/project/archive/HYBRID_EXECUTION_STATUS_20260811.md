# Statut d'exécution hybride SIA 4010 — 2026-08-11

## Couverture actuelle

- Cas exacts enregistrés : 30.
- Routes VEScripts directes : 6 cas Test 1 (`600`, `640`, `600FF`, `900`, `940`, `900FF`).
- Cas diagnostic Test 1 : `1E`, préparation uniquement.
- Cas nécessitant encore un template VE qualifié ou une liaison API démontrée : 23.
- Templates qualifiés actuellement enregistrés : 0.

Le rapport machine-readable de référence est :

`sia4010_artifacts/templates/sia4010_hybrid_readiness.json`

## Ce qui est livré

- Contrat de stratégie : `config/sia4010_template_requirements.json`.
- Exemple de binding : `config/sia4010_template_bindings.example.json`.
- Exemple de qualification : `config/sia4010_template_qualification.example.json`.
- Calcul d'empreinte et validation fail-closed : `template_strategy.py`.
- Readiness VEScripts : `Run_VE_SIA4010_Hybrid_Readiness.py`.
- Capture sans qualification automatique : `Run_VE_SIA4010_Capture_Active_Template.py`.
- Copie jetable checksum-vérifiée : `Run_VE_SIA4010_Create_Disposable_From_Template.py`.
- Exécution accélérée Test 1 : `Run_VE_SIA4010_Test1_Fast_Start.py`.

## Garde-fous

- Un template absent, modifié ou non revu reste bloqué.
- Une copie ne remplace jamais un dossier existant.
- L'empreinte du template est vérifiée avant et après la copie.
- Une route exécutable n'est pas un verdict de validation.
- Une comparaison APS et la revue SIA restent des gates séparés.

## Blocage factuel

Les Tests 4 à 7 exigent des topologies ApacheHVAC/plant que l'API `iesve`
installée n'a pas démontré pouvoir construire intégralement. Aucun modèle client
existant ne peut servir de substitut sans revue officielle des entrées. Le
blocage restant est donc la fourniture ou la construction initiale de ces
templates exacts, pas l'orchestration de leur réutilisation.

