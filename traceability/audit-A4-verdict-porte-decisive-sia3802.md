# Audit A4 — La porte §7.2.5.2 est-elle le critère décisif unique du verdict SIA 380/2 ?

Analyste normatif — 2026-08-21. Lecture seule, aucun code de production modifié.
Cible : `swiss_sia/compliance_verdict.py:221-270` (« Product decision 2026-08-19,
PENDING norm-analyst / qa-auditor sign-off »).

Source : `refs/SIA-380-2-2022.pdf` (SN 504380/2:2022 fr), texte extrait dans
`.codex_tmp/sia3802_full.txt`. Renvois SIA 180:2014, SIA 382/1, SIA 2028:2010
cités par la norme mais **absents de `/refs`** → voir « Zones d'incertitude ».

---

## Fait normatif structurant : chapitre 7 « EXIGENCES »

SIA 380/2:2022 sépare explicitement deux familles d'exigences :

- **§7.1 Exigences relatives à la construction** (p. 31) — autonomes :
  - §7.1.1 ventilation → « définies dans SIA 382/1 ».
  - §7.1.2 Protection contre la chaleur en été. §7.1.2.1 : « Les exigences […]
    sont définies selon **SIA 180:2014, chapitre 5** ». §7.1.2.2–7.1.2.5 :
    exigences supplémentaires de **commande de la protection solaire**
    (asservissement par façade, commande automatique sur l'irradiance,
    lanterneaux séparés).
- **§7.2 Exigences énergétiques** (p. 31-32) :
  - §7.2.2.1 : « Les **valeurs limites ET les exigences générales** doivent être
    respectées » → la conformité énergétique n'est pas réductible aux seules
    valeurs limites.
  - §7.2.3 : les performances ponctuelles ventilation (SIA 382/1) « lorsque les
    exigences globales sont respectées selon 7.2.5, elles ne doivent pas être
    respectées » (elles deviennent de simples repères).
  - §7.2.4 : installations de faible puissance électrique requise (seuil
    ≤ 7 W/m², ≤ 12 W/m² pour existant/rénové) — exigence conditionnant
    l'admission du refroidissement (renvoyée par §3.2.3.1 note 1, §3.2.5.2).
  - §7.2.5 Performances globales : §7.2.5.2 « La performance globale est
    respectée lorsque la valeur de projet selon le chapitre 6 est inférieure à
    la valeur limite ou à la valeur cible correspondante du projet de
    référence » ; §7.2.5.3 + **Tableau 2** listent les grandeurs d'entrée du
    projet de référence.

**Tableau 2 (p. 32-33)** — les composants sont des *données d'entrée* du projet
de référence (valeur « spéc. au proj. » côté projet, valeur standard côté
référence) : Uw (réf. 1,1 / cible 0,88 W/m²K), **ponts thermiques ψ, χ (réf. 0 /
cible 0)**, part de cadre ff (0,25), taux de vitrage fg (SIA 2024), g⊥ (0,50),
τ (0,70), protection solaire (store à lamelles extérieur).

---

## Q1 — §7.2.5.2 critère décisif ; les composants sont-ils de simples entrées ?

**Verdict : À CORRIGER (partiel).**

Correct pour les composants du Tableau 2. §7.2.5.2 est bien la porte décisive de
la **performance globale énergétique** ; §7.2.5.3 + Tableau 2 confirment que Uw,
ψ/χ, ff, fg, g⊥, τ, protection solaire sont des *entrées* du projet de référence,
pas des exigences autonomes. §7.2.3 confirme de plus que les performances
ponctuelles ventilation s'effacent quand §7.2.5 est satisfait. Traiter ces
diagnostics-là comme « réserves » est **conforme**.

Faux comme règle générale. §7.2.2.1 impose « valeurs limites **ET** exigences
générales » ; §7.1 pose des exigences **de construction autonomes** que la
comparaison globale ne subsume pas :
1. protection contre la chaleur en été (§7.1.2.1 → SIA 180:2014 ch.5),
2. commande de la protection solaire (§7.1.2.2–7.1.2.5),
3. ventilation SIA 382/1 (§7.1.1) — le code l'exempte déjà (« essential gate »),
4. faible puissance électrique §7.2.4 lorsque du refroidissement est présent.

