# Arbitrage normatif — « Streubereich » du critère de distribution de fréquence (Tests SIA 4010 n° 2 à 6)

> **DÉCISION ANTÉRIEURE SUPPLANTÉE — 2026-08-10.** Une clarification écrite de
> Prof. Gerhard Zweifel confirme que le `Streubereich` des distributions est
> l'enveloppe **minimum à maximum des programmes de référence, classe par
> classe** (interprétation n° 1). La déduction historique `moyenne ± écart
> maximal` conservée ci-dessous n'est plus normative ; elle subsiste seulement
> pour expliquer et reproduire d'anciens audits. Une seconde clarification du
> 2026-08-10 confirme que les séries ont bien 8 760 heures : les totaux visibles
> inférieurs correspondent aux seules classes affichées, certaines valeurs se
> trouvant hors de leurs bornes. Ces heures sont auditées séparément ; elles ne
> sont ni qualifiées de manquantes, ni ajoutées à la dernière classe.
>
> La même réponse signale que les classeurs des Tests 4 et 6 contiennent bien
> des classes et distributions. Vérification locale : les deux possèdent une
> feuille `Haeufigkeitskassen`, des tableaux `Stündliche Häufigkeitsverteilung`
> dans `Zusammenfassung` et de nombreux graphiques dédiés. L'ancienne affirmation
> contraire est retirée. Une réponse écrite ultérieure de Yiqiao confirme que
> les résultats à livrer pour les Tests 4, 6 et 7 sont ceux indiqués dans les
> classeurs Excel : leur **périmètre de sortie est donc confirmé**. Cette réponse
> ne dit toutefois pas que chaque distribution ou grandeur diagnostique est un
> critère PASS/FAIL ; la portée exacte du gate d'acceptation 4/6 reste séparément
> fail-closed.

> Statut historique : **SUPPLANTÉ PAR CLARIFICATION ÉCRITE.**
> Auteur : `norm-analyst`, 2026-07-30.
> Portée : uniquement le critère « Häufigkeitsverteilung … im Streubereich der
> Referenzprogramme liegen » des Tests 2, 3, 5 (Test 4 : voir §6.2).

---

