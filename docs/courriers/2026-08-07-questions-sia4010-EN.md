# Projet de courriel — questions normatives SIA 4010

**À** : Yiqiao Yang (SIA)
**De** : Ulysse Couliou (IES)
**Date de rédaction** : 2026-08-07
**Statut** : **BROUILLON — à relire et envoyer par Ulysse.** Rien n'a été envoyé.

> Note de rédaction. Trois questions seulement : un courriel long obtient une
> réponse courte. Les deux premières sont établies et vérifiables — la
> sous-commission peut les recouper en ouvrant les classeurs. La troisième est
> plus ouverte et vient en dernier pour cette raison.
>
> Rédigé en anglais, comme les échanges précédents.

---

**Subject:** SIA 4010 — three questions on the evaluation workbooks (Tests 2–7)

Dear Mr Yang,

Thank you again for the documents and the pointers to the CH2018 dataset and
the SIA 2028/C2 corrigenda — both were exactly what we needed.

We are now implementing the SIA 4010 test evaluation in IES Virtual
Environment, working strictly from the official specifications and the
`Resultaterfassung` workbooks. Three points are not resolved by those
documents, and we would rather ask than assume. Each is reproducible from the
files you provided.

---

**1. Test 7 — the conditional-formatting rule uses a different lower bound
from the other six workbooks.**

In `Resultaterfassung Test7.xlsx`, sheet `Zusammenfassung`, the only place
where the tolerance band is actually applied is a conditional-formatting rule
on the test-program column:

```
sqref = F8:F12 F14:F18 F20
operator = between,  formulas = $L8 , $M8
```

In that sheet, `L7 = Mittelwert`, `M7 = Obere Grenze`, `N7 = Untere Grenze`.
The rule therefore spans **[mean ; upper bound]**, not
**[lower bound ; upper bound]**.

We compared the equivalent rule in all six workbooks by identifying the
columns from their formulas rather than their position:

| Workbook | mean | upper | lower | columns used by the rule | span |
|---|---|---|---|---|---|
| Test 1 | G | H | I | `$I`, `$H` | lower → upper |
| Test 2 | M | N | O | `$N`, `$O` | lower → upper |
| Test 3 | O | P | Q | `$Q`, `$P` | lower → upper |
| Test 4 | T | U | V | `$U`, `$V` | lower → upper |
| Test 6 | K | L | M | `$L`, `$M` | lower → upper |
| **Test 7** | **L** | **M** | **N** | **`$L`, `$M`** | **mean → upper** |

Test 7 is the only one of the six that differs. Is this an oversight in the
Test 7 workbook, or is the acceptance range for Test 7 intentionally
asymmetric?

Our engine currently applies the symmetric band, i.e. the same rule as the
other six workbooks, and this divergence is recorded as unresolved.

---

**2. The frequency-distribution criterion is stated in the specifications but
computed nowhere.**

The specifications of Tests 2, 3 and 5 state two acceptance criteria. The
first is unambiguous:

> « Jahressumme: Mittelwert +/- max. Abweichung der Referenzprogramme »

The second is:

> « Die Häufigkeitsverteilung muss im Streubereich der Referenzprogramme
> liegen. »

In the workbooks, every `Verteilung` sheet is a **chart**, not a table: it
plots the reference programs and the test program, and no cell anywhere
computes a band for a distribution. The judgement therefore appears to be
visual.

Two readings of `Streubereich` seem defensible to us, and they do not
coincide:

- the **envelope** of the reference programs, class by class — i.e.
  min…max;
- **mean ± maximum deviation**, which is the rule the same workbooks apply to
  the annual sums.

Which reading does the sub-commission intend? Our engine currently computes
both and reports the criterion as *not established*, so that no result is ever
declared compliant on an assumption.

A related detail: several reference programs total fewer than 8 760 hours in
those distributions (we observe 8 432, 8 567, 8 744, 8 759 …). We keep those
totals as they are. Should a program with an incomplete year be excluded from
the scatter band, or retained?

---

**3. Tests 4 and 6 — no `Testkriterien` section.**

The specifications of Tests 2, 3 and 5 each contain a `Testkriterien` section.
Those of Tests 4 and 6 do not, and clause 4.4 of SIA 4010:2023 delegates the
comparison to the evaluation workbook. Their workbooks contain neither
frequency classes nor distribution sheets.

We therefore assume that for Tests 4 and 6 the annual-sum band is the **only**
criterion, and that the formula is the same as elsewhere. Could you confirm?

---

Thank you in advance. We are happy to share our reading of the workbooks in
more detail if that would be useful to the sub-commission.

Kind regards,

Ulysse Couliou
IES — Integrated Environmental Solutions

---

## Ce qui n'est PAS dans ce courriel, et pourquoi

- **L'irradiance solaire de Kloten.** Ce n'est pas une question normative mais
  une question de licence de données : à traiter avec Johan d'abord, et avec
  la SIA seulement si IES n'a pas déjà accès aux données SIA 2028.
- **Le point de consigne du Test 4, dessiné et non écrit.** Nous l'avons lu
  sur le graphique et les quatre points d'inflexion y sont annotés en clair.
  La seule déduction restante — quelle courbe est le chauffage, quelle courbe
  le refroidissement — est corroborée par la largeur de la bande morte. Poser
  la question affaiblirait les trois autres en les noyant ; à garder pour un
  second échange si besoin.
- **Toute question d'implémentation IESVE.** Elle ne regarde pas la SIA.
