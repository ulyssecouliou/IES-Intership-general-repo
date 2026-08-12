# Correspondance SIA — Prof. Zweifel, 2026-08-12

Objet : correction d'une affirmation erronée de notre part, et deux questions
qui restent ouvertes sur les classeurs d'évaluation.

Ce document existe pour une raison : le message précédent contenait une
affirmation fausse, relevée par notre interlocuteur. Avant tout nouvel envoi,
chaque phrase du brouillon est ici adossée à la cellule ou au fichier qui la
prouve. Ce qui n'est pas vérifiable n'est pas envoyé.

---

## 1. Ce que nous avions écrit, et pourquoi c'était faux

Nous avions écrit que « the corresponding workbooks do not include frequency
classes or distribution sheets » pour les Tests 4 et 6. Prof. Zweifel a répondu
« they do ». Il a raison, sur les deux moitiés de la phrase.

Deux causes, toutes deux de notre côté :

| Cause | Détail |
| --- | --- |
| Mauvais critère de recherche | Nous cherchions des feuilles préfixées `Vert.` au lieu d'examiner le type de feuille. Les feuilles `Verteilung` des Tests 4/6/7 sont des **graphiques** (chartsheets), pas des feuilles de calcul ; notre inventaire les ignorait. |
| Orthographe divergente | La feuille s'appelle `Haeufigkeitsklassen` dans les Tests 2, 3 et 5, mais `Haeufigkeitskassen` (sans le `l`) dans les Tests 4, 6 et 7. Notre recherche n'utilisait que la première orthographe et sautait donc silencieusement trois classeurs. |

Vérification, lue dans `xl/workbook.xml` de chaque classeur :

| Classeur | Feuille de classes de fréquence |
| --- | --- |
| Test1 | *aucune* |
| Test2 | `Haeufigkeitsklassen` |
| Test3 | `Haeufigkeitsklassen` |
| Test4 | `Haeufigkeitskassen` |
| Test5 | `Haeufigkeitsklassen` |
| Test6 | `Haeufigkeitskassen` |
| Test7 | `Haeufigkeitskassen` |

Après correction du lecteur, les distributions ont été relevées cellule par
cellule et réconciliées avec la ligne de totaux de chaque classeur :

| Test | Distributions figées | Référence |
| --- | --- | --- |
| 2 | 22 | `refs/reference-data/test-2.distributions.ref.json` |
| 3 | 16 | `refs/reference-data/test-3.distributions.ref.json` |
| 4 | **11** | `refs/reference-data/test-4.distributions.ref.json` |
| 5 | 16 | `refs/reference-data/test-5.distributions.ref.json` |
| 6 | **10** | `refs/reference-data/test-6.distributions.ref.json` |
| 7 | **17** | `refs/reference-data/test-7.distributions.ref.json` |

Soit 38 distributions supplémentaires par rapport à ce que nous pensions avoir.

---

## 2. Les deux questions qui restent ouvertes

### 2.1 Le Streubereich est-il un critère opposable pour les Tests 4, 6 et 7 ?

Fait relevé : dans ces trois classeurs, les feuilles `Verteilung` sont des
graphiques. Elles tracent les variantes de référence et le programme testé,
**sans calculer aucune bande** ; aucune cellule n'y définit un Streubereich.

L'asymétrie décisive est ailleurs, et elle est dans les **spécifications**, pas
dans les classeurs. Vérifié par recherche plein texte le 2026-08-12 :

| Spécification | Section `Testkriterien` | Ce qu'elle dit de la distribution |
| --- | --- | --- |
| `Spezifikation_Test2.pdf` p. 2/2 | **présente** | « Häufigkeitsverteilung … muss im Streubereich der Referenzprogramme liegen » |
| `Spezifikation_Test3.pdf` p. 3/3 | **présente** | « Häufigkeitsverteilung innerhalb des Streubereichs der Referenzprogramme » |
| `Spezifikation_Test5.pdf` p. 5/5 | **présente** | « Die Häufigkeitsverteilungen müssen im Streubereich der Referenzprogramme liegen » |
| `Spezifikation_Test4.pdf` | **absente** — 0 occurrence | — |
| `Spezifikation_Test6.pdf` | **absente** — 0 occurrence | — |