> ## ✅ VÉRIFICATION ORCHESTRATEUR — 2026-07-30, après remise de l'arbitrage
>
> Le `norm-analyst` n'a pas d'outil pour ouvrir un PDF ou un `.xlsx`. Trois des
> points qu'il a laissés ouverts relevaient d'une extraction, pas d'une lecture de
> norme : ils sont traités ici. **La confiance du verdict monte de ~85 % à ~92 %.**
>
> **1. Le maillon porteur est fermé (§7.1).** `Spezifikation_Test1.pdf` a été
> extraite en texte intégral et lue directement. Sous la rubrique *Testkriterien*
> (l. 69) figure, l. 102 :
> « Resultate für den Test 1E müssen im **Streubereich** der enthaltenen
> Referenz[programme] … »
> La citation attestée par la session antérieure est donc **confirmée de première
> main**. Le transfert de sens Test 1 → Tests 2-5 repose bien sur le même mot, dans
> le même type de rubrique, et ce critère-là est celui que le classeur calcule en
> `moyenne ± max|écart|` (formules relevées : `H16`, `I16`, `H82`, `I82`).
> L'hypothèse de repli « si Streubereich n'y figure pas, retour à indécidable » est
> **écartée**.
>
> **2. Le mot n'apparaît dans AUCUN classeur.** Recherche de `Streubereich` dans
> `xl/sharedStrings.xml` des sept `Resultaterfassung` : **0 occurrence** partout.
> Le terme vit exclusivement dans les spécifications ; les classeurs le rendent
> sous les libellés `Mittelwert` / `obere Grenze` / `untere Grenze`. Cela **renforce**
> le raisonnement : il n'existe pas de second sens tabulé quelque part qui
> contredirait celui du Test 1.
>
> **3. Le Test 4 n'a réellement aucun critère dans sa spec (§6.2 confirmé).** Ce
> n'est pas un artefact d'extraction : la spec fait 3 pages, a été ré-extraite en
> mode brut (208 lignes) et fouillée par recherche insensible à l'encodage —
> `Testkriterien`, `Streubereich`, `Mittelwert`, `Abweichung`, `Häufigkeitsverteilung` :
> **0 occurrence de chacun**. Le document s'achève sur les paramètres de
> dimensionnement CVC. Le critère du Test 4 n'existe donc que dans son classeur, qui
> tabule bel et bien des bandes (3 métriques extraites). À traiter comme un point
> normatif distinct.
>
> **4. Le contre-argument des graphiques est levé (§7.2).** Les 50 graphiques du
> classeur Test 2 ont été inventoriés. Le plus fourni, `chart9`, est un
> **histogramme (`barChart`) à 9 séries**, traçant `Zusammenfassung!$CS$32:$CX+$51`
> — soit la zone des classes de fréquence du cas 2D. Les 9 séries sont nommées en
> ligne 30 : `Testprogramm Fe einfach`, `IDA_ICE Fe det Spec`, `IDA_ICE Fe det
> noSpec`, `IDA_ICE Fe einf`, `Excel SIA 387/4 + 380/2`, `EnergyPlus Fe det Spec`,
> `EnergyPlus Fe det nonSpec`, `EnergyPlus Fe einf`, `TAS Fe det nonSpect`.
> **Aucune série de bande, aucune enveloppe min/max, aucun graphique en aires.**
> Le classeur se contente de superposer les histogrammes des programmes.
> Le SIA ne matérialise donc la bande de distribution **nulle part** : ni tabulée,
> ni tracée. La seule définition qu'il ait jamais rendue en chiffres pour ce mot
> reste `moyenne ± max|écart|`. Le contre-argument perd son support matériel.
>
> **5. DÉCOUVERTE — l'ensemble contributeur est une sélection normative, pas « tous
> les programmes ».** La bande annuelle du Test 2 moyenne **4** valeurs alors que le
> classeur contient **8** colonnes de référence. Les colonnes retenues par la
> formule `M14 = AVERAGE(E14,H14,K14,L14)` sont, d'après les en-têtes L9/L10 :
>
> | Colonne | Programme | Variante retenue |
> |---|---|---|
> | E | IDA_ICE | **Fe det Spec** |
> | H | Excel | (variante unique) |
> | K | Energy+/OpenStudio | **Fe einf** |
> | L | EDSL-Tas | **Fe det nonSpect** |
>
> Exclues : F, G (autres variantes IDA_ICE) et I, J (autres variantes Energy+).
> **Une variante par programme — et pas la même d'un programme à l'autre.** Une
> implémentation qui moyennerait les 8 colonnes, ou qui choisirait une variante
> uniforme, produirait une bande différente et donc de faux verdicts.
> Second point confirmé : `M15 = AVERAGE(E15,H15,K15)` — pour le cas 2B, TAS
> disparaît (il n'a pas livré ce cas, cf. Anwenderbericht TAS). Un programme absent
> est exclu de la moyenne, jamais compté comme zéro.
>
> **Règle d'implémentation qui en découle** : l'ensemble contributeur ne se devine
> pas, il se **lit dans la formule de bande annuelle du classeur** (les colonnes
> référencées par `AVERAGE`), puis s'applique à l'identique aux classes de
> fréquence. C'est vérifiable et reproductible, contrairement à toute convention
> choisie a priori.

---

## 1. La question

Le « Streubereich » des programmes de référence, à construire classe de fréquence par
classe de fréquence faute d'être tabulé dans le classeur, est-il **(a)** la bande
symétrique `moyenne ± max|programme − moyenne|`, ou **(b)** l'enveloppe
`min(programmes) .. max(programmes)` ?

## 2. Verdict

**(a) BANDE SYMÉTRIQUE** — `moyenne ± max|programme − moyenne|`, appliquée par classe de
fréquence : c'est la seule construction que le SIA ait jamais rendue en chiffres pour
ce mot exact, dans son propre classeur, pour le seul critère du Test 1 qui porte le même
libellé. **Niveau de confiance : ÉLEVÉ (~85 %)** — pas absolu, car la déduction repose
sur un transfert de sens entre le Test 1 et les Tests 2–5, et sur une citation du Test 1
que je n'ai pas pu relire moi-même (§7.1).

---

## 3. Preuves, citation par citation

Convention : **[V]** = vérifié par moi dans une source lue cette session ; **[V-2e]** =
attesté par un livrable interne recontrôlé indépendamment mais dont la source primaire
ne m'est pas lisible ; **[I]** = inférence, marquée comme telle.

### 3.1 Le libellé du critère est bien homogène sur les Tests 2, 3 et 5 **[V]**

| Test | Critère « somme annuelle » | Critère « distribution » |
|---|---|---|
| 2 | « Mittelwert der Referenzprogramme +/- maximale Abweichung » (`spec_test2.txt` l. 108) | « Häufigkeitsverteilung … : muss im **Streubereich** der Referenzprogramme liegen » (l. 109-110) |
| 3 | « Jahressumme: Mittelwert +/- max. Abweichung der Referenzprogramme » (`spec_test3.txt` l. 153) | « Häufigkeitsverteilung innerhalb des **Streubereichs** der Referenzprogramme » (l. 155) |
| 5 | « **Zulässiger Bereich** für Jahressummen: Mittelwerte der Referenzprogramme +/- maximale Abweichung. » (`spec_test5.txt` l. 274-276) | « Die Häufigkeitsverteilungen müssen im **Streubereich** der Referenzprogramme liegen. » (l. 278-280) |

(Sources : `…\scratchpad\norme\spec_test2.txt`, `spec_test3.txt`, `spec_test5.txt` —
extractions intégrales des `Spezifikation_TestN.pdf`, section *Testkriterien*.)

Aucune des trois n'est plus explicite que les autres : **le Test 5, le plus détaillé, ne
définit pas davantage le terme.** Il apporte en revanche un point de vocabulaire utile
(§3.4).

### 3.2 SIA 4010:2023 est MUET sur le terme et sur le critère **[V]**

- Recherche `Streu` sur l'ensemble de `…\scratchpad\norme\` : **0 occurrence** dans
  `sia_4010_2023.txt`. Le motif est purement ASCII, aucune coupure de mot ne peut
  l'avoir masqué (une césure « Streu-bereich » contiendrait encore « Streu »).
- Attention, fait matériel important : **l'exemplaire en main est la version FRANÇAISE**
  (`sia_4010_2023.txt` l. 8-15, « SNG 594010:2023 fr »). Les recherches françaises
  correspondantes — `dispersion`, `fréquence`, `écart`, `critère`, `tolérance`,
  `programmes de référence` — **ne renvoient également aucune occurrence pertinente**
  (seuls des « Plage pratique, à titre informatif » de tableaux d'entrées EN, l. 1443,
  1527, 1614, 2014, 2041).
- La raison est structurelle, et elle est écrite : SIA 4010 §4.4 (l. 2695-2702) délègue
  *l'intégralité* des descriptions et critères aux documents séparés et au fichier
  d'évaluation EXCEL : « Les descriptions détaillées de chaque test sont disponibles sous
  forme de documents séparés sur www.sia.ch/sia4010. Pour chaque test, un fichier
  d'évaluation EXCEL est disponible … qui génère la représentation comparative des
  résultats avec les résultats de référence. »

→ **La norme-chapeau ne tranchera jamais ce point.** La seule autorité disponible est le
couple {spécification de test, classeur d'évaluation}.

### 3.3 PREUVE CENTRALE — le SIA a déjà rendu ce mot en chiffres, une fois, et c'est (a)

Chaîne en quatre maillons :

1. **Le Test 1 utilise le MÊME mot pour son unique critère pass/fail.** `[V-2e]`
   `traceability/test-1.spec.md` l. 299-302, citation donnée comme vérifiée mot pour mot
   contre `SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf`, rubrique *Testkriterien* :
   « **Resultate für den Test 1E müssen im Streubereich der enthaltenen Referenzprogramme
   liegen** ». Même document l. 295-298 : les cas 600/640/900/940/600FF/900FF n'ont
   **aucun** critère (« Es gibt dafür kein Abweichungskriterium »). Le cas 1E est donc le
   **seul** endroit du Test 1 où le mot « Streubereich » commande un verdict.

2. **Le classeur du Test 1 tabule une bande — et une seule — pour ce cas 1E, et c'est la
   bande symétrique.** `[V]` `PREUVE_classeurs.txt` l. 5-22 (formules relevées avec
   `openpyxl data_only=False` sur `Resultaterfassung_Test1.xlsx`) :

   ```
   Table 28 (besoins mensuels, cas 1E)      G16 = AVERAGE(C16:F16)
                                            H16 = G16 + MAX(ABS(C16-G16),…,ABS(F16-G16))
                                            I16 = MAX(0, G16 - MAX(ABS(C16-G16),…))
   Table 31 (charges de pointe hor., cas 1E) idem, lignes 82-83
   ```
   En-têtes : `Mittelwert` / `obere Grenze` / `untere Grenze` (G15/H15/I15, G81/H81/I81).

3. **Cette formule est vérifiée numériquement, indépendamment, sans échantillonnage.**
   `[V]` `AUDIT.md` l. 60-67 et l. 142 (`qa-auditor`, passe 3) : « le `Streubereich`
   n'est **PAS** le simple min/max des 4 programmes. La formule réelle est
   `range_max = moyenne + écart_max`, `range_min = max(0, moyenne − écart_max)`,
   `écart_max = max|programme − moyenne|` (bande symétrique, plancher à 0). Vérifiée
   **26/26**. L'hypothèse « range = min/max des programmes » est **fausse**. »
   Recoupé à la main sur la Table 31 : `AUDIT-swiss-sia-existant.md` l. 109-113
   (moyenne 1.75245555 = G82 ; écart max 0.0913288 ; 1.8437844 = H82 ; 1.6611267 = I82).

4. **Les Tests 2 à 5 emploient le même mot pour le même office** (commander un verdict
   « … liegen »), sur des programmes de référence de même nature. `[V]` §3.1 ci-dessus.

→ **Conclusion** : quand le SIA a dû transformer « im Streubereich … liegen » en une
règle calculable, il a écrit `moyenne ± max|écart|`. C'est la définition opérationnelle
du terme dans le corpus SIA 4010. `[I, mais inférence courte et directe]`

### 3.4 Deux indices de corroboration, faibles mais convergents **[I]**

- **Le plancher à zéro est en lui-même une preuve de construction.** `MAX(0, …)`
  (`PREUVE_classeurs.txt` l. 11, 19) n'a de sens que si la borne basse peut descendre
  **sous** la plus petite valeur observée, et même sous zéro. Une enveloppe min–max de
  grandeurs positives ne peut jamais être négative : le garde-fou serait mort-né. Sa
  présence atteste que le rédacteur construisait bien une bande symétrique détachée des
  données.
- **Le choix était le plus coûteux à écrire.** `MIN(C16:F16)` / `MAX(C16:F16)` était plus
  court et plus naturel si l'enveloppe était visée. Le rédacteur a écrit
  `G16+MAX(ABS(C16-G16),ABS(D16-G16),ABS(E16-G16),ABS(F16-G16))`. Un choix délibéré.
- **Test 5 : « Zulässiger Bereich » = moyenne ± écart max** (`spec_test5.txt` l. 274-276).
  Le SIA nomme donc *bande admissible* exactement la construction (a). Que la phrase
  suivante appelle *Streubereich* la bande admissible des distributions n'introduit pas
  de rupture de sens ; c'est le même auteur, le même paragraphe.

### 3.5 Les Anwenderberichte du Test 2 : AUCUNE preuve sur la construction de la bande **[V]**

Les quatre rapports ont été lus intégralement (`anwender_test2_1..4.txt`). **Aucun** ne
décrit comment la distribution a été jugée. Ils ne documentent que des choix de
modélisation et des limitations. Résultat négatif, à acter : cette piste ne tranche pas.

En revanche ils apportent un élément **utile pour l'implémentation** (programmes non
contributeurs, §5.3) :
- EXCEL (`anwender_test2_1.txt` l. 19-28) : albédo dépendant de l'état du sol, d'où
  « zu gewissen Zeiten mit Neuschnee erheblich höhere Einstrahlungswerte » et
  « entsprechend enthält die **Verteilung** der Einstrahlung eine beschränkte Anzahl
  Stunden mit höheren Werten ». → un programme de référence est un **outlier assumé et
  documenté dans la distribution**, et le SIA l'a **conservé** dans le jeu de référence.
- TAS (`anwender_test2_3.txt` l. 10-20) : pas de modèle de lamelles (« Kein
  Lamellenmodell »), donc « nur der Testfall 2 sowie der Testfall 4 mit einer
  Stoffmarkise gerechnet » ; « Sekundärer solarer Wärmeeintrag nicht auswertbar » ;
  « Solare Einstrahlung nur als Summe ».
- EnergyPlus (`anwender_test2_2.txt` l. 18-24) : gains solaires disponibles uniquement
  avec le modèle de fenêtre simple.
- IDA ICE (`anwender_test2_4.txt` l. 13-15) : aucune hypothèse particulière.

Ces déclarations expliquent exactement pourquoi les moyennes du classeur portent sur des
jeux de programmes **variables** : `M14 = AVERAGE(E14,H14,K14,L14)` (4 programmes) mais
`M15 = AVERAGE(E15,H15,K15)` (3), et `Z14 = AVERAGE(R14,U14,V14)` (3) pour l'autre
grandeur (`PREUVE_classeurs.txt` l. 28-39).

---

## 4. Contre-arguments à ma propre conclusion (exposés honnêtement)

**C1 — L'argument du double libellé.** Dans le *même* bloc *Testkriterien*, le rédacteur
écrit la formule en toutes lettres pour la somme annuelle et emploie un mot différent
pour la distribution. Pourquoi changer, sinon pour désigner autre chose ? C'est
l'argument le plus fort en faveur de (b) et il n'est **pas réfutable par le texte seul**.
*Ma réponse* `[I]` : le Test 1 démontre que « Streubereich » est, chez cet auteur, le nom
générique de la bande qu'il calcule en moyenne ± écart max — il l'emploie seul, sans
formule, là où le classeur applique (a). L'asymétrie de rédaction s'explique mieux par
l'asymétrie de *tabulation* : la somme annuelle est un nombre unique par cas, tabulé, donc
sa formule est explicitée ; la distribution est un vecteur de centaines de classes, non
tabulé, donc désigné par le mot générique. C'est une explication plausible, pas une preuve.

**C2 — L'argument du graphique.** Le classeur ne tabule aucune bande pour les
distributions (`PREUVE_classeurs.txt` l. 43-48 : balayage exhaustif lignes 26-308,
colonnes 1-239, zéro `Mittelwert` / `obere Grenze` / `untere Grenze`). Le jugement se fait
donc, en pratique, sur une **superposition de courbes**. Or, visuellement, « la courbe
candidate est dans le Streubereich des courbes de référence » se lit spontanément comme
« entre la plus basse et la plus haute » — soit (b). C'est un argument sérieux et je ne
peux pas l'écarter : je n'ai pas pu ouvrir les graphiques du classeur pour voir quelles
séries y sont tracées (§7.2).

**C3 — L'asymétrie du risque n'est pas univoque.** Comme `[min,max] ⊆ [moy−écart, moy+écart]`,
(a) est toujours plus permissif. Choisir (a) supprime le risque de **faux échec** — mais
crée symétriquement un risque de **faux succès** : annoncer « conforme » à un client dont
la sous-commission SIA refusera ensuite le dossier. Le traitement de ce risque est
intégré au §5.5 (double affichage) : il ne se règle pas en choisissant l'autre bande, il
se règle en **rendant l'écart visible**.

**C4 — Le verdict final n'appartient pas à l'outil.** SIA 4010 §4.6.1 (l. 2796-2799) :
« La sous-commission, composée d'un président et de 2 à 4 experts neutres … évalue les
résultats et délivre, si nécessaire en échangeant avec le demandeur dans le cadre d'une
procédure itérative, l'attestation de conformité. » §4.6.2 (l. 2813-2818) prévoit
explicitement un aller-retour avec demandes d'améliorations. **Notre outil produit un
pronostic, pas une décision.** Cela plaide pour un affichage informatif riche plutôt que
pour un binaire sec — et rend le choix (a) vs (b) moins irréversible qu'il n'y paraît.

---

## 5. Formule retenue — prête à implémenter

### 5.1 Définition

Soit un cas de test `c`, une grandeur contrôlée `q`, et une classe de fréquence `b`.
Soit `P(c,q)` l'ensemble des **programmes de référence contributeurs** pour ce couple
(§5.3), et `x_p(c,q,b)` la valeur de la classe `b` de la distribution du programme
`p ∈ P(c,q)`.

```
n        = |P(c,q)|
moyenne  = (1/n) · Σ_{p∈P}  x_p                       # moyenne arithmétique simple, non pondérée
écart_max= max_{p∈P} | x_p − moyenne |                # écart absolu maximal à la moyenne
borne_sup= moyenne + écart_max
borne_inf= max(0, moyenne − écart_max)                # plancher à zéro : voir 5.2
VERDICT(b) : borne_inf ≤ x_candidat(c,q,b) ≤ borne_sup     # intervalle FERMÉ
```

Bornes **inclusives** (intervalle fermé). Le texte dit « **im** Streubereich … **liegen** »
(`spec_test2.txt` l. 110, `spec_test5.txt` l. 278-280), sans mention de stricte
infériorité ; l'inclusion est la lecture standard. `[I — interprétation, non contestée par
aucune source]`

Comparaison flottante : si un garde-fou numérique est nécessaire, il doit être déclaré
**détail d'implémentation** (epsilon relatif de nature purement IEEE-754), **jamais** une
tolérance normative, et tout verdict qui bascule à cause de lui doit être journalisé.
Aucune source n'autorise une tolérance sur ce critère.

### 5.2 Plancher à zéro

**À appliquer** (`borne_inf = max(0, …)`), par cohérence avec le seul précédent tabulé
(Test 1, `PREUVE_classeurs.txt` l. 11 et 19). Le Test 2 ne l'applique pas pour ses valeurs
**annuelles** (l. 30, 33, 39 : `O14 = M14 - MAX(...)` sans `MAX(0,…)`) — divergence réelle
entre classeurs, que je **ne sais pas expliquer normativement**.

**Impact sur le verdict : nul.** Les classes de fréquence sont des effectifs (nombre
d'heures) ou des fractions, donc `x_candidat ≥ 0`. Que la borne basse vaille `0` ou une
valeur négative, l'ensemble des candidats acceptés est identique. Le plancher n'est donc
qu'une question d'affichage. **Je recommande de l'appliquer et de le signaler dans l'UI**
(« borne basse théorique négative, ramenée à 0 »), ce qui informe l'utilisateur que la
bande n'est pas contraignante par le bas pour cette classe.
`[I — raisonnement arithmétique, vérifiable]`

### 5.3 Programmes non contributeurs

**Règle : un programme absent est EXCLU de `P(c,q)` — jamais compté comme zéro.**
Fondement vérifié : `M15 = AVERAGE(E15,H15,K15)` contre `M14 = AVERAGE(E14,H14,K14,L14)`,
et `Z14 = AVERAGE(R14,U14,V14)` (`PREUVE_classeurs.txt` l. 28-39). Le jeu contributeur
varie **par cas** *et* **par grandeur**, ce que les Anwenderberichte expliquent
exactement (§3.5). `[V pour les valeurs annuelles ; I pour l'extension aux distributions]`

Extension aux distributions : **inférence**, mais l'alternative est absurde — compter
0 heure dans toutes les classes pour un programme qui n'a pas livré le cas fausserait
moyenne *et* écart max de façon massive.

**Piège à ne pas ignorer.** Dans la zone des distributions, un programme non contributeur
apparaîtra probablement en **colonne vide ou entièrement à zéro**, indiscernable d'un
programme ayant réellement livré une distribution nulle. **Ne pas déduire l'appartenance
à `P(c,q)` de la seule vacuité des cellules.** Le jeu contributeur doit être établi à
partir des plages `AVERAGE` des **valeurs annuelles** — qui encodent la décision propre du
SIA — et recoupé contre les déclarations des Anwenderberichte. Il doit être **figé
explicitement dans le JSON de référence**, cas par cas et grandeur par grandeur, pas
recalculé à la volée. `[I — règle d'ingénierie, justifiée]`

### 5.4 Sur quelles données calculer la bande

Sur les **valeurs de distribution déjà tabulées par programme dans le classeur**
(`Resultaterfassung_TestN.xlsx`, zone `Häufigkeitsklassen`), et non sur un rebinning
maison des séries horaires brutes — sauf à avoir prouvé que notre binning reproduit
exactement celui du classeur (bornes de classes, ouverture/fermeture des intervalles,
effectifs bruts vs %, cumulé ou non). Ces caractéristiques **ne sont pas établies à ce
jour** et relèvent de `reference-data-engineer` (§7.2).

### 5.5 Restitution exigée dans l'UI (protection contre C3)

L'outil calcule et affiche **les deux** constructions :
- **(a)** bande `moyenne ± écart_max` → **support du verdict** ;
- **(b)** enveloppe `min..max` des programmes → **affichée en surcouche**, sans verdict.

Trois états par classe, au lieu de deux :
| État | Condition |
|---|---|
| **CONFORME** | `x_candidat ∈ [min, max]` (dans l'enveloppe, donc conforme aux deux lectures) |
| **CONFORME — RÉSERVE** | `x_candidat ∈ [borne_inf, borne_sup] \ [min, max]` : conforme selon (a), hors enveloppe des programmes |
| **HORS BANDE** | `x_candidat ∉ [borne_inf, borne_sup]` (non conforme aux deux lectures) |

Toute classe en « CONFORME — RÉSERVE » est un point de discussion à préparer pour la
sous-commission (SIA 4010 §4.6.2, l. 2813-2818). Cette restitution neutralise le risque
des deux côtés et rend l'arbitrage réversible sans réécrire le moteur.

---

## 6. Points ouverts DISTINCTS, révélés par l'analyse (à ne pas confondre avec la question tranchée)

### 6.1 Sévérité : combien de classes hors bande font échouer le test ? — NON TRANCHÉ

Le texte dit « **die** Häufigkeitsverteilung … muss … liegen » : la distribution, comme
objet, doit être dans la bande. La lecture stricte est « **toutes** les classes ». Aucune
source, ni spécification ni classeur, n'autorise un quota de classes hors bande.
**Mais** : appliquer un « une classe hors bande ⇒ échec » à un critère que le SIA fait
juger visuellement par une sous-commission (§4.6.1) serait vraisemblablement plus sévère
que la pratique réelle. **Recommandation** : l'outil ne doit **pas** rendre un
« NON CONFORME » sec ; il doit rendre `N classes hors bande sur M`, avec la liste, la
classe concernée et l'ampleur du dépassement. Point à faire arbitrer par la
sous-commission, pas par nous. `[I — signalé, non tranché]`

### 6.2 Test 4 : libellé du critère NON VÉRIFIABLE dans l'extraction fournie

`spec_test4.txt` (3 pages, complet jusqu'à « 3 / 3 » l. 131) **ne contient aucune
rubrique *Testkriterien***. Recherches infructueuses sur `Testkriterien`, `Kriterium`,
`Testgrösse`, `Streu`, `Bereich`, `Häufigkeit`, `Verteilung`, `Abweichung`, `Auswertung`,
`Resultaterfassung`, `Mittelwert` : **0 occurrence**. Le bloc a été perdu à l'extraction
(cadre de texte non capturé). **Je ne peux donc pas confirmer que le Test 4 porte le même
critère.** À re-extraire avant d'appliquer la présente décision au Test 4.

---

## 7. Ce qui reste NON VÉRIFIÉ

### 7.1 La citation porteuse (criticité maximale)

Le verdict repose sur le fait que la spécification du **Test 1** emploie littéralement
« im **Streubereich** der enthaltenen Referenzprogramme liegen ». Je n'ai **pas pu lire
moi-même** `SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf` (outil `Read` : rendu
PDF indisponible, « pdftoppm is not installed »). Je m'appuie sur `traceability/test-1.spec.md`
l. 299-302, qui donne la citation comme vérifiée mot pour mot par une session
`norm-analyst` antérieure, et sur `AUDIT.md` / `AUDIT-swiss-sia-existant.md` qui
emploient le même terme pour le même cas.
→ **Action bloquante avant figeage** : extraire
`SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf` en texte (`pdftotext`) et me
faire relire la rubrique *Testkriterien* verbatim. **Si le mot « Streubereich » n'y figure
pas, le maillon 1 du §3.3 saute et le verdict retombe à « indécidable, léger avantage à (b) ».**

Nuance à ne pas masquer : les colonnes du classeur Test 1 sont étiquetées
`Mittelwert` / `obere Grenze` / `untere Grenze` — **jamais** `Streubereich`
(`PREUVE_classeurs.txt` l. 6-8, 14-16, 25-27). Le lien entre le mot de la spécification
et la formule du classeur est **fonctionnel** (c'est la seule bande, pour le seul cas
porteur d'un critère), **pas lexical**.

### 7.2 Sources manquantes qui trancheraient, par ordre de rendement

| # | Source | Ce qu'elle trancherait | Comment l'obtenir |
|---|---|---|---|
| 1 | `Spezifikation_Test1.pdf`, rubrique *Testkriterien*, verbatim | Le maillon porteur (§7.1) | **Déjà dans le dépôt** — extraction `pdftotext` |
| 2 | Définitions de **graphiques** de la zone `Häufigkeitsklassen` de `Resultaterfassung_Test2/3/5.xlsx` (`xl/charts/chartN.xml` dans le zip) | Décisif contre C2 : si une série `Mittelwert`/`obere Grenze`/`untere Grenze` y est tracée (même issue de colonnes masquées ou de noms définis) ⇒ (a) confirmé ; si seules les courbes par programme sont tracées ⇒ C2 se renforce | **Déjà dans le dépôt** — dézipper le `.xlsx` |
| 3 | Balayage de la chaîne `Streubereich` dans **toutes** les feuilles (y compris masquées) et **tous** les classeurs Tests 1 à 7 | Si le mot apparaît comme en-tête à côté d'une colonne calculée, la définition est nailée lexicalement | **Déjà dans le dépôt** — `openpyxl`, toutes feuilles |
| 4 | `Spezifikation_Test6.pdf` et `Spezifikation_Test7.pdf` + leurs classeurs | Occurrences supplémentaires du couple {mot « Streubereich », formule tabulée}. Chaque occurrence supplémentaire confirme ou casse la règle | **Déjà dans le dépôt** |
| 5 | `Spezifikation_Test4.pdf` re-extrait | §6.2 | **Déjà dans le dépôt** |
| 6 | **FAQ SIA 4010** — SIA 4010 §4.6.1 (l. 2790-2792) annonce « un document FAQ sur les tests, dynamique, c'est-à-dire qu'il contient de plus en plus les questions issues des tests réalisés et les réponses à celles-ci » | C'est l'endroit *conçu* pour ce genre de question ; il est plausible qu'elle y ait déjà été posée | Téléchargement sur www.sia.ch/sia4010 — **hors du dépôt** |
| 7 | **Question directe à la sous-commission** | Définitif | SIA 4010 §4.6.2 (l. 2804-2818) institue l'échange itératif avec le demandeur : c'est la voie prévue par la norme, et la moins chère en absolu |

### 7.3 Autres éléments non vérifiés

- **Structure exacte des distributions** : bornes des classes, effectifs bruts vs
  pourcentages, cumulé ou non, nombre de classes. Inconnus. Le balayage
  `PREUVE_classeurs.txt` l. 45 mentionne « lignes 26 à 308 » sans en donner le contenu.
  → `reference-data-engineer`.
- **`M15` exclut la colonne `L` alors que `M14` l'inclut** (`PREUVE_classeurs.txt`
  l. 28-33). Excel ignorant de toute façon les cellules vides dans `AVERAGE`, ce
  rétrécissement de plage est soit cosmétique, soit une **exclusion délibérée d'une
  valeur présente**. Les deux cas n'ont pas le même sens. → à élucider en lisant `L15`.
- **Version allemande de SIA 4010:2023** : non consultée (seule la version fr est dans
  `/refs`). Rendement attendu faible, puisque §4.4 délègue de toute façon aux documents
  séparés — mais non vérifié.
- **EN 16798-5-1:2017, EN ISO 52016-1:2017** : absentes de `/refs`. Sans objet ici (aucune
  ne définit le critère d'acceptation SIA), mentionnées pour mémoire.

---

## 8. Ce qui me ferait changer d'avis

1. **Spezifikation_Test1.pdf n'emploie pas « Streubereich »** → verdict retombe à
   *indécidable*, avec léger avantage à (b) par l'argument C1. **Basculement immédiat.**
2. **Un graphique de la zone `Häufigkeitsklassen` ne trace que les courbes par programme**,
   sans série calculée → renforce C2 sans être décisif ; je passerais la confiance de
   ~85 % à ~65 % et je recommanderais de saisir la sous-commission avant tout figeage.
3. **Un classeur (Tests 6 ou 7) tabule une bande de distribution en `MIN`/`MAX`** →
   preuve directe et contraire ; bascule vers (b).
4. **Une entrée de la FAQ SIA** tranchant explicitement → autorité supérieure à toute
   inférence ci-dessus, quel que soit son sens.

Rien de ce qui précède ne remet en cause le §5.5 : la restitution à trois états reste
correcte sous (a) comme sous (b), et doit être implémentée dans les deux cas.
