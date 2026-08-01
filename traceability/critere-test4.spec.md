# Arbitrage normatif — critère d'acceptation du Test SIA 4010 n° 4

> Statut : **ARBITRAGE RENDU — confiance élevée sur la forme du critère,
> confiance moyenne sur le bloc de données auquel il s'applique.**
> Auteur : `norm-analyst`, 2026-07-31.
> Portée : Test 4 uniquement (climatisation d'une seule pièce, système tout-air,
> amphithéâtre du bâtiment exemple). Classes de validation concernées : **3, 4A, 4B**.
> Dépendance : réutilise sans le refaire l'arbitrage
> `traceability/streubereich-distributions.spec.md` (construction de la bande,
> confiance ~92 %). Le présent document ne traite que la question *d'où le Test 4
> tire son critère*, pas *comment la bande se calcule*.

---

## 1. La question

`Spezifikation_Test4.pdf` ne contient aucun critère d'acceptation ; sur quelle
autorité, et sous quelle formule, le Test 4 peut-il alors être jugé conforme ?

---

## 2. Verdict

**Le critère du Test 4 n'existe pas dans sa spécification, et SIA 4010:2023 n'en
définit aucun de générique. Son unique support matériel est le classeur
`Resultaterfassung Test4.xlsx`, auquel SIA 4010 §4.4 délègue explicitement la
comparaison aux résultats de référence. La formule à appliquer est celle de la
famille (Tests 2, 3, 5), transportée au Test 4 par analogie et confirmée par la
présence effective de bandes dans son propre classeur :**

```
Somme annuelle des 3 Testgrössen : moyenne des programmes de référence
                                    ± max |programme − moyenne|
Distributions horaires de fréquence : dans le Streubereich des programmes de référence
                                      (même construction, cf. streubereich-distributions.spec.md)
```

| Élément du verdict | Niveau | Confiance |
|---|---|---|
| La spécification du Test 4 est muette (ce n'est pas un artefact d'extraction) | **VÉRIFIÉ** | ~97 % |
| SIA 4010:2023 ne contient aucun critère numérique, générique ou non | **VÉRIFIÉ** | ~95 % |
| L'autorité est déléguée par SIA 4010 §4.4 au classeur d'évaluation | **VÉRIFIÉ** | ~95 % |
| La forme de la bande est `moyenne ± max\|écart\|` sur 4 programmes de référence | **ANALOGIE + preuve matérielle** | ~88 % |
| Elle porte sur les **3 Testgrössen annuelles** (et non sur les 4 Diagnosegrössen) | **INFÉRÉ (fort)** | ~85 % |
| Les colonnes de bande `T/U/V` sont celles du bloc **Jahreswerte** et non **Maximalwerte** | **NON VÉRIFIÉ** | ~70 % |
| Le critère de distribution de fréquence s'applique aussi au Test 4 | **ANALOGIE** | ~80 % |

**Ce qui n'est PAS acquis et bloque un figeage complet : la formule de la cellule
`T10` du classeur Test 4** (§7.1). Une seule cellule tranche.

---

## 3. Preuves, citation par citation

Convention : **[V]** vérifié par moi dans une source lue cette session ;
**[V-orch]** fait matériel extrait par l'orchestrateur d'un binaire que je ne peux
pas ouvrir, et que je prends pour établi ; **[I]** inférence ; **[A]** analogie.