Autrement dit : pour les Tests 2, 3 et 5, la spécification **exige** elle-même
que la distribution tombe dans le Streubereich, et la clarification du
2026-08-10 en précise la définition. Pour les Tests 4 et 6, aucune phrase
équivalente n'existe. Note pour éviter un faux argument : aucun des sept
classeurs ne contient le mot `Testkriterien` — cette section n'appartient qu'aux
spécifications.

La clarification écrite du 2026-08-10 a défini la règle pour les Tests 2, 3 et
5 : enveloppe min/max des programmes de référence, classe par classe. La
question est de savoir si cette règle s'applique identiquement aux Tests 4, 6
et 7, ou si ces trois-là restent « résultats consignés, pas de critère ».

Notre position tant que la réponse n'est pas écrite : les distributions sont
extraites et consignées, mais le moteur ne les transforme pas en verdict. Statut
`RESULTS_RECORDED_NO_CRITERION`.

### 2.2 Régulation du store : quatre sémantiques non énoncées

C'est **le** blocage du cas 1E, seul cas du Test 1 à porter un critère
pass/fail. La spécification définit 1E comme « Diagnosefall 1D, jedoch mit
Stoffmarkisen-Sonnenschutz gemäss Diagnosetest 2 E1 », et le dispositif est
entièrement documenté : Soltis 92-2048-Alu, seuil 150 W/m², propriétés de la
fenêtre entière store déployé. Nous avons construit le contrat de contrôle à
partir de ces valeurs.

Ce qui manque n'est pas le dispositif mais la **dynamique**, et aucun des quatre
points ne se déduit des documents :

| Point | Ce que disent les sources |
| --- | --- |
| Signal d'irradiance exact | « Einstrahlungs-Schwellenwertregelung », sans définir la grandeur mesurée |
| Opérateur de comparaison | seuil 150 W/m² énoncé, sens de l'inégalité non énoncé |
| Règle de relâche | aucune |
| Traitement du pas de temps et de l'état | aucun |

À cela s'ajoute une question d'API : IESVE expose deux seuils distincts,
`external_shade_radiation_to_lower` et `external_shade_radiation_to_raise`. Nous
les avons tous deux positionnés à 150 W/m², mais leur équivalence dynamique à la
règle de la spécification ne se déduit pas de leurs noms.

Tant que ces points ne sont pas écrits, nous laissons 1E bloqué. Deviner la règle
de relâche déplacerait un verdict réel, sur le seul cas du Test 1 qui en porte un.

### 2.3 Test 7, bloc W : deux unités contradictoires

Fichier `Test7/Resultaterfassung Test7.xlsx`, feuille `Zusammenfassung`.
Grandeur « Aus Kälteerzeugung an die Wärmeseite gelieferte Wärme », bloc de
colonnes `W`.

- la cellule de grandeur porte `kW` ;
- la ligne d'unité (ligne 33) porte `°C`.

Un seul bloc sur dix-sept est concerné. **Vérifié cellule par cellule** le
2026-08-12 : `W32` = « Aus Kälteerzeugung an die Wärmeseite gelieferte Wärme,
kW » et `W33` = « °C », alors que tous les autres blocs concordent — `B32`/`B33`
kW/kW, `AR32`/`AR33` °C/°C, `AK32`/`AK33` sans unité et `-`. Nous avons conservé
les effectifs, qui ne dépendent pas de cette étiquette, et laissé l'unité nulle :
trancher reviendrait à corriger un défaut du classeur officiel à la place de son
auteur.

### 2.4 Ce que nous NE signalons pas, après vérification

Une version antérieure de ce dossier annonçait une contradiction entre la
spécification Test 2 et la documentation du bâtiment exemple sur le U du
vitrage : 0,654 contre 0,646. **C'était notre erreur, pas la vôtre.** La
documentation décrit la même fenêtre sous deux familles de normes et le U y
diffère — 0,646 en conditions de référence EN ISO 52022-3, 0,654 en conditions
d'hiver ISO 15099. La spécification reprend la seconde, au chiffre près. Les deux
documents concordent ; notre comparaison portait sur le mauvais bloc. Rien à
signaler, donc, et c'est consigné ici pour que ce faux constat ne ressorte pas.

---

## 3. Ce qui est déjà réglé et n'a pas besoin d'être redemandé

| Point | Réponse reçue |
| --- | --- |
| Streubereich Tests 2/3/5 | Enveloppe min/max par classe de fréquence (2026-08-10). |
| Totaux inférieurs à 8760 | Ce ne sont pas des heures manquantes : les valeurs restantes sont hors des bornes définies par les classes (2026-08-10). Nous les conservons comme compteur hors classes, sans les ajouter à la dernière classe. |
| Test 7, classeur corrigé | Borne basse / borne haute, et non moyenne / borne haute. Contrôle XML et checksum consignés. |

