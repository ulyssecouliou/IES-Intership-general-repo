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
_REFS = os.path.join(_RACINE, 'refs', 'reference-data')


def _charger(nom):
    chemin = os.path.join(_REFS, nom)
    if not os.path.exists(chemin):
        pytest.skip(u'référentiel absent : %s' % nom)
    with io.open(chemin, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope='module')
def figure1():
    return _charger('sia-380-2-2022.figure1.json')


@pytest.fixture(scope='module')
def sia2024():
    return _charger('sia-2024-2021.tables.json')


# --------------------------------------------------------------------------
# 1. Reproduction des références publiées
# --------------------------------------------------------------------------

# SIA 4010:2023 §3.1.4, p. 10 — « une courbe limite inférieure et donc une
# courbe de point de réglage décalée de 1 K pour les utilisations 3.04 salle de
# guichets, 5.01 à 5.03 (magasins de vente) et 6.03 et 6.04 (cuisines), et de
# 3 K pour l'utilisation 9.01 production (travail grossier). Un déplacement de
# la courbe de point de réglage supérieure vers le haut se produit pour les
# utilisations 6.03 et 6.04 (cuisines) de 2 K, pour l'utilisation 9.01 de 4 K. »
DECALAGES_PUBLIES_INFERIEURE = {
    '3.04': 1.0, '5.01': 1.0, '5.02': 1.0, '5.03': 1.0,
    '6.03': 1.0, '6.04': 1.0, '9.01': 3.0,
}
DECALAGES_PUBLIES_SUPERIEURE = {'6.03': 2.0, '6.04': 2.0, '9.01': 4.0}


def test_reproduces_the_ten_shifts_of_sia_4010():
    """Les dix valeurs de SIA 4010 §3.1.4, reconstruites depuis le tableau 11.

    Le SIA énonce des décalages « vers le bas » / « vers le haut » : ce sont des
    amplitudes. `usage_shift` renvoie des grandeurs signées, d'où les signes ici.
    """
    for usage, amplitude in sorted(DECALAGES_PUBLIES_INFERIEURE.items()):
        inferieur, _ = sc.usage_shift(usage)
        assert inferieur == -amplitude, (
            u'usage %s : SIA 4010 annonce la limite inférieure décalée de %g K '
            u'vers le bas, le tableau 11 donne %g K' % (usage, amplitude, -inferieur))

    for usage, amplitude in sorted(DECALAGES_PUBLIES_SUPERIEURE.items()):
        _, superieur = sc.usage_shift(usage)
        assert superieur == amplitude, (
            u'usage %s : SIA 4010 annonce la limite supérieure décalée de %g K '
            u'vers le haut, le tableau 11 donne %g K' % (usage, amplitude, superieur))


def test_reference_group_is_unanimous_which_is_what_makes_the_shift_scalar():
    """§5.2.2.5 parle de « la différence » avec les usages 1.01 à 3.03.

    Cette formulation n'a de sens que si les sept usages du groupe portent la
    même valeur. Si le tableau 11 était hétérogène, la règle serait ambiguë et
    ce module reposerait sur un choix non écrit.
    """
    chauffage = set(sc.DESIGN_TEMPERATURES[u][0] for u in sc.REFERENCE_USAGES)
    refroidissement = set(sc.DESIGN_TEMPERATURES[u][1] for u in sc.REFERENCE_USAGES)
    assert chauffage == {sc.REFERENCE_THETA_H}
    assert refroidissement == {sc.REFERENCE_THETA_C}


def test_usage_404_horsaal_is_not_shifted():
    """Point ouvert O1 : la consigne du test 4 (usage 4.4 Hörsaal).

    4.04 porte 21/26 au tableau 11, identiques au groupe de référence : le
    décalage est nul. C'est un fait tabulé, pas l'inférence à ~65 % que la
    spécification du bâtiment exemple portait jusqu'ici.
    """
    assert sc.usage_shift('4.04') == (0.0, 0.0)
    assert sc.limits('4.04') == (sc.LOWER_LIMIT, sc.UPPER_LIMIT)


def test_embedded_design_temperatures_match_the_frozen_table_11(sia2024):
    """Le module ne doit pas pouvoir dériver de sa source."""
    lignes = sia2024['tableau_11']['lignes']
    assert len(lignes) == len(sc.DESIGN_TEMPERATURES) == 45
    for ligne in lignes:
        attendu = (
            None if ligne['theta_h_design_c'] is None else float(ligne['theta_h_design_c']),
            None if ligne['theta_c_design_c'] is None else float(ligne['theta_c_design_c']),
        )
        assert sc.DESIGN_TEMPERATURES[ligne['usage']] == attendu, ligne['usage']