Toutes les lignes citées `spec_testN.txt`, `sia_*.txt`, `anwender_*.txt`,
`PREUVE_*.txt` renvoient au répertoire d'extraction de session
`…\scratchpad\norme\`. Sources primaires correspondantes :
`SIA_4010_geteilter_Link/Test<N>/Spezifikation_Test<N>.pdf`,
`Resultaterfassung Test4.xlsx`, `refs/` (SIA 4010:2023 fr, SIA 380/2:2022 fr).

### 3.1 La spécification du Test 4 est muette — et pas seulement sur le critère **[V]**

`spec_test4_raw.txt` (208 l., extraction brute) et `spec_test4.txt` (131 l.,
`-layout`) : recherche de `Resultat`, `Testgr`, `Diagnose`, `liefern`,
`Auswertung` → **0 occurrence dans les deux extractions**. Ce n'est donc pas la
seule rubrique *Testkriterien* qui manque : **tout le bloc final
« Zu liefernde Resultate / Testresultate / Testkriterien / Diagnoseresultate » est
absent**, alors qu'il est présent dans les quatre autres spécifications lues
(`spec_test1.txt` l. 64-69 ; `spec_test2.txt` l. 70, 101-110 ;
`spec_test3.txt` l. 148-155 ; `spec_test5.txt` l. 238-241, 272-280).

Le document se déclare complet : pieds de page `2 / 3` (`spec_test4.txt` l. 87) et
`3 / 3` (l. 131), la page 3 s'achevant sur les paramètres du Lufterhitzer
(`Heizwasser-Vorlauftemperatur konstant 40°C`, l. 129). À titre de comparaison,
Test 3 place ses critères en page 3/3 et Test 5 en page 5/5 : chez ces deux-là le
bloc tient sur la dernière page. **Chez le Test 4, il n'y a pas de page pour lui.**

→ **[I]** Il s'agit très probablement d'une **omission éditoriale du SIA** (les
dernières lignes du gabarit de tableau n'ont pas été imprimées), non d'une décision
de ne pas juger le Test 4 : un test dont aucun résultat ne serait demandé serait
sans objet, or `Resultaterfassung Test4.xlsx` existe, définit les grandeurs à
livrer, et **quatre** programmes de référence l'ont rempli (§3.6).

**Réserve honnête** : je ne peux pas exclure que la page 3 comporte, visuellement,
des libellés de lignes sans contenu textuel extractible (cadre de texte vectorisé,
image). Il faudrait un rendu visuel de la page 3 pour l'écarter tout à fait.

### 3.2 SIA 4010:2023 ne définit aucun critère, ni spécifique ni générique **[V]**

L'exemplaire de `/refs` est la **version française** (`sia_4010_2023.txt` l. 8-15,
« SNG 594010:2023 fr »). Recherches sur l'intégralité du texte (3109 l.) :

| Motif | Occurrences |
|---|---|
| `tol.rance`, `crit.re`, `dispersion`, `.cart` | **0** |
| `moyenne` | 14, **toutes** dans des tableaux de données d'entrée EN (l. 1767, 2290-2419 : « Température moyenne de l'eau … ») — **aucune** en rapport avec un critère |
| `Streu` (motif purement ASCII, insensible à la césure) | **0** |

Les quatre articles nommés dans la question ont été lus intégralement :

- **§4.4 « Descriptions et résultats des tests »** (l. 2695-2702) — **c'est
  l'article porteur** : « Les descriptions détaillées de chaque test sont
  disponibles sous forme de documents séparés sur www.sia.ch/sia4010. Pour chaque
  test, un fichier d'évaluation EXCEL est disponible sur www.sia.ch/sia4010, dans
  lequel les résultats peuvent être transférés et **qui génère la représentation
  comparative des résultats avec les résultats de référence**. » → délégation
  explicite, à la fois aux spécifications et au **classeur**.
- **§4.5 / tableau 63 « Classes de validation »** (l. 2704-2781) — n'attribue que
  des **tests à des classes**, aucune tolérance. Le Test 4 apparaît dans trois
  entrées de la colonne « Tests » : `1, 4 à 6`, `1, 2A, 3A à F, 4 à 7`, `1 à 7`.
  Par correspondance de position avec la colonne « N° de classe »
  (`1A, 1B, 2A, 2B, 3, 4A, 4B, 5`, l. 2743-2779) : **classes 3, 4A et 4B**.
  `[I]` — l'alignement lignes/colonnes du tableau est dégradé par l'extraction ;
  la reconstruction est positionnelle et **demande une confirmation visuelle**.
- **§4.6.1 « Infrastructure »** (l. 2783-2799) — annonce les instruments
  (classeurs EXCEL, **document FAQ**, liste de prix, liste d'outils validés) puis :
  « La sous-commission, composée d'un président et de 2 à 4 experts neutres … **évalue
  les résultats** et délivre, si nécessaire en échangeant avec le demandeur dans le
  cadre d'une procédure itérative, l'attestation de conformité. »
- **§4.6.2 « Procédure »** (l. 2802-2818) — aller-retour itératif, aucun seuil.
- **Annexe A / tableau 64** (l. 2821-2892) — donne pour le Test 4 la **liste des
  grandeurs de résultat** (§5), mais **aucun critère**.

Amont : **SIA 380/2:2022 §2.2.2.5** (`sia_380_2_2022.txt` l. 1048-1049) « on peut
appliquer toutes les méthodes de calcul pour autant qu'elles répondent aux exigences
de SN EN ISO 52016-1:2017, chiffre 7.2, ainsi qu'à la validation selon SIA 4010 » et
**§6.2.2.4** (l. 1556-1561) « Elles peuvent justifier d'une validation selon
SIA 4010 pour les systèmes considérés ». La norme **exige** la validation et ne la
chiffre nulle part.

→ **La chaîne d'autorité est fermée et documentée** :
`SIA 380/2 §2.2.2.5 / §6.2.2.4 → SIA 4010 §4.4 → {spécification de test, classeur
d'évaluation} → SIA 4010 §4.6.1 (jugement de la sous-commission)`.
Pour le Test 4, le premier maillon terminal est vide ; **le second porte seul**.

### 3.3 La formulation du critère est identique dans trois spécifications sur quatre **[V]**

| Test | Sommes annuelles | Distributions de fréquence |
|---|---|---|
| 1 | cas 600/640/900/940/600FF/900FF : « Es gibt dafür **kein Abweichungskriterium** » (`spec_test1.txt` l. 98-100) | cas 1E : « Resultate für den Test 1E müssen im **Streubereich** der enthaltenen Referenzprogramme liegen » (l. 102-104) |
| 2 | « Jahressumme … : **Mittelwert der Referenzprogramme +/- maximale Abweichung** » (`spec_test2.txt` l. 107-108) | « muss im **Streubereich** der Referenzprogramme liegen » (l. 109-110) |
| 3 | « Jahressumme: **Mittelwert +/- max. Abweichung der Referenzprogramme** » (`spec_test3.txt` l. 153) | « **Häufigkeitsverteilung innerhalb des Streubereichs** der Referenzprogramme » (l. 155) |
| **4** | **absent** | **absent** |
| 5 | « **Zulässiger Bereich für Jahressummen: Mittelwerte der Referenzprogramme +/- maximale Abweichung.** » (`spec_test5.txt` l. 274-276) | « Die **Häufigkeitsverteilungen** müssen im **Streubereich** der Referenzprogramme liegen. » (l. 278-280) |

Point capital pour la lecture du silence : **le SIA sait écrire « pas de critère »
quand il le veut** (Test 1, l. 100). Le Test 4 n'écrit ni l'un ni l'autre. Son
silence est donc un **défaut de document**, pas une exemption. `[I]`

### 3.4 Le classeur du Test 4 tabule bel et bien une bande, et sur 3 lignes précises **[V-orch]**

`PREUVE_classeur_test4.txt`, feuille `Zusammenfassung` (307 × 90) :

| Cellule | Contenu | Ligne de preuve |
|---|---|---|
| `T8` / `U8` / `V8` | `Mittelwert` / `obere Grenze` / `untere Grenze` | l. 11 |
| `A8` / `J8` | `Jahreswerte` / `Maximalwerte` (titres de bloc) | l. 11 |
| `A9` / `J9` | `Testgrössen` / `Diagnosegrössen` (sous-titres) | l. 12 |
| `A10`-`A12` | `Energiebedarf Ventilatoren`, `Wärmezufuhr Lufterwärmer`, `Wärmeabfuhr Luftkühler total` | l. 13-15 |
| `A13` | `Diagnosegrössen` | l. 16 |
| `A14`-`A17` | `Energiebedarf Zuluftventilator`, `Energiebedarf Abluftventilator`, `Wärmezufuhr WRG`, `Wärmeabfuhr Luftkühler latent` | l. 17-20 |
| `A19` | `Stündliche Häufigkeitsverteilung` | l. 21 |
| `D8`-`H8` | noms des programmes : `Daten Testprogramm`, `Daten IDA_ICE`, `Daten Excel`, `Daten EnergyPlus`, `Daten TAS` | l. 11 |

Les en-têtes de bande du Test 4 sont **exactement les trois libellés** dont la
formule a été relevée dans les classeurs des Tests 1 et 2 (`PREUVE_classeurs.txt`
l. 6-8, 14-16, 25-27, 34-36) :

```
Test 1, cas 1E    G16 = AVERAGE(C16:F16)
                  H16 = G16 + MAX(ABS(C16-G16),ABS(D16-G16),ABS(E16-G16),ABS(F16-G16))
                  I16 = MAX(0, G16 - MAX(ABS(C16-G16),…))            (PREUVE_classeurs.txt l. 9-11)
Test 2, annuel    M14 = AVERAGE(E14,H14,K14,L14)
                  N14 = M14 + MAX(ABS(E14-M14),…)
                  O14 = M14 - MAX(ABS(E14-M14),…)                    (l. 28-30)
```

→ **[A + I]** Mêmes en-têtes, même classeur-type, même auteur, même famille de
tests : la bande du Test 4 est de la même construction. C'est la seule construction
que le SIA ait jamais rendue en chiffres sous ces libellés.

### 3.5 ARGUMENT PORTEUR — dans ce corpus, « le classeur tabule une bande » ⇔ « un critère s'applique » **[V-orch]**

`AUDIT-swiss-sia-existant.md` l. 174-182, exécution réelle des sept loaders sur les
sept classeurs officiels :

| Test | Métriques | Avec bande | Cas couverts |
|---|---|---|---|
| 1 | 28 | 28 | **1E uniquement** |
| 4 | 3 | 3 | Test 4 |

Le Test 1 comporte six cas **explicitement sans critère** (§3.3) et un seul cas
avec critère : **le classeur ne tabule de bande que pour ce cas-là**. Les colonnes
`Mittelwert / obere Grenze / untere Grenze` sont donc, dans ce corpus, un **marqueur
fiable de l'existence d'un critère pass/fail**. Le classeur du Test 4 en tabule
trois → **le Test 4 a un critère, portant sur trois grandeurs.** C'est l'argument le
plus solide dont je dispose, et il ne repose sur aucune analogie textuelle.

Convergence indépendante sur le **nombre 3** : le loader s'arrête à la première
ligne libellée sans bande (`workbook_loaders.py` l. 660-661, « a labelled non-band
row ends the obligatory block »), soit `A13 = Diagnosegrössen`. Il rend donc
exactement les lignes 10-12. Deux faits distincts pointent au même endroit : le
**libellé** `Testgrössen` (l. 12 de la preuve) et l'**absence numérique** de bande
en lignes 14-17.

### 3.6 Les 4 programmes de référence du Test 4 sont identifiés et cohérents **[V]**

Colonnes `E`, `F`, `G`, `H` du classeur (`PREUVE_classeur_test4.txt` l. 11) ↔ les
quatre Anwenderberichte du Test 4 :

| Col. | Programme | Rapport | Version |
|---|---|---|---|
| E | IDA-ICE | `anwender_test4_4.txt` l. 7 | 5.0 Beta 22 |
| F | Excel (feuilles EN ISO 52016-1 + EN 16798-7 + EN 16798-5-1) | `anwender_test4_1.txt` l. 7-21 | itératif, 3-5 boucles (l. 39-42) |
| G | EnergyPlus / OpenStudio | `anwender_test4_2.txt` l. 7 | 9.1.0 |
| H | TAS (EDSL) | `anwender_test4_3.txt` l. 7 | — |

La colonne `D` (`Daten Testprogramm`) est le programme **candidat** : elle doit être
exclue de la moyenne, conformément aux formules des Tests 1 et 2 qui ne moyennent
que les colonnes de référence (`PREUVE_classeurs.txt` l. 9, 28).

### 3.7 Les Anwenderberichte du Test 4 ne donnent AUCUN critère — mais deux indices utiles **[V]**

Résultat négatif à acter : les quatre rapports ont été lus intégralement ; **aucun**
n'énonce comment les résultats ont été jugés. Ils ne documentent que des choix de
modélisation et des constats qualitatifs. Deux indices exploitables :

1. **Le jugement du Test 4 a bien porté sur des distributions de fréquence.**
   `anwender_test4_1.txt` l. 77-80 : « Die erwarteten Abweichungen bei den
   Volumenströmen treten v.a. in den Anfangsstunden auf und führen zu fehlenden
   Volumenströmen im sehr tiefen Bereich und zu einer **höheren Anzahl in der nächst
   höheren Kategorie**. Ansonsten ist die Übereinstimmung sehr gut. » Le rédacteur
   raisonne en **effectifs par catégorie** : c'est le critère de distribution.
   `[I — indice fort, mais ce n'est pas une citation du critère]`
2. **Deux programmes de référence divergent fortement sur la puissance latente du
   refroidisseur** — dans des sens opposés : « Die latente Luftkühlerleistung ist
   beträchtlich **höher** als bei anderen Programmen » (`anwender_test4_1.txt`
   l. 86-87) ; « Latente Luftkühlerleistung deutlich **tiefer** als bei anderen
   Programmen » (`anwender_test4_3.txt` l. 15). Or `Wärmeabfuhr Luftkühler latent`
   est précisément classé **Diagnosegrösse** (`A17`, sous `A13`). Cohérent : le SIA
   n'impose pas de bande là où ses propres programmes se contredisent. `[I]`
3. **Contributeur manquant à prévoir.** `anwender_test4_3.txt` l. 14 : « Bei
   Anlagensimulationen wertet TAS **nur die Raumlufttemperatur** aus. » → TAS ne
   livre pas la **température opérative** : il doit être **exclu** de l'ensemble
   contributeur pour cette distribution, jamais compté comme zéro
   (règle §5.3 de `streubereich-distributions.spec.md`). `[V pour la déclaration,
   I pour la conséquence]`

**Défaut de source à signaler** : `anwender_test4_3.txt` l. 10-12 (rapport TAS,
Test 4) parle de « Test 3 », de cas de protection solaire et de
« Sonnenschutzregelung 2 und 4 » — contenu manifestement **copié du rapport Test 2/3**.
Ce rapport est partiellement inexploitable ; ne rien en inférer sur le Test 4
au-delà de la l. 14-15.

### 3.8 Test 5 : l'analogie est légitime mais reste une ANALOGIE **[A]**

Le Test 5 partage avec le Test 4 : le même bâtiment exemple (SIA 4010 §4.3,
`sia_4010_2023.txt` l. 2680-2687 « Pour les tests 4 à 7, un bâtiment exemple a été
défini »), le même climat et la même période (`spec_test4.txt` l. 5-7 /
`spec_test5.txt` l. 5-7 : SIA 2028 DRY normal Zürich Kloten, 1.1.2022–31.12.2022),
les mêmes normes de référence (SN EN 16798-7:2017 et SN EN 16798-5-1:2017, tab. 64
l. 2880-2884 pour le Test 4 et l. 2915-2921 pour le Test 5), la même famille de
grandeurs (débits, énergie de ventilateur, batteries chaude/froide, WRG) et le même
classeur-type `Resultaterfassung`.

**Ce que l'analogie autorise** : transporter la *formulation* du critère
(`spec_test5.txt` l. 274-280) au Test 4.
**Ce qu'elle n'autorise pas** : présenter cette formulation comme une citation
applicable au Test 4. Aucun texte SIA ne dit que les critères du Test 5 valent pour
le Test 4. **C'est une analogie, pas une citation.**

Élément de renfort structurel : le Test 5 emploie **la même partition
`Testgrössen` / `Diagnosegrössen`** dans son classeur — partition déjà exploitée par
le code existant (`swiss_sia/reference_model/sia4010/distribution_reference.py`
l. 607-608 : `"scored_section": "Testgrössen"`, `"diagnostic_section":
"Diagnosegrössen"`). La grille de lecture appliquée au Test 4 en §3.5 est donc celle
que le SIA emploie dans le test voisin dont le critère est écrit.

---

## 4. Contre-arguments à ma propre conclusion

**C1 — Le silence pourrait être voulu : Test 4 = test purement comparatif.**
Le Test 1 montre que le SIA affiche parfois des résultats « zum Vergleich » sans
critère (`spec_test1.txt` l. 96-100). Peut-être le Test 4 est-il dans ce régime.
*Réponse* : réfuté par §3.5 — le classeur du Test 1 **ne tabule aucune bande** pour
les cas sans critère, tandis que celui du Test 4 en tabule trois. Un régime « sans
critère » avec bande tabulée serait sans précédent dans le corpus. **Contre-argument
levé, mais par une preuve structurelle et non textuelle.**

**C2 — La bande `T/U/V` pourrait porter sur les `Maximalwerte`, pas sur les
`Jahreswerte`. RISQUE RÉEL, NON LEVÉ.**
Géométrie des colonnes (`PREUVE_classeur_test4.txt` l. 11) : bloc 1 = `A` (libellé)
+ `D:H` (5 programmes) ; bloc 2 = `J` (libellé `Maximalwerte`) + `M:Q` (5 programmes) ;
puis `T/U/V`. Dans le classeur du Test 2, les colonnes de bande suivent
**immédiatement** les colonnes de programmes de leur propre bloc
(`M/N/O` après `D:L` ; `Z/AA/AB` après `R:V` — `PREUVE_classeurs.txt` l. 24-39).
Appliquée telle quelle, cette convention rattacherait `T/U/V` au bloc
`Maximalwerte` — ce qui signifierait que le critère du Test 4 porte sur les
**puissances de pointe** et non sur les sommes annuelles, en rupture avec les
Tests 2/3/5.
*Réponse partielle* : `J9 = Diagnosegrössen` (l. 12) qualifie **l'intégralité** du
bloc `Maximalwerte` de diagnostique ; une bande pass/fail sur un bloc déclaré
diagnostique serait contradictoire. De plus le pas régulier de la feuille est de
9 colonnes (libellés en `A`, `J`, puis `S`), ce qui fait de `S:V` un **troisième bloc
autonome** plutôt qu'un appendice du bloc `J`.
*Statut* : argumenté, **pas prouvé**. Voir §7.1 — la formule de `T10` tranche.
Sous C2, la classe **4A** (« calcul de la puissance thermique requise en fonction du
système », tab. 63 l. 2767-2769) resterait couverte, mais la grandeur contrôlée
changerait d'unité (kW au lieu de kWh) : **l'enjeu n'est pas cosmétique.**

**C3 — Le plancher à zéro diverge d'un classeur à l'autre.**
Test 1 : `MAX(0, moyenne − écart)` (`PREUVE_classeurs.txt` l. 11, 19) ; Test 2 : pas
de plancher (l. 30, 33, 39). Je ne sais pas quelle variante le Test 4 applique, et je
**ne sais pas expliquer normativement** cette divergence. Impact sur le verdict :
nul pour des énergies et des effectifs (positifs), mais l'affichage de la borne
basse en dépend.

**C4 — Le verdict final n'appartient pas à l'outil.**
SIA 4010 §4.6.1 (l. 2796-2799) confie l'évaluation à une sous-commission de 2 à
4 experts neutres, §4.6.2 (l. 2813-2818) organise un aller-retour itératif avec
demandes d'améliorations. **Notre outil produit un pronostic, pas une décision.**
Pour un test dont la spécification est lacunaire, c'est un argument de plus pour un
affichage riche (bande, enveloppe min–max, ampleur du dépassement) plutôt qu'un
binaire sec — cf. §5.5 de `streubereich-distributions.spec.md`.

**C5 — Le tableau 64 liste 6 grandeurs de test, le classeur n'en borne que 3.**
Ma reconstruction (les 3 autres sont jugées par distribution de fréquence, §5.2) est
**cohérente mais non attestée** : aucun texte ne répartit les grandeurs du Test 4
entre « critère annuel » et « critère de distribution ».

---

## 5. Grandeurs exigées par le Test 4

### 5.1 Liste normative de référence — SIA 4010:2023, Annexe A, tab. 64 **[V]**

`sia_4010_2023.txt` l. 2880-2892, ligne « 4 Climatisation pour le conditionnement
d'une seule pièce (système à air seul) », colonnes « Résultats **test** » et
« Résultats **diagnostic** » :

| # | Grandeur (tab. 64, fr) | Correspondance classeur | Unité |
|---|---|---|---|
| 1 | débit d'air | `Zu-/Abluft-Volumenstrom` | **m3/h** [V] |
| 2 | énergie du ventilateur | `Energiebedarf Ventilatoren` | kWh [I] |
| 3 | température de l'air fourni | `Zulufttemperatur (im Betrieb)` | °C [I] |
| 4 | température de l'air intérieur | `Mittlere Raumlufttemperatur` | °C [I] |
| 5 | puissance du réchauffeur d'air | `Lufterwärmerleistung` / `Wärmezufuhr Lufterwärmer` | kW / kWh [I] |
| 6 | puissance du refroidisseur d'air | `Luftkühlerleistung total` / `Wärmeabfuhr Luftkühler total` | kW / kWh [I] |
| D1 | température intérieure opérative | `Operative Temperatur` | °C [I] |
| D2 | concentration en CO2 | `CO2 Konzentration` | ppm [I] |
| D3 | puissance du refroidisseur d'air latente | `Luftkühlerleistung latent` / `Wärmeabfuhr Luftkühler latent` | kW / kWh [I] |

**Le Test 4 exige donc 9 grandeurs** (6 de test + 3 de diagnostic) — et non 3.
`⚠` Statut normatif de l'annexe A (normative ou informative) **non vérifié** :
l'extraction ne porte pas la mention, et §4.2 l. 2676 ne dit que « une matrice avec
une caractérisation plus détaillée … se trouve dans l'annexe A ».

### 5.2 Ventilation opérationnelle telle que le classeur l'organise **[V-orch]**

**(a) Sommes annuelles — `Testgrössen`, AVEC bande (le critère) — 3 grandeurs**
| Ligne | Grandeur | Unité |
|---|---|---|
| `A10` | Energiebedarf Ventilatoren | kWh `[I]` |
| `A11` | Wärmezufuhr Lufterwärmer | kWh `[I]` |
| `A12` | Wärmeabfuhr Luftkühler total | kWh `[I]` |

**(b) Sommes annuelles — `Diagnosegrössen`, SANS bande — 4 grandeurs**
`A14` Energiebedarf Zuluftventilator · `A15` Energiebedarf Abluftventilator ·
`A16` Wärmezufuhr WRG · `A17` Wärmeabfuhr Luftkühler latent (kWh `[I]`).

**(c) Valeurs de pointe — bloc `Maximalwerte`, déclaré `Diagnosegrössen` (`J9`) —
7 grandeurs** : `J10` Leistungsbedarf Ventilatoren · `J11` Wärmezufuhr Lufterwärmer ·
`J12` Leistung Luftkühler · `J14` Leistungsbedarf Zuluftventilator ·
`J15` Leistungsbedarf Abluftventilator · `J16` Leistung WRG ·
`J17` Leistung Luftkühler latent (kW `[I]`). **Sous C2, ce bloc devient le porteur
du critère.**

**(d) Distributions horaires de fréquence — `Stündliche Häufigkeitsverteilung`
(`A19`), blocs de 7 colonnes en ligne 21 — ≥ 10 grandeurs**
`B21` Zu-/Abluft-Volumenstrom (**m3/h**, `B22` [V]) · `I21` Zulufttemperatur im
Betrieb · `P21` Mittlere Raumlufttemperatur · `W21` Operative Temperatur ·
`AD21` CO2 Konzentration · `AK21` Leistung Zuluftventilator ·
`AR21` Leistung Abluftventilator · `AY21` Leistung Zu- und Abluftventilator ·
`BF21` Lufterwärmerleistung · `BM21` Luftkühler… (**libellé tronqué dans la preuve ;
au moins un bloc supplémentaire probable au-delà de `BM`** — non vérifié).
20 classes de fréquence par grandeur (lignes 24-43, total en ligne 44 :
`C44 = SUM(C24:C43)`), bornes lues dans une feuille dédiée `Haeufigkeitsklassen`
(`B24 = Haeufigkeitskassen!B4`, sic — nom de feuille orthographié avec une coquille
dans le classeur).

**(e) Profils horaires de diagnostic** — `A53` « Daten für stündliche Verläufe »,
`A54` semaine d'hiver (semaine de travail 4, 24.-28.1.), grandeurs en ligne 57 :
Zu-/Abluft-Volumenstrom (m3/h), Zulufttemperatur, Mittlere Raumlufttemperatur,
Leistung Ventilatoren, Lufterwärmerleistung, Luftkühlerleistung total, Operative
Temperatur, CO2 Konzentration, Leistung Zuluftventilator, Leistung Abluftventilator,
Luftkühl… (tronqué). Une colonne en **mg/s** existe (`S58`, `AI58`, `AZ58`, `BQ58`,
`CI58`) : grandeur **non identifiée** (débit de CO2 émis ?) — à élucider.

### 5.3 Réponse à la sous-question « le loader ne trouve que 3 : bug ou réalité ? »

**Les deux, selon ce qu'on mesure.**
- Pour le **critère de bande annuelle** : 3 est **exact** — c'est le nombre de
  `Testgrössen` (§3.5), confirmé par deux faits indépendants. **Pas un défaut de
  couverture.**
- Pour la **couverture du Test 4** : 3 sur 9 grandeurs exigées (tab. 64). Le
  critère de **distribution de fréquence n'est pas implémenté du tout** pour le
  Test 4 : la clé `"4"` est **absente** de `DISTRIBUTION_CRITERIA`
  (`distribution_reference.py` l. 520-610, qui ne couvre que `"2"`, `"3"`, `"5"`).
  **C'est là le trou réel**, pas dans le nombre de bandes.
- **Le mystère du Test 5 (16 métriques pour 8 grandeurs annuelles) est résolu au
  passage** : le Test 5 n'exige pas les 8 grandeurs dans les 4 variantes, mais un
  **sous-ensemble différent par variante** (`spec_test5.txt` l. 250-271 : 5A
  ventilateurs + Lufterwärmer + Luftkühler total ; 5B ajoute WRG total/latent ;
  5C débits + WRG + Luftkühler latent ; 5D Lufterwärmer + Befeuchter), soit 4 par
  variante × 4 = 16. **Le loader du Test 5 n'est donc pas non plus en défaut de
  couverture** sur les bandes annuelles. `[V]`

---

## 6. Formule retenue — prête à implémenter

### 6.1 Critère A — sommes annuelles (les 3 `Testgrössen`)

```
P            = { IDA-ICE, Excel, EnergyPlus, TAS }        # colonnes E,F,G,H — JAMAIS D
               moins tout programme n'ayant pas livré la grandeur (exclu, pas compté 0)
n            = |P|
moyenne(q)   = (1/n) · Σ_{p∈P} x_p(q)                     # moyenne arithmétique simple
écart_max(q) = max_{p∈P} | x_p(q) − moyenne(q) |
borne_sup(q) = moyenne(q) + écart_max(q)
borne_inf(q) = moyenne(q) − écart_max(q)                  # plancher à 0 : voir C3
VERDICT(q)   : borne_inf(q) ≤ x_candidat(q) ≤ borne_sup(q)      # intervalle FERMÉ

q ∈ { Energiebedarf Ventilatoren,
      Wärmezufuhr Lufterwärmer,
      Wärmeabfuhr Luftkühler total }                      # lignes A10..A12
```

**Aucune tolérance additionnelle.** Aucune source n'en autorise. Un epsilon de
comparaison flottante est un **détail d'implémentation IEEE-754**, jamais une
tolérance normative, et tout verdict qui basculerait à cause de lui doit être
journalisé.

**Les bornes ne doivent PAS être recalculées si le classeur les tabule** : lire
`U10:V12` (ou les colonnes homologues résolues par en-tête) et **vérifier** que le
recalcul les reproduit. Un écart signale une erreur de lecture, pas une tolérance.

### 6.2 Critère B — distributions horaires de fréquence

Appliquer **à l'identique** `traceability/streubereich-distributions.spec.md` §5
(bande symétrique par classe de fréquence, ensemble contributeur lu dans les plages
`AVERAGE`, restitution à trois états). Grandeurs : les blocs de la ligne 21 (§5.2 d).
**Statut : ANALOGIE** — le mot `Streubereich` n'apparaît nulle part dans les sources
du Test 4 ; il est transporté depuis les Tests 2/3/5. Corroboré par
`anwender_test4_1.txt` l. 77-80 (§3.7).

### 6.3 Grandeurs sans critère — à afficher, jamais à sanctionner

Les 4 `Diagnosegrössen` annuelles (§5.2 b) et le bloc `Maximalwerte` (§5.2 c) sont à
afficher en comparaison, **sans verdict**, tant que C2 n'est pas levé. Si C2 se
retourne (bande sur `Maximalwerte`), inverser : le bloc de pointe devient porteur du
critère et les sommes annuelles passent en affichage.

### 6.4 Mention obligatoire dans l'UI et le rapport

> « Test 4 : la spécification SIA ne contient aucun critère d'acceptation. Le
> critère appliqué est celui tabulé par le classeur officiel
> `Resultaterfassung Test4.xlsx`, sous la construction utilisée par les Tests 2, 3
> et 5. Verdict à confirmer auprès de la sous-commission SIA 4010 (§4.6.1). »

Ne pas masquer cette réserve : c'est le seul test des sept dont le critère n'a pas
de support textuel propre.

---

## 7. Ce qui reste NON VÉRIFIÉ

### 7.1 BLOQUANT — la formule de `T10` (criticité maximale)

Ce qu'il faut extraire de `Resultaterfassung Test4.xlsx`, feuille `Zusammenfassung`,
avec `openpyxl(data_only=False)` :

| À extraire | Ce que ça tranche |
|---|---|
| **formule de `T10`, `U10`, `V10`** | **C2** : si `AVERAGE(E10:H10)` → bande **annuelle**, verdict §6.1 confirmé. Si `AVERAGE(N10:Q10)` → bande sur les **Maximalwerte**, §6.1 à réécrire en kW. |
| la plage exacte de l'`AVERAGE` | l'ensemble contributeur, et **si la colonne `D` (candidat) est incluse** — elle ne doit pas l'être |
| présence ou non de `MAX(0, …)` en `V10` | C3, plancher à zéro |
| `T14:V17` (vides ou non) | confirme que les `Diagnosegrössen` n'ont pas de bande |
| `R8`, `S8`, `S9`, `J13` | géométrie des blocs, argument anti-C2 |

Sans `T10`, la confiance sur *quelle grandeur* est bornée plafonne à ~70 %.
**Un seul appel `openpyxl` suffit.**

### 7.2 Autres points ouverts

| # | Point | Comment le lever |
|---|---|---|
| 1 | Unités réelles des lignes 10-17 (kWh ? MJ ? kWh/m2 ?) | cellule d'unité par ligne du classeur (`_first_unit_in_row`, `workbook_loaders.py` l. 606-613) — **non extraite** |
| 2 | Libellés au-delà de `BM21` (blocs de distribution manquants) | balayage complet de la ligne 21 jusqu'à la colonne 90 |
| 3 | Bornes des 20 classes de fréquence | feuille `Haeufigkeitskassen` (sic), colonnes `B` et `C`, lignes 4-23 |
| 4 | Grandeur en **mg/s** (`S58`) | ligne 57 du classeur, colonnes `S` et au-delà |
| 5 | Page 3 de `Spezifikation_Test4.pdf` en **rendu visuel** | écarte définitivement l'hypothèse « bloc présent mais non extractible » |
| 6 | Alignement classes ↔ tests du tab. 63 (classes 3, 4A, 4B) | lecture visuelle de la p. 48 de SIA 4010:2023 |
| 7 | Statut normatif/informatif de l'**annexe A** | première page de l'annexe A dans le PDF |
| 8 | **FAQ SIA 4010** — annoncée par §4.6.1 l. 2790-2792 comme contenant « de plus en plus les questions issues des tests réalisés et les réponses à celles-ci » | téléchargement sur www.sia.ch/sia4010 — **hors dépôt**. C'est l'endroit *conçu* pour cette question : une spécification amputée est exactement le genre de point qu'un candidat antérieur a dû soulever. |
| 9 | **Question directe à la sous-commission** | voie prévue par §4.6.2 l. 2804-2818. Seule réponse définitive pour un test dont la spécification est lacunaire. **Recommandée avant tout dossier de validation réel.** |
| 10 | Version **allemande** de SIA 4010:2023 | non consultée. Rendement attendu faible (§4.4 délègue de toute façon), mais non vérifié. |
| 11 | `SN EN 16798-5-1:2017`, `SN EN 16798-7:2017`, `SN EN ISO 52016-1:2017` | **absentes de `/refs`**. Elles définissent les *modèles* du Test 4 (tab. 64 l. 2880-2892), **pas** le critère d'acceptation. Aucune valeur ni tableau n'en a été cité ici. |

### 7.3 Ce qui me ferait changer d'avis

1. **`T10 = AVERAGE(N10:Q10)`** (ou toute plage du bloc `M:Q`) → C2 se confirme, le
   critère porte sur les puissances de pointe ; §6.1 est à réécrire. **Bascule
   immédiate.**
2. **`T14:V17` non vides** → les `Diagnosegrössen` portent aussi une bande ; le
   loader est alors en défaut de couverture et le nombre 3 est faux.
3. **Une page 4 de `Spezifikation_Test4.pdf`**, ou un bloc *Testkriterien* visible
   en page 3 → le Test 4 retrouve un critère propre ; l'analogie devient inutile et
   la confiance monte au niveau des Tests 2/3/5.
4. **Une entrée de la FAQ SIA** tranchant explicitement → autorité supérieure à
   toute inférence ci-dessus, quel que soit son sens.
5. **`Spezifikation_Test6/7.pdf` sans rubrique *Testkriterien* non plus** → le
   silence deviendrait un motif récurrent et non un accident, ce qui affaiblirait
   l'hypothèse « omission éditoriale » (§3.1) sans pour autant restaurer un critère.