---

## 4. Brouillon de message (anglais, à relire avant envoi)

> Dear Professor Zweifel,
>
> Thank you for the correction — you are right, and I was wrong. The Test 4 and
> Test 6 workbooks do contain frequency classes. Two mistakes on my side caused
> it: I was looking for worksheets and the `Verteilung` sheets in those files
> are chartsheets, and the frequency-class sheet is spelled
> `Haeufigkeitsklassen` in Tests 2, 3 and 5 but `Haeufigkeitskassen` in Tests 4,
> 6 and 7, so my reader silently skipped three workbooks.
>
> After fixing it we have read the classes cell by cell and reconciled them
> against each workbook's own totals row: 11 distributions in Test 4, 10 in Test
> 6 and 17 in Test 7, in addition to the 22, 16 and 16 of Tests 2, 3 and 5.
>
> Three points remain open, and I would rather ask than assume.
>
> First, the acceptance criterion for Tests 4 and 6. Your clarification of
> 10 August defined the Streubereich for Tests 2, 3 and 5 as the min/max
> envelope of the reference programs, class by class. For those three the
> specification itself requires the distribution to lie in that range —
> `Spezifikation_Test2.pdf` states "Häufigkeitsverteilung … muss im Streubereich
> der Referenzprogramme liegen", and Tests 3 and 5 carry the equivalent
> sentence. The specifications of Tests 4 and 6 contain no `Testkriterien`
> section at all. In their workbooks the `Verteilung` sheets are charts that
> plot the reference variants against the tested program without computing any
> band, so no cell defines a range either.
>
> Does the same min/max rule apply to Tests 4 and 6, or are their distributions
> recorded without an acceptance criterion pending the sub-commission? Until we
> have this in writing our engine records the distributions but issues no
> verdict from them.
>
> Second, the fabric-awning control of diagnostic test 2 E1. This is what
> currently blocks Test 1 case 1E, the only case of Test 1 carrying a pass/fail
> criterion, since the specification defines it as case 1D with the 2 E1
> shading. The device itself is fully documented and we have built its control
> contract from your figures: Soltis 92-2048-Alu, 150 W/m2 threshold, and the
> deployed-state whole-window properties from the example-building
> documentation. What we cannot derive is the control dynamics — the exact
> irradiance signal the threshold is compared against, the direction of the
> comparison, the release rule, and how the state is carried across a timestep.
> IESVE exposes two separate thresholds, "radiation to lower" and "radiation to
> raise"; we have set both to 150 W/m2, but we cannot show from their names that
> this reproduces the rule you intend. Could you confirm those four points, or
> tell us where they are specified?
>
> Third, a small defect I would like to report rather than silently resolve. In
> `Resultaterfassung Test7.xlsx`, sheet `Zusammenfassung`, the quantity "Aus
> Kälteerzeugung an die Wärmeseite gelieferte Wärme" (column block W) carries
> `kW` in the quantity cell and `°C` on the unit row, cells W32 and W33. It is
> the only one of the seventeen blocks where the two disagree; the others match,
> for example B32/B33 both kW and AR32/AR33 both °C. We have kept the hourly
> counts, which do not depend on the label, and left the unit unset.
>
> Finally, on the SIA 2024 usage data you mentioned would follow: the category
> 3.1 extract you sent on 10 August turned out to cover more than we expected —
> it is exactly the category the Test 2 specification prescribes, and it gives
> the occupant sensible gain directly, so it has unblocked the whole 1A to 1D
> diagnostic chain. Thank you for that. What we still lack are the other
> categories our test matrix needs: the auditorium and example-building
> profiles, and restaurant 6.2 and kitchen 6.4.
>
> To be explicit about what we are and are not claiming: this work is a
> readiness and evidence exercise on our side. We make no claim that our
> software is SIA 4010 validated, and none that SIA has reviewed or endorsed it.
>
> With thanks for your patience,

---

## 5. Ce que ce message ne prétend pas

- aucune revendication de validation SIA 4010 ;
- aucune revendication d'un examen ou d'un aval de la SIA ou d'IES ;
- aucune valeur normative déduite : les trois points signalés sont des faits
  relevés dans les fichiers officiels, ou des questions.