def test_embedded_curves_match_the_frozen_figure_1(figure1):
    courbes = figure1['courbes']
    attendu_bas = tuple(tuple(p) for p in courbes['limite_inferieure']['sommets'])
    attendu_haut = tuple(tuple(p) for p in courbes['limite_superieure']['sommets'])
    assert sc.LOWER_LIMIT == attendu_bas
    assert sc.UPPER_LIMIT == attendu_haut


def test_delta_theta_ctr_matches_the_measured_figure(figure1):
    ecart = figure1['ecart_de_regulation']
    assert sc.DELTA_THETA_CTR_K == ecart['mesure_chauffage_k']
    assert sc.DELTA_THETA_CTR_K == ecart['mesure_refroidissement_k']


def test_variable_setpoint_curves_match_the_frozen_figure_1(figure1):
    """Les consignes variables du module doivent redonner celles de la figure.

    La figure porte des sommets redondants (la consigne chauffage est plate en
    12 et 17,5) : on compare donc les VALEURS aux abscisses de la figure, pas les
    listes de sommets.
    """
    courbes = figure1['courbes']
    chauffage, refroidissement = sc.setpoint_curves('3.01')  # usage non décalé
    for x, y in courbes['consigne_chauffage_variable']['sommets']:
        assert abs(sc.evaluate(chauffage, x) - y) < 1e-9, x
    for x, y in courbes['consigne_refroidissement_variable']['sommets']:
        assert abs(sc.evaluate(refroidissement, x) - y) < 1e-9, x


def test_constant_setpoints_match_the_dash_dot_lines_of_the_figure(figure1):
    """22,7 et 23,8 — les deux traits mixtes de la figure 1."""
    courbes = figure1['courbes']
    chauffage, refroidissement = sc.constant_setpoints('3.01')
    assert chauffage == courbes['consigne_chauffage_constante']['valeur_c']
    assert refroidissement == courbes['consigne_refroidissement_constante']['valeur_c']
    assert (chauffage, refroidissement) == (22.7, 23.8)


def test_limits_are_also_sia_180_figure_4():
    """§5.2.2.5 : les limites « correspondent à celles de SIA 180:2014, figure 4 ».

    Les huit valeurs de la capture fournie par le SIA le 2026-08-04.
    """
    bas, haut = sc.limits('3.01', shift=False)
    assert [y for _, y in bas] == [20.5, 20.5, 22.0, 22.0]
    assert [x for x, _ in bas] == [10.0, 19.0, 23.5, 25.0]
    assert [y for _, y in haut] == [24.5, 24.5, 26.5, 26.5]
    assert [x for x, _ in haut] == [10.0, 12.0, 17.5, 25.0]


# --------------------------------------------------------------------------
# 2. Résistance à la mutation
# --------------------------------------------------------------------------

def test_setpoint_is_inside_its_limit_never_outside():
    """Mutation classique : le signe de Δθctr.

    La consigne de chauffage est AU-DESSUS de la limite inférieure, celle de
    refroidissement EN DESSOUS de la limite supérieure. Un signe inversé
    élargirait la bande au lieu de la resserrer, et passerait inaperçu sur une
    comparaison de moyennes annuelles.
    """
    bas, haut = sc.limits('3.01')
    chauffage, refroidissement = sc.setpoint_curves('3.01')
    for theta_rm in (10.0, 12.0, 15.0, 19.0, 21.0, 23.5, 25.0):
        assert sc.evaluate(chauffage, theta_rm) > sc.evaluate(bas, theta_rm)
        assert sc.evaluate(refroidissement, theta_rm) < sc.evaluate(haut, theta_rm)


def test_constant_setpoints_take_the_correct_end_of_each_curve():
    """§5.2.2.3 : MAXIMUM en chauffage, MINIMUM en refroidissement.

    Prendre le mauvais bout donnerait 21,2 et 25,8 — des valeurs qui restent
    dans la bande et dont l'erreur ne se voit pas sans ce test.
    """
    chauffage, refroidissement = sc.constant_setpoints('3.01')
    courbe_h, courbe_c = sc.setpoint_curves('3.01')
    assert chauffage == max(y for _, y in courbe_h)
    assert refroidissement == min(y for _, y in courbe_c)
    assert chauffage != min(y for _, y in courbe_h)      # 21,2
    assert refroidissement != max(y for _, y in courbe_c)  # 25,8


