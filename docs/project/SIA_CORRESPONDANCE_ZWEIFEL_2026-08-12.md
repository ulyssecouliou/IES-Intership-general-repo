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
**sans calculer aucune bande** ; aucune cellule n'y définit un Streubereich, et
ces classeurs ne portent pas de section `Testkriterien`.

La clarification écrite du 2026-08-10 a défini la règle pour les Tests 2, 3 et
5 : enveloppe min/max des programmes de référence, classe par classe. La
question est de savoir si cette règle s'applique identiquement aux Tests 4, 6
et 7, ou si ces trois-là restent « résultats consignés, pas de critère ».

Notre position tant que la réponse n'est pas écrite : les distributions sont
extraites et consignées, mais le moteur ne les transforme pas en verdict. Statut
`RESULTS_RECORDED_NO_CRITERION`.

### 2.2 Test 7, bloc W : deux unités contradictoires

Fichier `Test7/Resultaterfassung Test7.xlsx`, feuille `Zusammenfassung`.
Grandeur « Aus Kälteerzeugung an die Wärmeseite gelieferte Wärme », bloc de
colonnes `W`.

- la cellule de grandeur porte `kW` ;
- la ligne d'unité (ligne 33) porte `°C`.

Un seul bloc sur dix-sept est concerné. Nous avons conservé les effectifs, qui
ne dépendent pas de cette étiquette, et laissé l'unité nulle : trancher
reviendrait à corriger un défaut du classeur officiel à la place de son auteur.

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
> Two points remain open, and I would rather ask than assume.
>
> First, the acceptance criterion for Tests 4, 6 and 7. Your clarification of
> 10 August defined the Streubereich for Tests 2, 3 and 5 as the min/max
> envelope of the reference programs, class by class. In the Test 4, 6 and 7
> workbooks the `Verteilung` sheets are charts that plot the reference variants
> and the tested program without computing any band, and these workbooks carry
> no `Testkriterien` section. Does the same min/max rule apply to them, or are
> their distributions recorded without an acceptance criterion pending the
> sub-commission? Until we have this in writing our engine records the
> distributions but issues no verdict from them.
>
> Second, a small defect I would like to report rather than silently resolve. In
> `Resultaterfassung Test7.xlsx`, sheet `Zusammenfassung`, the quantity "Aus
> Kälteerzeugung an die Wärmeseite gelieferte Wärme" (column block W) carries
> `kW` in the quantity cell and `°C` on the unit row. One block out of
> seventeen. We have kept the hourly counts, which do not depend on the label,
> and left the unit unset.
>
> Finally, may I ask about the SIA 2024 usage data you mentioned would follow?
> It is the remaining external input for our Test 3 preparation.
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
