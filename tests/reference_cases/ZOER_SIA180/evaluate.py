"""Orchestration : produit les comptages et le verdict SIA 180 par zone/cas.

Fonctions pures. Aucune constante normative ici — tout provient de
``sia180_curves`` (courbes) et ``theta_rm`` (moyenne glissante).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import List, Optional

# Import des modules frères comme modules de premier niveau : le répertoire de
# la fixture n'est pas un paquet Python (tests/ ne l'est pas), donc on garantit
# qu'il est sur sys.path avant l'import absolu.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sia180_curves as curves  # noqa: E402
from loader import ZoneCase, load_c1, load_c2  # noqa: E402
from theta_rm import rolling_mean_48h  # noqa: E402

# Seuil normatif C2 : la courbe sup. de Fig.4 peut être dépassée ≤ 100 h/an
# pendant la Nutzungszeit (rapport §3.3, « nicht mehr als 100 h/a »).
FIG4_MAX_HOURS_PER_YEAR = 100

# Tolérance de comparaison flottante (les opératives sont à 0,01 °C près).
_EPS = 1e-6


@dataclass(frozen=True)
class C1Result:
    zone: int
    case: str
    n_hours_evaluated: int
    n_above_upper: int
    n_below_lower: int
    max_operative: float
    min_operative: float
    verdict: str  # "PASS" / "FAIL"
    skipped_no_theta_rm: int = 0


@dataclass(frozen=True)
class C2Result:
    zone: int
    case: str
    n_occupied: int
    n_above_fig4_upper: int
    n_below_fig4_lower: int
    n_outside_fig3: int  # observation (résumé rapport) : hors courbes Fig.3
    fig4_hour_threshold: int
    verdict: str
    skipped_no_theta_rm: int = 0


def _theta_rm_series(case: ZoneCase) -> List[Optional[float]]:
    return rolling_mean_48h([s.exterior for s in case.steps])


def evaluate_c1(case: ZoneCase) -> C1Result:
    """C1 — baulische Grundanforderungen : toutes les heures, week-ends inclus.

    PASS si aucune opérative au-dessus de la courbe sup. Fig.3 ni sous la
    courbe inf. (rapport §3.2).
    """
    theta = _theta_rm_series(case)
    n_above = n_below = evaluated = skipped = 0
    ops = [s.operative for s in case.steps]
    for s, th in zip(case.steps, theta):
        if th is None:
            skipped += 1
            continue
        evaluated += 1
        if s.operative > curves.fig3_upper(th) + _EPS:
            n_above += 1
        if s.operative < curves.fig3_lower(th) - _EPS:
            n_below += 1
    verdict = "PASS" if (n_above == 0 and n_below == 0) else "FAIL"
    return C1Result(
        zone=case.zone,
        case=case.case,
        n_hours_evaluated=evaluated,
        n_above_upper=n_above,
        n_below_lower=n_below,
        max_operative=max(ops),
        min_operative=min(ops),
        verdict=verdict,
        skipped_no_theta_rm=skipped,
    )


def evaluate_c2(case: ZoneCase) -> C2Result:
    """C2 — thermischer Komfort : heures occupées uniquement (People gain > 0).

    PASS (critère formel §3.3) si la courbe sup. de Fig.4 est dépassée
    ≤ 100 h/an ET la courbe inf. de Fig.4 n'est jamais franchie. On rapporte
    aussi ``n_outside_fig3`` (hors des courbes de Fig.3), observation du résumé.
    """
    theta = _theta_rm_series(case)
    n_above4 = n_below4 = n_outside3 = skipped = 0
    for s, th in zip(case.steps, theta):
        if not s.occupied:
            continue
        if th is None:
            skipped += 1
            continue
        if s.operative > curves.fig4_upper(th) + _EPS:
            n_above4 += 1
        if s.operative < curves.fig4_lower(th) - _EPS:
            n_below4 += 1
        if (
            s.operative > curves.fig3_upper(th) + _EPS
            or s.operative < curves.fig3_lower(th) - _EPS
        ):
            n_outside3 += 1
    verdict = (
        "PASS" if (n_above4 <= FIG4_MAX_HOURS_PER_YEAR and n_below4 == 0) else "FAIL"
    )
    return C2Result(
        zone=case.zone,
        case=case.case,
        n_occupied=case.n_occupied,
        n_above_fig4_upper=n_above4,
        n_below_fig4_lower=n_below4,
        n_outside_fig3=n_outside3,
        fig4_hour_threshold=FIG4_MAX_HOURS_PER_YEAR,
        verdict=verdict,
        skipped_no_theta_rm=skipped,
    )


def evaluate_zone_c1(zone: int, input_dir: Optional[str] = None) -> C1Result:
    kw = {"input_dir": input_dir} if input_dir else {}
    return evaluate_c1(load_c1(zone, **kw))


def evaluate_zone_c2(zone: int, input_dir: Optional[str] = None) -> C2Result:
    kw = {"input_dir": input_dir} if input_dir else {}
    return evaluate_c2(load_c2(zone, **kw))
