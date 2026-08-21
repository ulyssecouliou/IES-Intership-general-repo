# Audit A5 — §7.2.4 « Installations de faible puissance électrique requise » : porte bloquante, diagnostic ou réserve ?

Analyste normatif — 2026-08-21. **Lecture seule, aucun code de production modifié.**
Fait suite au ruling A4 (`traceability/audit-A4-verdict-porte-decisive-sia3802.md`),
qui laissait §7.2.4 explicitement « hors périmètre A4, à instruire séparément »
(A4 §Zones d'incertitude).

Source : `refs/SIA-380-2-2022.pdf` (SN 504380/2:2022 fr), texte extrait
`.codex_tmp/sia3802_full.txt`. Normes renvoyées **absentes de `/refs`** :
SIA 180:2014, SIA 382/1, SIA 2024, SIA 2056, SIA 380 (faîtière) → voir
« Zones d'incertitude ».

---

## Texte normatif cité (verbatim)

**§7.2.4 Installations de faible puissance électrique requise** (PDF p. 32) :
- §7.2.4.1 : « Par installation de faible puissance requise, on entend les
  installations avec une puissance électrique requise pour le **transport des
  fluides** (air, eau et autre fluides) et le **conditionnement des fluides, y
  compris le refroidissement** ainsi que, le cas échéant, l'humidification et le
  traitement de l'eau. La surface de référence est la **surface nette de plancher
  conditionnée**. »
- §7.2.4.2 : « Les installations existantes et les installations rénovées dont la
  puissance électrique requise ne dépasse pas **12 W/m²**, **au lieu de 7 W/m²**,
  sont considérées comme installations de faible puissance requise. »
- §7.2.4.3 : taux de simultanéité sur la journée ; rendement/COP au dimensionnement ;
  améliorations à charge partielle non prises en compte ; composants à très faible
  consommation (clapets, commande) négligeables.

**§7.2.2.1** (PDF p. 31) : « Les **valeurs limites ET les exigences générales**
doivent être respectées dans les nouvelles constructions ainsi qu'en cas de
remplacement d'installations existantes. En cas de transformation […] dans le
cadre de ce qui est techniquement possible et économiquement supportable. »

**Renvois qui donnent à §7.2.4 sa force contraignante (tous dans §3.2
Refroidissement, PDF p. 21-22) :**
- §3.2.1.1 : « Lorsqu'une installation de refroidissement active est prévue, les
  exigences constructives selon 7.1.1 et 7.1.2 doivent être remplies, **excepté
  pour les installations de faible puissance requise selon 7.2.4**. »
- §3.2.3.1 Tableau 1, note 1) : refroidissement « souhaitable » / « non
  nécessaire » → « Refroidissement **admis seulement avec des installations de
  faible puissance selon 7.2.4**. »
- §3.2.5.2 : « Dans ce cas [refroidissement seulement souhaité ou superflu selon
  3.2.3 ou 3.2.4], **seules les installations de faible puissance électrique selon
  7.2.4 sont admises**. »

**Tableau 2** (§7.2.5.3, PDF p. 32-33) : la puissance électrique §7.2.4 **n'y
figure pas**. Elle n'est donc **pas une grandeur d'entrée du projet de référence**
ni un terme comparé en §7.2.5.2.

---

## Q1 — Porte bloquante, cible, ou diagnostic ?

**Verdict : PORTE BLOQUANTE — mais CONDITIONNELLE (déclenchée par la présence de
refroidissement dans la catégorie « admis seulement si faible puissance »).**

Le dépassement du seuil n'est pas une « cible » (§7.2.2.2 « valeurs cibles doivent
être visées » — vocabulaire non employé ici) ni un simple repère (§7.2.3 réserve ce
statut aux performances ponctuelles ventilation). La formulation est **impérative
d'admissibilité** : « admis **seulement** avec » (Tab. 1 note 1), « **seules** les
installations de faible puissance […] **sont admises** » (§3.2.5.2). Une
installation qui dépasse 7/12 W/m² dans ces cas **n'est pas admise** → le
refroidissement est non conforme → le bâtiment est **NON conforme**.

Le traitement actuel (alerte MEDIUM non bloquante) est donc **trop faible** dans les
cas gouvernés par Tab. 1 note 1) / §3.2.5.2.

