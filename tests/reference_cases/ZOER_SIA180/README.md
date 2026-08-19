# Cas de référence — SIA 180:2014, surchauffe estivale (dossier ZOER)

*Golden reference fixture* pour la vérification de la protection thermique
estivale (sommerlicher Wärmeschutz) selon **Minergie Verfahren 3**, en appui sur
**SIA 180:2014** (Annexes C1 et C2) et **SIA 382/1:2014**, à partir du dossier
client réel et validé du **Hochhaus Regensbergbrücke** (Zürich Oerlikon).

L'oracle (vérité-terrain) est le rapport
`VE - Validation for Swiss Building Regs/32_ZOER_Simulationsbericht_20251208.pdf`.
La fixture reproduit ses 6 verdicts par un recalcul indépendant, en Python pur,
**sans IESVE**.

Périmètre : trois zones critiques orientées SW/SE — Zone 1 & Zone 2 (OG02,
usage Restaurant), Zone 3 (OG10, usage Bildung).

## Les deux vérifications

| Cas | Norme | Critère (rapport §3.2 / §3.3) | Période / heures |
|-----|-------|-------------------------------|------------------|
| **C1** — baulische Grundanforderungen | SIA 180 Anhang C1, **Fig.3 SIA 180** | Opérative **jamais** au-dessus de la courbe sup. ni sous la courbe inf. | 16.04 → 15.10, **24 h/24, week-ends inclus** |
| **C2** — thermischer Komfort | SIA 180 Anhang C2, **Fig.4 SIA 180** | Courbe sup. dépassée **≤ 100 h/a** ; courbe inf. jamais franchie | **heures occupées** (People gain > 0) |

## Lancer

```bash
python -m pytest tests/reference_cases/ZOER_SIA180/test_reference.py -v
```

Recalcul manuel des 6 verdicts :

```bash
python -c "import sys; sys.path.insert(0,'tests/reference_cases/ZOER_SIA180'); import evaluate as E; \
[print(E.evaluate_zone_c1(z)) for z in (1,2,3)]; [print(E.evaluate_zone_c2(z)) for z in (1,2,3)]"
```

## Fourniture des données

Les 6 classeurs `Zone X_C{1,2}_Ergebnisse_2035_RCP85_DRY.xlsx` et
`Luftvolumenstrom.xlsx` vivent dans `VE - Validation for Swiss Building Regs/`
à la racine du dépôt. **Ce dossier est gitignored** : les tests d'intégration
sont automatiquement **sautés** (`skipif`) si les fichiers sont absents (CI sans
données). Les tests unitaires (courbes, θrm, sommets Fig.4) tournent toujours.

Climat des simulations : `SMA_2035_RCP85_DRY.epw` (Design Reference Year,
RCP 8.5, horizon 2035, station Zürich SMA). Séries opératives issues de
`ZOER_C1.aps` / `ZOER_C2.aps`.

## Modules

| Fichier | Rôle |
|---------|------|
| `loader.py` | Lecture `.xlsx`, appariement **par horodatage**, séries propres. Aucune logique normative. |
| `sia180_curves.py` | Équations Fig.3 / Fig.4 (fonctions pures, citations). |
| `theta_rm.py` | Moyenne glissante extérieure sur 48 h. |
| `evaluate.py` | Orchestration → comptages + verdict PASS/FAIL par zone/cas. |
| `test_reference.py` | Tests pytest (unitaires + intégration/oracle). |
| `TRACEABILITY.md` | Matrice de traçabilité, signée QA. |

## Schéma des données (relevé et validé)

- Onglet source = **`Ergebnisse`** uniquement (`Zusammenfassung` / `Grafik` sont
  des formules non recalculées → `data_only` y renvoie `None`).
- **C1** : en-têtes lignes 1-3, données dès la ligne 4. Col D (idx 3) = opérative
  (HH:30) ; col O (idx 14) = extérieure dry-bulb (HH:00).
- **C2** : marqueurs « Paste below » ligne 1, en-têtes lignes 2-4, données dès la
  ligne 5. Col F (idx 5) = opérative (HH:30) ; col C (idx 2) = extérieure (HH:00) ;
  col I (idx 8) = People gain (kW).
- 4392 pas horaires = 183 jours × 24 h.

### Pièges d'appariement (résolus)

1. **HH:30 vs HH:00** — opératif à la demi-heure, extérieur à l'heure ronde. On
   apparie par **(date, heure)**, jamais par index de ligne.
2. **Décalage du jour de semaine (C2)** — le bloc extérieur porte un calendrier
   de jours de semaine décalé d'un jour par rapport au bloc opératif
   (« Thu, 16/Apr » vs « Wed, 16/Apr »). La **date** (« 16/Apr ») concorde ; on
   apparie donc sur la date, pas sur le libellé complet. *(Ne pas apparier sur ce
   libellé écarterait 100 % des heures → faux-PASS ; un test garde contre ça.)*
3. **Pas extérieur manquant (C1)** — 4392 opératives vs 4391 extérieures : le
   premier créneau (16.04 00:30) n'a pas d'extérieur. Ce pas unique est écarté du
   verdict (θrm indéfini). Sans effet (avril, marge maximale).

## Points `[À VÉRIFIER]` encore ouverts

- **Fig.3 SIA 180 (C1)** — les équations `max(25 ; 0,33·θrm + 21,8)` (sup.) et
  `0,33·θrm + 14,3` (inf.) sont **transcrites des étiquettes imprimées sur la
  figure du rapport** (Abbildung 3), pas confrontées à SIA 180:2014, Figure 3
  publiée (page non en notre possession). Le plateau bas à 25 °C est une lecture
  graphique. → cible de réplication de l'oracle, mais confirmation normative
  directe à faire.
- **Convention de bord θrm (48 premières heures)** — fenêtre tronquée retenue.
  Vérifié robuste (48 vs 49 termes, fenêtre incluant/excluant l'heure courante :
  verdict PASS inchangé dans les 3 cas). *Voir la réserve de marge ci-dessous.*
- **Extrapolation Fig.4 hors domaine θrm ∈ [10, 25]** — prolongement plat.
  Sans effet sur les verdicts ZOER.

### ⚠ Réserve de marge (importante)

Contrairement à l'hypothèse « marge large » du brief, la marge réelle est
**mince** : au pire créneau, l'opérative passe seulement **0,03 à 0,12 °C** sous
la courbe. Le verdict PASS **est** reproduit, et **reste** PASS sous les trois
conventions de θrm testées — mais les conventions d'appariement et de fenêtre
sont donc **porteuses**, pas anecdotiques. Toute évolution du recalcul doit
re-vérifier ces marges.

## Statut

`sia180_curves.FIG4_*` = **VÉRIFIÉ** (vectoriel, recoupé 8/8 — cf. TRACEABILITY).
`sia180_curves.FIG3_*` = **transcrit de l'oracle**, `[À VÉRIFIER]` contre la
norme publiée. Le cas n'est donc pas déclaré « vert plein » : voir TRACEABILITY.
