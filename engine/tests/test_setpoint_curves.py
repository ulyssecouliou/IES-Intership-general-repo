# -*- coding: utf-8 -*-
"""Tests for `engine/setpoint_curves.py`.

The decisive test here is `test_reproduces_the_ten_shifts_of_sia_4010`: SIA 4010
§3.1.4 publishes ten shift values across seven usages, and they must all fall
out of SIA 2024:2021 table 11 through the rule of SIA 380/2 §5.2.2.5. That is a
reference reproduction in the sense of CLAUDE.md rule 2 -- not a restatement of
the module's own constants -- because the ten values were printed by a different
committee in a different document from the table they are derived from.

The remaining tests split into two families:
  1. the embedded constants must equal the frozen JSON in refs/reference-data/,
     so the module cannot drift from its source;
  2. mutation resistance -- each asserts something a plausible wrong
     implementation would get wrong (sign of the shift, which end of a curve is
     taken for the constant setpoints, clamping direction, silent defaults).
"""

import io
import json
import os

import pytest

from engine import setpoint_curves as sc

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
_REFS = os.path.join(_RACINE, "refs", "reference-data")


def _charger(nom):
    chemin = os.path.join(_REFS, nom)
    if not os.path.exists(chemin):
        pytest.skip("référentiel absent : %s" % nom)
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def figure1():
    return _charger("sia-380-2-2022.figure1.json")


@pytest.fixture(scope="module")
def sia2024():
    return _charger("sia-2024-2021.tables.json")


# --------------------------------------------------------------------------
# 1. Reproduction of published references
# --------------------------------------------------------------------------

# SIA 4010:2023 §3.1.4, p. 10 — "a lower limit curve and thus a setpoint
# curve shifted by 1 K for usages 3.04 ticket counter hall, 5.01 to 5.03
# (retail stores) and 6.03 and 6.04 (kitchens), and by
# 3 K for usage 9.01 production (heavy work). An upward shift of
# the upper setpoint curve occurs for usages 6.03 and 6.04 (kitchens)
# by 2 K, for usage 9.01 by 4 K."
DECALAGES_PUBLIES_INFERIEURE = {
    "3.04": 1.0,
    "5.01": 1.0,
    "5.02": 1.0,
    "5.03": 1.0,
    "6.03": 1.0,
    "6.04": 1.0,
    "9.01": 3.0,
}
DECALAGES_PUBLIES_SUPERIEURE = {"6.03": 2.0, "6.04": 2.0, "9.01": 4.0}


def test_reproduces_the_ten_shifts_of_sia_4010():
    """The ten values from SIA 4010 §3.1.4, reconstructed from table 11.

    SIA states shifts "downward" / "upward": these are amplitudes. `usage_shift`
    returns signed quantities, hence the signs here.
    """
    for usage, amplitude in sorted(DECALAGES_PUBLIES_INFERIEURE.items()):
        inferieur, _ = sc.usage_shift(usage)
        assert inferieur == -amplitude, (
            "usage %s : SIA 4010 annonce la limite inférieure décalée de %g K "
            "vers le bas, le tableau 11 donne %g K" % (usage, amplitude, -inferieur)
        )

    for usage, amplitude in sorted(DECALAGES_PUBLIES_SUPERIEURE.items()):
        _, superieur = sc.usage_shift(usage)
        assert superieur == amplitude, (
            "usage %s : SIA 4010 annonce la limite supérieure décalée de %g K "
            "vers le haut, le tableau 11 donne %g K" % (usage, amplitude, superieur)
        )


def test_reference_group_is_unanimous_which_is_what_makes_the_shift_scalar():
    """§5.2.2.5 speaks of "the difference" with usages 1.01 to 3.03.

    This wording only makes sense if the seven usages in the group carry the
    same value. If table 11 were heterogeneous, the rule would be ambiguous and
    this module would rest on an unwritten choice.
    """
    chauffage = set(sc.DESIGN_TEMPERATURES[u][0] for u in sc.REFERENCE_USAGES)
    refroidissement = set(sc.DESIGN_TEMPERATURES[u][1] for u in sc.REFERENCE_USAGES)
    assert chauffage == {sc.REFERENCE_THETA_H}
    assert refroidissement == {sc.REFERENCE_THETA_C}