def test_shift_moves_the_ordinate_and_leaves_the_abscissa_alone():
    """§5.2.2.5 : « les courbes se déplacent, mais gardent leur forme »."""
    bas_ref, haut_ref = sc.limits('3.01')
    bas, haut = sc.limits('6.03')  # cuisine : -1 K en bas, +2 K en haut
    assert [x for x, _ in bas] == [x for x, _ in bas_ref]
    assert [x for x, _ in haut] == [x for x, _ in haut_ref]
    assert [y for _, y in bas] == [y - 1.0 for _, y in bas_ref]
    assert [y for _, y in haut] == [y + 2.0 for _, y in haut_ref]


def test_kitchen_band_is_wider_than_the_office_band():
    """Contrôle de sens physique : la cuisine descend plus bas ET monte plus haut.

    Une erreur de signe sur l'un des deux décalages RÉTRÉCIRAIT la bande.
    """
    bas_bureau, haut_bureau = sc.limits('3.01')
    bas_cuisine, haut_cuisine = sc.limits('6.03')
    assert sc.evaluate(bas_cuisine, 15.0) < sc.evaluate(bas_bureau, 15.0)
    assert sc.evaluate(haut_cuisine, 15.0) > sc.evaluate(haut_bureau, 15.0)


def test_evaluate_is_exact_at_the_vertices():
    for vertices in (sc.LOWER_LIMIT, sc.UPPER_LIMIT):
        for x, y in vertices:
            assert sc.evaluate(vertices, x) == y


def test_evaluate_interpolates_linearly_on_the_sloped_segment():
    """Milieu du segment croissant de chaque limite, calculé à la main."""
    # limite inférieure : de (19 ; 20,5) à (23,5 ; 22,0), milieu en 21,25
    assert abs(sc.evaluate(sc.LOWER_LIMIT, 21.25) - 21.25) < 1e-12
    # limite supérieure : de (12 ; 24,5) à (17,5 ; 26,5), milieu en 14,75
    assert abs(sc.evaluate(sc.UPPER_LIMIT, 14.75) - 25.5) < 1e-12


def test_evaluate_clamps_outside_the_figure_domain():
    assert sc.evaluate(sc.LOWER_LIMIT, -30.0) == 20.5
    assert sc.evaluate(sc.LOWER_LIMIT, 99.0) == 22.0
    assert sc.evaluate(sc.UPPER_LIMIT, -30.0) == 24.5
    assert sc.evaluate(sc.UPPER_LIMIT, 99.0) == 26.5


def test_slopes_are_one_third_and_four_elevenths():
    """Les deux pentes ne sont PAS égales — 1/3 en bas, 4/11 en haut.

    Les supposer égales est l'erreur naturelle en lisant la figure à l'œil ;
    elle décalerait le point de rupture supérieur de 17,5 à 18.
    """
    assert abs((22.0 - 20.5) / (23.5 - 19.0) - 1.0 / 3.0) < 1e-12
    assert abs((26.5 - 24.5) / (17.5 - 12.0) - 4.0 / 11.0) < 1e-12


def test_control_class_selects_constant_or_variable():
    for classe in sc.CONTROL_CLASSES_CONSTANT:
        assert sc.setpoints('3.01', 10.0, classe) == sc.setpoints('3.01', 25.0, classe)
    for classe in sc.CONTROL_CLASSES_VARIABLE:
        assert sc.setpoints('3.01', 10.0, classe) != sc.setpoints('3.01', 25.0, classe)


def test_control_class_outside_one_to_four_is_refused():
    with pytest.raises(ValueError):
        sc.setpoints('3.01', 15.0, 0)
    with pytest.raises(ValueError):
        sc.setpoints('3.01', 15.0, 5)


def test_unknown_usage_raises_instead_of_defaulting():
    """Jamais de repli silencieux sur 21/26."""
    with pytest.raises(sc.UnknownUsage):
        sc.usage_shift('4.99')
    with pytest.raises(sc.UnknownUsage):
        sc.limits('13.01')