Le code applique un « les composants sont des réserves » **trop large** : il
n'excepte que la ventilation. Les exigences §7.1 (été, commande protection
solaire) doivent rester des **portes autonomes**, pas des réserves.

**Nuance décisive sur les ponts thermiques (interprétation, justifiée).** ψ/χ
sont une *entrée Tableau 2 du côté projet* : ils alimentent la valeur de projet
comparée en §7.2.5.2. S'ils sont `NOT_AVAILABLE_IN_VE`, l'indice de projet porté
dans la comparaison est *incomplet/sous-estimé* → la prémisse « comparaison
relue et satisfaite » n'est plus garantie. Ce n'est une simple réserve que si le
relecteur atteste que la comparaison intègre déjà les ponts thermiques réels ;
sinon → `NOT_DETERMINED`.

Logique de verdict attendue : conserver §7.2.5.2 comme porte décisive de la
performance globale, mais ajouter des portes autonomes §7.1 (été, commande
protection solaire) au même titre que la ventilation, et ne rétrograder un
diagnostic Tableau 2 en réserve que s'il est effectivement pris en compte dans
la comparaison relue.

---

## Q2 — Protection thermique estivale : exigence autonome ? Correctif A3 bloquant ?

**Verdict : CONFORME À LA NORME (A3 justifié).**

La protection contre la chaleur en été est une **exigence autonome de
construction** : §7.1.2.1 la définit « selon SIA 180:2014, chapitre 5 », hors du
§7.2 énergétique. §3.2.1.1 et §3.2.1.3 confirment que les exigences
constructives §7.1.1/§7.1.2 doivent être remplies « même si » le refroidissement
est omis. §3.2.4.2 fixe le critère : nécessité de refroidir avérée « lorsque la
courbe limite supérieure de la figure 3 dans SIA 180:2014 est dépassée »
(§3.2.4.3 : > 100 h/an ; §3.2.4.5 : 400 h/an en existant).

Donc rendre **bloquante une surchauffe DÉTERMINÉE**
(`SIA3802_SUMMER_COMFORT_DYNAMIC`, HIGH) est correct : c'est une exigence
§7.1.2, pas un simple renvoi facultatif. Garder le cas *non vérifiable*
(APS annuel manquant / climat non conforme) en **réserve `NOT_DETERMINED`** est
également correct (fail-closed, pas de faux échec).

Réserve de citation : le seuil pass/échec appartient à SIA 180 (courbe limite
supérieure) — le verdict doit citer « exigence SIA 380/2:2022 §7.1.2.1 → SIA
180:2014 ch.5 / §3.2.4 » et non revendiquer un critère 380/2 propre. La règle A3
doit s'appuyer sur les paramètres annexe C et Tableau 2 (§3.2.4.6-7).

---

## Q3 — Puissance de dimensionnement (jours de dimensionnement) : exigence ou donnée ?

**Verdict : RÉSERVE ACCEPTABLE.**

Le chapitre 4 « Puissance thermique requise pour le chauffage et le
refroidissement » est une **méthode de calcul** produisant les puissances de
dimensionnement : §4.2.1 chauffage sur données de dimensionnement SIA 2028:2010
§3.8 (WDD, éq. 1) ; §4.3.1.1 refroidissement sur SIA 2028:2010 §3.7 (3 jours de
référence, SDD, éq. 2). Ces puissances servent au **dimensionnement des
composants** (§6.4.1-6.4.3), pas à une comparaison de conformité.

Le chapitre 7 EXIGENCES ne fixe **aucune valeur limite sur la puissance requise
elle-même**. La seule exigence chiffrée liée à la puissance est §7.2.4
(puissance *électrique* des installations ≤ 7 / 12 W/m²), qui est distincte des
jours de dimensionnement. Donc `SIA3802_DESIGN_POWER_DAYS = NOT_AVAILABLE_IN_VE`
en réserve dans un dossier COMPLIANT est **acceptable pour la conformité 380/2**
(données annexes de dimensionnement).