def test_usage_404_horsaal_is_not_shifted():
    """Open point O1: the setpoint for test 4 (usage 4.4 Hörsaal).

    4.04 carries 21/26 in table 11, identical to the reference group: the
    shift is zero. This is a tabulated fact, not the ~65% inference that the
    example building specification carried until now.
    """
    assert sc.usage_shift("4.04") == (0.0, 0.0)
    assert sc.limits("4.04") == (sc.LOWER_LIMIT, sc.UPPER_LIMIT)


def test_embedded_design_temperatures_match_the_frozen_table_11(sia2024):
    """The module must not be able to drift from its source."""
    lignes = sia2024["tableau_11"]["lignes"]
    assert len(lignes) == len(sc.DESIGN_TEMPERATURES) == 45
    for ligne in lignes:
        attendu = (
            (
                None
                if ligne["theta_h_design_c"] is None
                else float(ligne["theta_h_design_c"])
            ),
            (
                None
                if ligne["theta_c_design_c"] is None
                else float(ligne["theta_c_design_c"])
            ),
        )
        assert sc.DESIGN_TEMPERATURES[ligne["usage"]] == attendu, ligne["usage"]


def test_embedded_curves_match_the_frozen_figure_1(figure1):
    courbes = figure1["courbes"]
    attendu_bas = tuple(tuple(p) for p in courbes["limite_inferieure"]["sommets"])
    attendu_haut = tuple(tuple(p) for p in courbes["limite_superieure"]["sommets"])
    assert sc.LOWER_LIMIT == attendu_bas
    assert sc.UPPER_LIMIT == attendu_haut


def test_delta_theta_ctr_matches_the_measured_figure(figure1):
    ecart = figure1["ecart_de_regulation"]
    assert sc.DELTA_THETA_CTR_K == ecart["mesure_chauffage_k"]
    assert sc.DELTA_THETA_CTR_K == ecart["mesure_refroidissement_k"]


def test_variable_setpoint_curves_match_the_frozen_figure_1(figure1):
    """The variable setpoints from the module must reproduce those of the figure.

    The figure carries redundant vertices (the heating setpoint is flat at
    12 and 17.5): we therefore compare VALUES at the figure's abscissae, not
    the vertex lists.
    """
    courbes = figure1["courbes"]
    chauffage, refroidissement = sc.setpoint_curves("3.01")  # unshifted usage
    for x, y in courbes["consigne_chauffage_variable"]["sommets"]:
        assert abs(sc.evaluate(chauffage, x) - y) < 1e-9, x
    for x, y in courbes["consigne_refroidissement_variable"]["sommets"]:
        assert abs(sc.evaluate(refroidissement, x) - y) < 1e-9, x


def test_constant_setpoints_match_the_dash_dot_lines_of_the_figure(figure1):
    """22.7 and 23.8 — the two dash-dot lines of figure 1."""
    courbes = figure1["courbes"]
    chauffage, refroidissement = sc.constant_setpoints("3.01")
    assert chauffage == courbes["consigne_chauffage_constante"]["valeur_c"]
    assert refroidissement == courbes["consigne_refroidissement_constante"]["valeur_c"]
    assert (chauffage, refroidissement) == (22.7, 23.8)


def test_limits_are_also_sia_180_figure_4():
    """§5.2.2.5: limits "correspond to those of SIA 180:2014, figure 4".

    The eight values from the capture provided by the SIA on 2026-08-04.
    """
    bas, haut = sc.limits("3.01", shift=False)
    assert [y for _, y in bas] == [20.5, 20.5, 22.0, 22.0]
    assert [x for x, _ in bas] == [10.0, 19.0, 23.5, 25.0]
    assert [y for _, y in haut] == [24.5, 24.5, 26.5, 26.5]
    assert [x for x, _ in haut] == [10.0, 12.0, 17.5, 25.0]


# --------------------------------------------------------------------------
# 2. Mutation resistance
# --------------------------------------------------------------------------


def test_setpoint_is_inside_its_limit_never_outside():
    """Classic mutation: the sign of Δθctr.

    The heating setpoint is ABOVE the lower limit, the cooling one BELOW
    the upper limit. An inverted sign would widen the band instead of
    narrowing it, and would pass unnoticed on a comparison of annual means.
    """
    bas, haut = sc.limits("3.01")
    chauffage, refroidissement = sc.setpoint_curves("3.01")
    for theta_rm in (10.0, 12.0, 15.0, 19.0, 21.0, 23.5, 25.0):
        assert sc.evaluate(chauffage, theta_rm) > sc.evaluate(bas, theta_rm)
        assert sc.evaluate(refroidissement, theta_rm) < sc.evaluate(haut, theta_rm)