**Restriction décisive (à ne pas sur-bloquer).** Le verrou d'admissibilité ne mord
que lorsque le refroidissement est « **souhaitable** », « **non nécessaire** » ou
« **souhaité ou superflu** » (§3.2.3.1 note 1 ; §3.2.5.2). Lorsque le
refroidissement est **nécessaire** (cas spéciaux §3.2.2 ; ligne « nécessaire » du
Tab. 1 ; surchauffe avérée §3.2.4.2-3, > 100 h/an, ou > 400 h/an en existant), la
norme **ne restreint pas** à la faible puissance : un dépassement de 7/12 n'est
alors **pas** en soi une violation d'admissibilité §3.2. Il déclenche seulement
§3.2.1.1 (les exigences constructives 7.1.1/7.1.2 redeviennent pleinement
exigibles, car l'exemption « faible puissance » tombe). Un blocage inconditionnel
de tout dépassement serait donc une **sur-interprétation**.

---

## Q2 — Subsumé par §7.2.5.2, ou exigence autonome (§7.2.2.1) ?

**Verdict : EXIGENCE AUTONOME. Non subsumée par la comparaison globale §7.2.5.2 ;
ce n'est PAS une réserve légitime de la comparaison.**

La puissance électrique §7.2.4 **n'apparaît pas au Tableau 2** — elle n'alimente
pas la valeur de projet comparée en §7.2.5.2 et n'est pas recalculée côté projet de
référence. Elle relève des « **exigences générales** » de §7.2.2.1 (« valeurs
limites **ET** exigences générales doivent être respectées ») et sert de
**condition d'admissibilité** du refroidissement via §3.2. Elle est donc **autonome
au même titre que les portes §7.1** retenues en A4 (été §7.1.2.1, commande de
protection solaire §7.1.2.2-5, ventilation §7.1.1). Satisfaire la porte globale
§7.2.5.2 **ne démontre pas** le respect de §7.2.4.

*Interprétation (marquée)* : le classement « autonome » découle de l'absence de
§7.2.4 au Tableau 2 combinée à §7.2.2.1 et aux verrous §3.2 ; il est cohérent avec
la doctrine A4 (Q1/Q2). Réserve : §7.2.4 est physiquement placé sous §7.2
(énergétique) et non sous §7.1 (construction) — cela ne change pas son caractère
autonome mais sa citation doit rester « §7.2.4 + §3.2.x », non « §7.1 ».

---

## Q3 — Neuf vs existant (7 vs 12) ; périmètre « refroidissement présent » ; bâtiment sans CVC

**Seuils :** §7.2.4.2 fixe explicitement **12 W/m²** pour installations
**existantes et rénovées**, « **au lieu de 7 W/m²** » → 7 W/m² est le seuil de
référence (**construction neuve / remplacement d'installations**). Le statut
neuf/existant/rénové se détermine par le **cas d'application selon SIA 380**
(§7.2.1.1 renvoie à SIA 380 — *faîtière absente de `/refs`*, [TO VERIFY] pour
l'appariement exact cas d'application ↔ 7/12).
*Interprétation légère* : « 7 W/m² pour le neuf » n'est écrit qu'en creux
(« au lieu de 7 »), mais la lecture est univoque.

**Périmètre.** §7.2.4.1 définit le périmètre par la **présence d'une installation**
de transport et/ou de conditionnement de fluides (air, eau, autres), refroidissement
inclus, ± humidification / traitement d'eau. Le seuil porte sur la puissance
électrique **de cette installation** rapportée à la surface nette conditionnée.

- **Bâtiment sans installation mécanique de transport/conditionnement** (ventilation
  purement naturelle, aucun refroidissement, aucune humidification) → **rien à
  mesurer** → **§7.2.4 HORS PÉRIMÈTRE (NOT_APPLICABLE)**. §7.2.4 n'a pas de clause
  générale « toute installation doit être ≤ 7/12 » : sa force contraignante ne
  s'exerce que via §3.2 (admissibilité du refroidissement) et via §3.2.1.1
  (exemption des exigences constructives). Sans installation, aucun de ces
  déclencheurs n'existe.
- **Le seuil s'applique-t-il toujours dès qu'il y a refroidissement ?** Le *calcul*
  ≤ 7/12 couvre **toute** la puissance de transport + conditionnement, pas seulement
  le compresseur de froid (§7.2.4.1). Mais le *verrou bloquant* ne s'active que
  quand le refroidissement relève de la catégorie « admis seulement si faible
  puissance » (cf. Q1). Refroidissement **nécessaire** → pas de plafond
  d'admissibilité, mais §3.2.1.1 s'applique.

---

## Q4 — Logique fail-closed exacte (si porte)

**Verdict : PORTE fail-closed, statut par cas.**

Nouvel item proposé (nommage indicatif) : `SIA3802_LOW_POWER_ELECTRICAL_7_2_4`.

Arbre de décision (citations entre crochets) :

1. **Aucune installation de transport/conditionnement de fluides** (pas de
   ventilation mécanique, pas de froid, pas d'humidification)
   → **NOT_APPLICABLE** [§7.2.4.1].
2. **Installation présente, mais puissance électrique requise (transport +
   conditionnement, W) / surface nette conditionnée (m²) NON fournie ou non
   relue** → **NOT_DETERMINED** (réserve fail-closed : « missing evidence never
   becomes PASS ») [§7.2.4.1, §7.2.4.3].
3. **Puissance connue, ≤ seuil** (7 W/m² neuf / 12 W/m² existant-rénové)
   → **satisfait** : installation de faible puissance ; exemption §3.2.1.1
   disponible [§7.2.4.2].
4. **Puissance connue, > seuil** → dépend de la catégorie de nécessité du
   refroidissement :
   - **Souhaitable / non nécessaire / souhaité ou superflu** (§3.2.3.1 Tab. 1
     note 1 ; §3.2.5.2) → **NOT_COMPLIANT** : refroidissement **non admis**.
   - **Nécessaire** établi (§3.2.2 ; ligne « nécessaire » Tab. 1 ; surchauffe
     avérée §3.2.4) → §7.2.4 **non bloquant sur la puissance**, mais **§3.2.1.1
     force** les exigences constructives 7.1.1/7.1.2 (rattacher à la porte été
     A3 + ventilation) ; statut §7.2.4 = **satisfait/NON décisif** sur le plan
     puissance, avec couplage signalé.
   - **Catégorie de nécessité indéterminable** (nécessite SIA 180 / SIA 2024,
     absents de `/refs`, ou données manquantes) → **NOT_DETERMINED** (fail-closed :
     on ne peut pas certifier que le dépassement est admissible).

**Conséquence globale** (cohérente A4/A5) : un item §7.2.4 en **NOT_COMPLIANT**
force le verdict global **NON conforme** ; en **NOT_DETERMINED** force
**NOT_DETERMINED** (jamais COMPLIANT-avec-réserve, car exigence autonome — cf. A4
Q4). NOT_APPLICABLE n'a aucun effet bloquant.

*Interprétation (marquée)* : la branche « nécessaire → non bloquant sur la
puissance » est déduite du silence de §3.2 (aucune restriction de puissance quand
le froid est nécessaire) ; à défaut de pouvoir classer la nécessité (SIA 180
absent), retomber en **NOT_DETERMINED** plutôt qu'en NOT_COMPLIANT évite le faux
échec tout en restant fail-closed.

---

## Synthèse

| Q | Objet | Verdict |
|---|-------|---------|
| 1 | Dépassement 7/12 W/m² : porte / cible / diagnostic | **PORTE BLOQUANTE CONDITIONNELLE** — bloque quand froid « souhaitable/superflu » (§3.2.3.1 n.1, §3.2.5.2) ; MEDIUM actuel trop faible ; ne pas sur-bloquer si froid nécessaire |
| 2 | Subsumé §7.2.5.2 ou autonome §7.2.2.1 | **EXIGENCE AUTONOME** — absente du Tableau 2, « exigences générales » §7.2.2.1 ; pas une réserve de la comparaison |
| 3 | 7 vs 12 ; périmètre ; sans CVC | 7 neuf / 12 existant-rénové (§7.2.4.2) ; périmètre = présence d'installation (§7.2.4.1) ; **sans installation → NOT_APPLICABLE** ; verrou lié à la catégorie de refroidissement |
| 4 | Logique fail-closed | **> seuil avéré (cas gouverné) = NOT_COMPLIANT** ; **valeur non fournie = NOT_DETERMINED** ; sans installation = NOT_APPLICABLE ; catégorie de nécessité inconnue = NOT_DETERMINED |

**Exigence vs interprétation.** Normatif (texte cité) : §7.2.4.1-3, §7.2.2.1,
§3.2.1.1, §3.2.3.1 (Tab. 1 note 1), §3.2.5.2, §7.2.5.3 (absence au Tableau 2).
Interprétation de l'analyste : les qualifications « porte autonome »,
« conditionnelle », l'appariement cas d'application ↔ 7/12, et la retombée
NOT_DETERMINED quand la catégorie de nécessité n'est pas classable.

## Zones d'incertitude
- **SIA 180:2014** (courbe limite fig. 3, annexe C) et **SIA 2024 / SIA 2056**
  (apports internes du Tab. 1) : requis pour classer la nécessité du refroidissement
  (souhaitable / nécessaire) — **absents de `/refs`** → la branche de classification
  Q4 est **non vérifiable ici** ([TO VERIFY]).
- **SIA 380 (faîtière)** : appariement exact « cas d'application 1/2 » ↔ seuil 7 vs
  12 W/m² — **absente de `/refs`** ([TO VERIFY]).
- Méthode de **relevé de la puissance électrique requise** (transport +
  conditionnement, avec taux de simultanéité §7.2.4.3) côté IESVE : à confirmer que
  la grandeur relue correspond bien à la définition §7.2.4.1 (puissance de
  dimensionnement, hors gains à charge partielle) — sinon la comparaison au seuil
  est invalide.