Réserve d'interprétation : §7.2.4 (seuil W/m² électrique, admission du
refroidissement §3.2.3.1/§3.2.5.2) EST une exigence lorsqu'un refroidissement
est présent ; elle ne doit pas être confondue avec les jours de dimensionnement
et devrait, elle, être vérifiée (aujourd'hui non traitée — à noter).

---

## Q4 — Peut-on afficher COMPLIANT avec des composants NOT_CHECKABLE ?

**Verdict : À CORRIGER (nuancé).**

Principe applicable (règles projet + esprit fail-closed du module, docstring
l.3-4) : « missing evidence never becomes PASS ». Décomposition :

- Diagnostic **non décisif et non autonome** (repère ponctuel §7.2.3, entrée
  Tableau 2 déjà intégrée à la comparaison relue) `NOT_CHECKABLE` →
  COMPLIANT + réserve visible est **acceptable**.
- Entrée **Tableau 2 décisive non intégrée** (ex. ponts thermiques absents
  alimentant la valeur de projet) `NOT_AVAILABLE` → la comparaison n'est pas
  vérifiée → **`NOT_DETERMINED`**, pas COMPLIANT-avec-réserve.
- Exigence **autonome §7.1** (été, commande protection solaire, ventilation)
  `NOT_CHECKABLE` → **`NOT_DETERMINED`**. Le code n'excepte aujourd'hui que la
  ventilation ; il faut étendre aux autres portes §7.1.

Le libellé « réserve » ne doit s'appliquer qu'à des éléments réellement non
décisifs et non autonomes. Le COMPLIANT-avec-réserves global est **trop
permissif** tant que subsistent des inconnues sur une entrée décisive de la
comparaison ou sur une exigence §7.1 autonome.

Logique de verdict attendue : classer chaque item en {décisif-comparaison,
exigence-autonome-§7.1, diagnostic-non-décisif}. Un item des deux premières
catégories en `NOT_CHECKABLE`/`NOT_AVAILABLE` force `NOT_DETERMINED` ; seule la
troisième reste réserve compatible COMPLIANT.

---

## Synthèse

| Q | Objet | Verdict |
|---|-------|---------|
| 1 | §7.2.5.2 porte décisive, composants = entrées | À CORRIGER (partiel) — vrai pour Tableau 2 ; §7.1 sont des exigences autonomes |
| 2 | Surchauffe estivale (§7.1.2.1 / SIA 180) | CONFORME — A3 bloquant justifié |
| 3 | Puissance de dimensionnement (ch. 4) | RÉSERVE ACCEPTABLE — donnée de dimensionnement, non exigence 380/2 |
| 4 | COMPLIANT malgré composants NOT_CHECKABLE | À CORRIGER — permis seulement pour items non décisifs/non autonomes |

Distinction exigence / interprétation : les statuts §7.1, §7.2.2.1, §7.2.3,
§7.2.5.2-3 + Tableau 2, §4.2/§4.3, §7.2.4 sont **normatifs** (texte cité). Les
qualifications « décisif », « autonome », « entrée intégrée à la comparaison »,
et la conséquence `NOT_DETERMINED` sont **interprétation** de l'analyste, fondée
sur §7.2.2.1 (« valeurs limites ET exigences générales ») et sur la nature
d'entrée Tableau 2 des ponts thermiques.

## Zones d'incertitude

- **SIA 180:2014**, **SIA 382/1**, **SIA 2028:2010** : renvoyés par la norme
  mais **absents de `/refs`** — critères de surchauffe (courbe limite fig. 3),
  exigences ventilation ponctuelles et données climatiques de dimensionnement
  **non vérifiables ici** ([TO VERIFY]).
- §7.2.4 (seuil électrique W/m² admission refroidissement) : exigence non
  traitée par le verdict actuel — hors périmètre A4, à instruire séparément.
- Le caractère « déjà intégré à la comparaison relue » des ponts thermiques
  dépend du contenu réel du CSV `global_reference_comparison` relu par le
  mandataire : à confirmer au cas par cas (attestation relecteur).