def test_constant_setpoints_take_the_correct_end_of_each_curve():
    """§5.2.2.3: MAXIMUM for heating, MINIMUM for cooling.

    Taking the wrong end would give 21.2 and 25.8 — values that remain
    within the band and whose error is invisible without this test.
    """
    chauffage, refroidissement = sc.constant_setpoints("3.01")
    courbe_h, courbe_c = sc.setpoint_curves("3.01")
    assert chauffage == max(y for _, y in courbe_h)
    assert refroidissement == min(y for _, y in courbe_c)
    assert chauffage != min(y for _, y in courbe_h)  # 21.2
    assert refroidissement != max(y for _, y in courbe_c)  # 25.8


def test_shift_moves_the_ordinate_and_leaves_the_abscissa_alone():
    """§5.2.2.5: "the curves shift, but keep their shape"."""
    bas_ref, haut_ref = sc.limits("3.01")
    bas, haut = sc.limits("6.03")  # kitchen: -1 K lower, +2 K upper
    assert [x for x, _ in bas] == [x for x, _ in bas_ref]
    assert [x for x, _ in haut] == [x for x, _ in haut_ref]
    assert [y for _, y in bas] == [y - 1.0 for _, y in bas_ref]
    assert [y for _, y in haut] == [y + 2.0 for _, y in haut_ref]


def test_kitchen_band_is_wider_than_the_office_band():
    """Physical sense check: the kitchen goes lower AND higher.

    A sign error on either shift would NARROW the band.
    """
    bas_bureau, haut_bureau = sc.limits("3.01")
    bas_cuisine, haut_cuisine = sc.limits("6.03")
    assert sc.evaluate(bas_cuisine, 15.0) < sc.evaluate(bas_bureau, 15.0)
    assert sc.evaluate(haut_cuisine, 15.0) > sc.evaluate(haut_bureau, 15.0)


def test_evaluate_is_exact_at_the_vertices():
    for vertices in (sc.LOWER_LIMIT, sc.UPPER_LIMIT):
        for x, y in vertices:
            assert sc.evaluate(vertices, x) == y


def test_evaluate_interpolates_linearly_on_the_sloped_segment():
    """Midpoint of the rising segment of each limit, computed by hand."""
    # lower limit: from (19; 20.5) to (23.5; 22.0), midpoint at 21.25
    assert abs(sc.evaluate(sc.LOWER_LIMIT, 21.25) - 21.25) < 1e-12
    # upper limit: from (12; 24.5) to (17.5; 26.5), midpoint at 14.75
    assert abs(sc.evaluate(sc.UPPER_LIMIT, 14.75) - 25.5) < 1e-12


def test_evaluate_clamps_outside_the_figure_domain():
    assert sc.evaluate(sc.LOWER_LIMIT, -30.0) == 20.5
    assert sc.evaluate(sc.LOWER_LIMIT, 99.0) == 22.0
    assert sc.evaluate(sc.UPPER_LIMIT, -30.0) == 24.5
    assert sc.evaluate(sc.UPPER_LIMIT, 99.0) == 26.5


def test_slopes_are_one_third_and_four_elevenths():
    """The two slopes are NOT equal — 1/3 lower, 4/11 upper.

    Assuming them equal is the natural error when reading the figure by eye;
    it would shift the upper breakpoint from 17.5 to 18.
    """
    assert abs((22.0 - 20.5) / (23.5 - 19.0) - 1.0 / 3.0) < 1e-12
    assert abs((26.5 - 24.5) / (17.5 - 12.0) - 4.0 / 11.0) < 1e-12


def test_control_class_selects_constant_or_variable():
    for classe in sc.CONTROL_CLASSES_CONSTANT:
        assert sc.setpoints("3.01", 10.0, classe) == sc.setpoints("3.01", 25.0, classe)
    for classe in sc.CONTROL_CLASSES_VARIABLE:
        assert sc.setpoints("3.01", 10.0, classe) != sc.setpoints("3.01", 25.0, classe)


def test_control_class_outside_one_to_four_is_refused():
    with pytest.raises(ValueError):
        sc.setpoints("3.01", 15.0, 0)
    with pytest.raises(ValueError):
        sc.setpoints("3.01", 15.0, 5)


def test_unknown_usage_raises_instead_of_defaulting():
    """Never a silent fallback to 21/26."""
    with pytest.raises(sc.UnknownUsage):
        sc.usage_shift("4.99")
    with pytest.raises(sc.UnknownUsage):
        sc.limits("13.01")


