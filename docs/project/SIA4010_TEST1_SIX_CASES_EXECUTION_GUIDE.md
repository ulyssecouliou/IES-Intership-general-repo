# SIA 4010 Test 1 — exécution contrôlée des six cas

## Résultat visé

Le MVP couvre les six cas horaires prescrits par ISO 52016-1, clause 7.2 :

| Cas | Construction | Contrôle |
|---|---|---|
| 600 | légère | continu, 20 °C / 27 °C |
| 640 | légère | intermittent, 20 °C de 07:00 à 23:00 et 10 °C la nuit ; refroidissement 27 °C |
| 900 | lourde | continu, 20 °C / 27 °C |
| 940 | lourde | intermittent, 20 °C de 07:00 à 23:00 et 10 °C la nuit ; refroidissement 27 °C |
| 600FF | légère | évolution libre |
| 900FF | lourde | évolution libre |

Chaque cas doit être exécuté dans son propre projet VE sauvegardé. Ne jamais
réutiliser un projet ayant déjà reçu la géométrie d’un autre cas.

## Préparation de la campagne

Créer six projets VE vides et sauvegardés, par exemple :

```text
SIA4010_TEST1_600
SIA4010_TEST1_640
SIA4010_TEST1_900
SIA4010_TEST1_940
SIA4010_TEST1_600FF
SIA4010_TEST1_900FF
```

Conserver une copie intacte de chaque projet avant toute mutation. Le fichier
météo contrôlé doit être présent dans chaque projet selon le manifeste du cas.

## Parcours dans VEScripts

Pour chaque projet :

1. Ouvrir le projet correspondant au cas dans VE.
2. Exécuter `Run_VE_SIA_Model_Builder_UI.py` depuis VEScripts.
3. Choisir le profil `SIA4010_OFFICIAL`, la classe `1A`, la variante `test_1`
   et le cas correspondant au nom du projet.
4. Cliquer sur **Prepare / Préparer** et contrôler le rapport de préflight.
5. Cliquer sur **Create / Créer dans VE** une seule fois.
6. Cliquer sur **Probe Test 1 runtime inputs / Sonder les entrées runtime
   Test 1**. Cette étape est strictement en lecture seule.
7. Tant que la sonde ne retourne pas
   `READY_FOR_CONTROLLED_BINDING_REVIEW`, ne pas revendiquer une reproduction
   exacte du cas ISO.
8. Après qualification contrôlée des champs mobilier et puissances, cliquer
   sur **Simulate & evaluate / Simuler et évaluer**.
9. Ouvrir le navigateur de preuves et archiver le JSON d’évaluation avec le
   fichier APS correspondant.

## Contrôles ISO automatisés

La configuration centralisée vérifie notamment :

- géométrie 8 m × 6 m × 2,7 m, deux fenêtres de 3 m × 2 m et volume 129,6 m³ ;
- variantes légère et lourde des tableaux 23 et 24 ;
- vitrage `U = 2,984 W/(m²·K)`, `g = 0,71` et fraction de ré-réflexion nulle ;
- absorptivité solaire opaque 0,6 ;
- infiltration continue 0,41 vol/h, sans ventilation mécanique ;
- gain interne sensible continu 200 W ;
- capacité air + mobilier 10 000 J/(m²·K) ;
- puissances disponibles chauffage et refroidissement de 1 000 000 W ;
- période annuelle et sorties horaires nécessaires aux tableaux 28 à 34.

## Interprétation des résultats

Les tableaux 28 à 34 sont intégrés dans le catalogue machine-readable
`config/iso52016_test1_verification_cases.json`. Pour chaque résultat disponible,
le rapport contient la valeur ISO, la valeur APS, l’écart signé, l’écart absolu
et l’écart relatif.

Les pages ISO fournies ne définissent pas de tolérance d’acceptation. Le logiciel
doit donc afficher `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` et non un
faux PASS. Un verdict normatif ne pourra être produit que si une tolérance
officielle et traçable est fournie ultérieurement.

## Déclaration des méthodes — annexes A.10 et B.10

Les trois choix de l’annexe A.10 sont actuellement déclarés **No** par prudence,
car la documentation publique IES décrit des formulations ApacheSim différentes
ou plus générales que les méthodes numérotées 6.5.5.2, 6.5.6.3.1 et 6.5.7.1.
Ce choix déclenche correctement les cas de validation de la clause 7.2. Une
confirmation écrite de l’équipe solveur IES pourra remplacer cette déclaration,
mais seulement avec une source archivée.

## Blocage runtime restant

Le poste hors VE ne peut pas introspecter les types Boost.Python natifs. Le
rapport produit par le bouton **Sonder les entrées runtime Test 1** est donc la
preuve nécessaire avant d’implémenter les setters :

- `furniture_mass_factor` ;
- drapeaux, unités et valeurs des capacités chauffage/refroidissement ;
- valeurs relues après affectation.

Cette garde évite les crashs VE déjà rencontrés lors d’affectations d’énumérations
avec un type Python incompatible.