def test_usage_without_cooling_design_value_yields_no_cooling_curve():
    """11.01 Turnhalle : « – » en refroidissement au tableau 11."""
    inferieur, superieur = sc.usage_shift('11.01')
    assert inferieur == -3.0
    assert superieur is None
    bas, haut = sc.limits('11.01')
    assert bas is not None
    assert haut is None
    chauffage, refroidissement = sc.setpoints('11.01', 15.0, 3)
    assert chauffage is not None
    assert refroidissement is None


def test_non_seasonal_clothing_usages_have_constant_limits():
    """§5.2.2.5 : la courbe « prend la forme d'une ligne droite ».

    La limite inférieure garde sa valeur BASSE (pas d'augmentation quand il fait
    chaud dehors), la supérieure sa valeur HAUTE (pas de diminution quand il
    fait froid).
    """
    bas, haut = sc.limits('11.02')  # Fitnessraum, 21/26 -> décalage nul
    assert len(set(y for _, y in bas)) == 1
    assert len(set(y for _, y in haut)) == 1
    assert sc.evaluate(bas, 10.0) == sc.evaluate(bas, 25.0) == 20.5
    assert sc.evaluate(haut, 10.0) == sc.evaluate(haut, 25.0) == 26.5


def test_seasonal_usages_keep_a_variable_band():
    """Contrôle miroir du précédent : un bureau n'est PAS aplati."""
    bas, haut = sc.limits('3.01')
    assert len(set(y for _, y in bas)) > 1
    assert len(set(y for _, y in haut)) > 1


def test_within_limits_flags_both_directions():
    """À θ_rm = 15 °C, la limite haute vaut 24,5 + 2·(15−12)/5,5 = 25,5909…

    Écrire 25,5 ici serait commettre l'erreur de pente que
    `test_slopes_are_one_third_and_four_elevenths` interdit : 15 °C tombe sur le
    segment croissant, de pente 4/11 et non 1/3.
    """
    haut_attendu = 24.5 + 2.0 * (15.0 - 12.0) / 5.5
    inside, bas, haut = sc.within_limits('3.01', 15.0, 23.0)
    assert inside
    assert bas == 20.5
    assert abs(haut - haut_attendu) < 1e-12

    trop_chaud, _, _ = sc.within_limits('3.01', 15.0, 26.0)
    assert not trop_chaud
    trop_froid, _, _ = sc.within_limits('3.01', 15.0, 19.0)
    assert not trop_froid


def test_within_limits_is_inclusive_at_the_boundary():
    """§3.2.4.3 compte les heures « dépass[ant] » la limite : le bord passe.

    Les deux bornes sont prises du module lui-même : coder une décimale en dur
    testerait l'arrondi de l'auteur du test, pas l'inclusivité.
    """
    _, bas, haut = sc.within_limits('3.01', 15.0, 23.0)
    for temperature in (bas, haut):
        inside, _, _ = sc.within_limits('3.01', 15.0, temperature)
        assert inside, temperature


def test_within_limits_ignores_an_undefined_limit():
    """11.01 n'a pas de limite haute : 40 °C ne peut pas être déclaré hors bande."""
    inside, bas, haut = sc.within_limits('11.01', 15.0, 40.0)
    assert inside
    assert haut is None
    assert bas == 17.5  # 20,5 - 3 K


def test_running_mean_uses_48_hours_not_24():
    serie = [0.0] * 24 + [24.0] * 24
    assert sc.running_mean_48h(serie, 47) == 12.0
    assert sc.running_mean_48h(serie, 23) == 0.0


def test_running_mean_window_slides_and_drops_the_49th_hour():
    serie = [100.0] + [0.0] * 48
    assert sc.running_mean_48h(serie, 47) == 100.0 / 48.0
    assert sc.running_mean_48h(serie, 48) == 0.0  # l'heure 0 est sortie


def test_running_mean_refuses_an_hour_outside_the_series():
    with pytest.raises(IndexError):
        sc.running_mean_48h([1.0, 2.0], 2)
    with pytest.raises(IndexError):
        sc.running_mean_48h([1.0, 2.0], -1)


def test_no_iesve_import():
    """Règle 4 de CLAUDE.md : engine/ est du Python pur."""
    chemin = os.path.join(_RACINE, 'engine', 'setpoint_curves.py')
    with io.open(chemin, encoding='utf-8') as f:
        for numero, ligne in enumerate(f, 1):
            nu = ligne.strip()
            assert not nu.startswith('import iesve'), numero
            assert not nu.startswith('from iesve'), numero