def test_usage_without_cooling_design_value_yields_no_cooling_curve():
    """11.01 Turnhalle: '–' for cooling in table 11."""
    inferieur, superieur = sc.usage_shift("11.01")
    assert inferieur == -3.0
    assert superieur is None
    bas, haut = sc.limits("11.01")
    assert bas is not None
    assert haut is None
    chauffage, refroidissement = sc.setpoints("11.01", 15.0, 3)
    assert chauffage is not None
    assert refroidissement is None


def test_non_seasonal_clothing_usages_have_constant_limits():
    """§5.2.2.5: the curve "takes the form of a straight line".

    The lower limit keeps its LOW value (no increase when it is hot outside),
    the upper keeps its HIGH value (no decrease when it is cold).
    """
    bas, haut = sc.limits("11.02")  # Fitnessraum, 21/26 -> zero shift
    assert len(set(y for _, y in bas)) == 1
    assert len(set(y for _, y in haut)) == 1
    assert sc.evaluate(bas, 10.0) == sc.evaluate(bas, 25.0) == 20.5
    assert sc.evaluate(haut, 10.0) == sc.evaluate(haut, 25.0) == 26.5


def test_seasonal_usages_keep_a_variable_band():
    """Mirror check of the previous: an office is NOT flattened."""
    bas, haut = sc.limits("3.01")
    assert len(set(y for _, y in bas)) > 1
    assert len(set(y for _, y in haut)) > 1


def test_within_limits_flags_both_directions():
    """At θ_rm = 15 °C, the upper limit is 24.5 + 2·(15−12)/5.5 = 25.5909…

    Writing 25.5 here would commit the slope error that
    `test_slopes_are_one_third_and_four_elevenths` forbids: 15 °C falls on the
    rising segment, with slope 4/11 not 1/3.
    """
    haut_attendu = 24.5 + 2.0 * (15.0 - 12.0) / 5.5
    inside, bas, haut = sc.within_limits("3.01", 15.0, 23.0)
    assert inside
    assert bas == 20.5
    assert abs(haut - haut_attendu) < 1e-12

    trop_chaud, _, _ = sc.within_limits("3.01", 15.0, 26.0)
    assert not trop_chaud
    trop_froid, _, _ = sc.within_limits("3.01", 15.0, 19.0)
    assert not trop_froid


def test_within_limits_is_inclusive_at_the_boundary():
    """§3.2.4.3 counts hours "exceed[ing]" the limit: the boundary passes.

    Both bounds are taken from the module itself: hard-coding a decimal would
    test the test author's rounding, not inclusivity.
    """
    _, bas, haut = sc.within_limits("3.01", 15.0, 23.0)
    for temperature in (bas, haut):
        inside, _, _ = sc.within_limits("3.01", 15.0, temperature)
        assert inside, temperature


def test_within_limits_ignores_an_undefined_limit():
    """11.01 has no upper limit: 40 °C cannot be declared out-of-band."""
    inside, bas, haut = sc.within_limits("11.01", 15.0, 40.0)
    assert inside
    assert haut is None
    assert bas == 17.5  # 20.5 - 3 K


def test_running_mean_uses_48_hours_not_24():
    serie = [0.0] * 24 + [24.0] * 24
    assert sc.running_mean_48h(serie, 47) == 12.0
    assert sc.running_mean_48h(serie, 23) == 0.0


def test_running_mean_window_slides_and_drops_the_49th_hour():
    serie = [100.0] + [0.0] * 48
    assert sc.running_mean_48h(serie, 47) == 100.0 / 48.0
    assert sc.running_mean_48h(serie, 48) == 0.0  # hour 0 has left the window


def test_running_mean_refuses_an_hour_outside_the_series():
    with pytest.raises(IndexError):
        sc.running_mean_48h([1.0, 2.0], 2)
    with pytest.raises(IndexError):
        sc.running_mean_48h([1.0, 2.0], -1)


def test_no_iesve_import():
    """Rule 4 of CLAUDE.md: engine/ is pure Python."""
    chemin = os.path.join(_RACINE, "engine", "setpoint_curves.py")
    with io.open(chemin, encoding="utf-8") as f:
        for numero, ligne in enumerate(f, 1):
            nu = ligne.strip()
            assert not nu.startswith("import iesve"), numero
            assert not nu.startswith("from iesve"), numero
