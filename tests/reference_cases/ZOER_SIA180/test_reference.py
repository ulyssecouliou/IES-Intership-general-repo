"""Tests de la fixture de référence SIA 180 — dossier ZOER.

Deux familles :
* Tests UNITAIRES purs (courbes, θrm, sommets Fig.4 vs JSON figé) — toujours
  exécutés, sans fichier d'entrée.
* Tests d'INTÉGRATION reproduisant les 6 verdicts du rapport-oracle — exécutés
  seulement si les classeurs ``.xlsx`` sont présents (ils sont hors dépôt /
  gitignored ; voir README §Fourniture des données).

Marqueur pytest : ``sia4010`` (machinerie de validation), cohérent avec
``tests/conftest.py``.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import evaluate as E  # noqa: E402
import loader as L  # noqa: E402
import sia180_curves as C  # noqa: E402
import theta_rm as T  # noqa: E402

pytestmark = pytest.mark.sia4010

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Les 6 classeurs sont-ils disponibles ? Sinon on saute l'intégration.
_INPUTS_PRESENT = all(
    os.path.exists(os.path.join(L.DEFAULT_INPUT_DIR, name))
    for name in (
        "Zone 1_C1_Ergebnisse_2035_RCP85_DRY.xlsx",
        "Zone 1_C2_Ergebnisse_2035_RCP85_DRY.xlsx",
        "Zone 2_C1_Ergebnisse_2035_RCP85_DRY.xlsx",
        "Zone 2_C2_Ergebnisse_2035_RCP85_DRY.xlsx",
        "Zone 3_C1_Ergebnisse_2035_RCP85_DRY.xlsx",
        "Zone 3_C2_Ergebnisse_2035_RCP85_DRY.xlsx",
    )
)
requires_inputs = pytest.mark.skipif(
    not _INPUTS_PRESENT,
    reason="classeurs ZOER absents (hors dépôt) — voir README §Fourniture des données",
)


# --------------------------------------------------------------------------- #
# Tests unitaires purs — courbes SIA 180                                       #
# --------------------------------------------------------------------------- #
def test_fig3_upper_plateau_and_slope():
    # Plateau bas à 25 °C ; puis 0,33·θrm + 21,8 (Abbildung 3 du rapport).
    assert C.fig3_upper(0.0) == pytest.approx(25.0)
    assert C.fig3_upper(9.0) == pytest.approx(25.0)          # 0,33·9+21,8=24,77 < 25 → plateau
    assert C.fig3_upper(10.0) == pytest.approx(25.1)         # 0,33·10+21,8
    assert C.fig3_upper(20.0) == pytest.approx(28.4)


def test_fig3_lower_line():
    assert C.fig3_lower(0.0) == pytest.approx(14.3)
    assert C.fig3_lower(10.0) == pytest.approx(17.6)
    assert C.fig3_lower(27.0) == pytest.approx(23.21)


def test_fig4_vertices_and_interpolation():
    # Sommets exacts.
    assert C.fig4_upper(10.0) == pytest.approx(24.5)
    assert C.fig4_upper(12.0) == pytest.approx(24.5)
    assert C.fig4_upper(17.5) == pytest.approx(26.5)
    assert C.fig4_upper(25.0) == pytest.approx(26.5)
    assert C.fig4_lower(10.0) == pytest.approx(20.5)
    assert C.fig4_lower(19.0) == pytest.approx(20.5)
    assert C.fig4_lower(23.5) == pytest.approx(22.0)
    # Interpolation à mi-segment (12 → 17,5) : +2 K sur 5,5 K.
    assert C.fig4_upper(14.75) == pytest.approx(25.5)
    # Clamp plat hors domaine.
    assert C.fig4_upper(5.0) == pytest.approx(24.5)
    assert C.fig4_upper(30.0) == pytest.approx(26.5)
    assert C.fig4_lower(5.0) == pytest.approx(20.5)


def test_fig4_vertices_match_frozen_reference_json():
    """Les sommets de Fig.4 ne doivent pas dériver du JSON figé de référence."""
    path = os.path.join(_REPO_ROOT, "refs", "reference-data", "sia-380-2-2022.figure1.json")
    with open(path, encoding="utf-8") as f:
        ref = json.load(f)
    up = [tuple(p) for p in ref["courbes"]["limite_superieure"]["sommets"]]
    lo = [tuple(p) for p in ref["courbes"]["limite_inferieure"]["sommets"]]
    assert C.FIG4_UPPER_VERTICES == up
    assert C.FIG4_LOWER_VERTICES == lo


# --------------------------------------------------------------------------- #
# Tests unitaires purs — θrm                                                   #
# --------------------------------------------------------------------------- #
def test_theta_rm_known_sequence():
    ext = [10.0, 20.0, 30.0, 40.0]
    got = T.rolling_mean_48h(ext, window=2)
    assert got == pytest.approx([10.0, 15.0, 25.0, 35.0])


def test_theta_rm_skips_none_and_handles_empty_window():
    ext = [None, 10.0, 20.0]
    got = T.rolling_mean_48h(ext, window=2)
    assert got[0] is None          # fenêtre sans aucune valeur
    assert got[1] == pytest.approx(10.0)
    assert got[2] == pytest.approx(15.0)


# --------------------------------------------------------------------------- #
# Intégration — reproduction de l'oracle (rapport PDF §7)                      #
# --------------------------------------------------------------------------- #
@requires_inputs
def test_loader_header_mapping_all_six_files():
    """Le loader valide le mapping §Schéma sur les 6 fichiers (via ses asserts)."""
    for z in (1, 2, 3):
        c1 = L.load_c1(z)
        c2 = L.load_c2(z)
        assert len(c1.steps) == 4392, f"C1 Z{z}: 4392 pas horaires attendus"
        assert len(c2.steps) == 4392, f"C2 Z{z}: 4392 pas horaires attendus"


@requires_inputs
def test_zone1_c1_non_regression():
    """Non-régression : Zone 1 C1 → max opérative 29,83 °C, 0 h de dépassement."""
    r = E.evaluate_zone_c1(1)
    assert r.max_operative == pytest.approx(29.83, abs=0.01)
    assert r.n_above_upper == 0
    assert r.n_below_lower == 0
    assert r.verdict == "PASS"


@requires_inputs
@pytest.mark.parametrize("zone,max_op", [(1, 29.83), (2, 29.49), (3, 29.84)])
def test_c1_verdicts_all_zones(zone, max_op):
    """Oracle §7 : C1 zones 1/2/3 → PASS, aucune heure hors courbes Fig.3."""
    r = E.evaluate_zone_c1(zone)
    assert r.n_above_upper == 0
    assert r.n_below_lower == 0
    assert r.max_operative == pytest.approx(max_op, abs=0.01)
    assert r.verdict == "PASS"


@requires_inputs
@pytest.mark.parametrize("zone,n_occ", [(1, 2379), (2, 2379), (3, 2013)])
def test_c2_verdicts_all_zones(zone, n_occ):
    """Oracle §7 : C2 zones 1/2/3 → PASS, 0 h au-dessus de Fig.4 (< seuil 100).

    Encode LES DEUX : le seuil normatif (≤ 100 h/a) ET la valeur observée
    attendue par le rapport (0 h). Garde aussi contre le faux-PASS : toutes les
    heures occupées doivent être évaluées (aucune écartée faute de θrm).
    """
    r = E.evaluate_zone_c2(zone)
    assert r.n_occupied == n_occ
    assert r.skipped_no_theta_rm == 0, "faux-PASS : des heures occupées non évaluées"
    assert r.n_below_fig4_lower == 0
    assert r.n_outside_fig3 == 0
    # Valeur observée par l'oracle : 0 h au-dessus de Fig.4 …
    assert r.n_above_fig4_upper == 0
    # … qui satisfait a fortiori le seuil normatif ≤ 100 h/a.
    assert r.n_above_fig4_upper <= r.fig4_hour_threshold
    assert r.verdict == "PASS"


@requires_inputs
def test_people_gain_occupancy_gap():
    """Le seuil d'occupation « People gain > 0 » est net : rien dans (0 ; 0,05] kW."""
    case = L.load_c2(1)
    small = [s.people_gain for s in case.steps
             if s.people_gain is not None and 0.0 < s.people_gain <= 0.05]
    assert small == [], "des valeurs de People gain proches de 0 rendraient le seuil ambigu"
