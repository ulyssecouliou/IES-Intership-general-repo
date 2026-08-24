# Campagne accélérée de validation SIA 4010

## Objectif

Le lanceur `Run_VE_SIA4010_Validation_Campaign.py` reconstruit une file unique
pour les huit classes. Il évite de recalculer les cas communs et indique le
prochain cas exact à traiter, le lanceur VE à utiliser et la classe débloquée.

Un cas n'est marqué complet que si les trois preuves suivantes sont encore
présentes et valides par SHA-256 :

1. modèle exact vérifié ;
2. simulation ApacheSim annuelle reliée à ce modèle ;
3. évaluation APS reliée au résultat simulé et non `FAIL`/`NOT_CHECKABLE`.

La préparation d'un fichier, une simulation réussie ou un template capturé ne
suffisent jamais séparément.

## Ordre optimal

| Phase | Cas | Effet recherché |
|---|---|---|
| P0 | Test 1 complet, y compris 1E | socle commun de toutes les classes sauf 5 |
| P1 | 2A | première fermeture rapide : classe 1A |
| P2 | 2B, 2C, 2D | fermeture de la classe 1B |
| P3 | 3A à 3F | fermeture de la classe 2A |
| P4 | 3G à 3L | fermeture de la classe 2B |
| P5 | 4, 5A à 5D, 6 | fermeture de la classe 3 |
| P6 | 7 | classe 5, puis 4A/4B si les phases précédentes sont closes |

## Séquence VE quotidienne

1. Exécuter `Run_VE_SIA4010_Validation_Campaign.py` depuis les scripts VE.
2. Lire **NEXT CASE** et **RUN**. Ne travailler que sur ce cas dans un projet
   jetable enregistré.
3. Exécuter le lanceur indiqué.
4. Relancer la campagne. La file se décale automatiquement vers le prochain
   cas dont une preuve manque ou est devenue obsolète.

### Test 1 direct

- Pour 600 : ouvrir le projet existant et exécuter
  `Run_VE_SIA4010_Test1_Reconcile_Floor_Insulation.py`, puis le Fast Start.
- Pour 640, 600FF, 900, 940, 900FF et 1A à 1D : utiliser
  `Run_VE_SIA4010_Test1_Fast_Start.py` dans un projet jetable distinct.
- Le lanceur `Run_VE_SIA4010_Simulate_Active_Case.py` effectue ensuite la
  simulation gardée et l'évaluation APS.

### Cas sans générateur VE exposé : 1E et Tests 2 à 7

1. Construire ou ouvrir le cas exact, puis exécuter
   `Run_VE_SIA4010_Capture_Active_Template.py`.
2. Faire revoir indépendamment la géométrie, les données thermiques, les
   contrôles, la météo, les systèmes et les sorties exigées. Le manifeste doit
   porter `status: QUALIFIED`, un relecteur, une date, la version VE, les cas
   couverts, les preuves obligatoires et la signature capturée.
3. Ajouter la liaison dans `sia4010_template_bindings.json` du projet de
   pilotage.
4. Exécuter `Run_VE_SIA4010_Create_Disposable_From_Template.py`.
5. Ouvrir le `.mdl` copié et exécuter
   `Run_VE_SIA4010_Verify_Template_Model.py`. Toute modification d'un fichier
   modèle critique invalide la signature et bloque l'enregistrement.

Pour **1E et 2A à 2D**, exécuter ensuite
`Run_VE_SIA4010_Simulate_Qualified_Template.py`. Ce lanceur :

- impose le 1er janvier au 31 décembre et les résultats horaires ;
- conserve et trace le pas de calcul et la précondition non prescrits ;
- refuse tout écart au read-back des options ApacheSim ;
- produit un APS unique et vérifié ;
- enregistre la simulation ;
- lance immédiatement la comparaison officielle. Pour le Test 2, la somme
  annuelle et la distribution horaire sont toutes les deux obligatoires.

Pour les **Tests 3 à 7**, le template exact permet déjà de fermer la preuve
modèle. La simulation ne doit toutefois pas être présentée comme validante tant
que les liaisons APS propres à ces familles ne sont pas qualifiées. Le tableau
de campagne les maintient donc explicitement en attente et renvoie vers les
sondes de capacité runtime.

## Règles d'accélération sans perte de preuve

- Un projet jetable par cas exact ; aucun écrasement d'un APS existant.
- Réutiliser un template uniquement pour les cas mentionnés dans son manifeste
  de qualification.
- Traiter 2A avant 2B-2D, puis 3A-3F avant 3G-3L : c'est l'ordre qui débloque
  le plus tôt une classe complète.
- Réutiliser la même famille de template revue pour les variantes proches,
  mais capturer et signer chaque état exact après les changements contrôlés.
- Archiver ensemble le JSON de campagne, les rapports modèle/simulation/APS et
  le navigateur des huit classes.

## Portée du résultat

`TECHNICALLY_COMPLETE_AWAITING_SIA_ATTESTATION` signifie que la chaîne technique
interne est complète. Cela ne remplace pas l'attestation officielle de la
sous-commission SIA compétente.
