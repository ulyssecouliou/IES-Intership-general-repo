# -*- coding: utf-8 -*-
"""Room setpoint and comfort-limit curves of SIA 380/2:2022, figure 1.

WHAT THIS IS. Figure 1 of SIA 380/2:2022 (printed page 27) carries four
piecewise-linear curves against the 48-hour running mean of outdoor
temperature: an upper and a lower comfort limit, and a heating and a cooling
setpoint. This module evaluates them, shifts them per space usage, and answers
the one question the engine needs: what setpoint applies to this usage, at this
outdoor running mean, under this emission-control class.

WHERE THE NUMBERS COME FROM -- extracted, not read by eye. Figure 1 is a VECTOR
drawing in `refs/SIA-380-2-2022.pdf`, so its vertices are in the file exactly.
`scripts/extract_sia380_2_figure1.py` recovers them after calibrating on the
frame's gridlines (not on the text labels, which sit ~0.8 pt off), with a
residual below 0.001 degC. Frozen in
`refs/reference-data/sia-380-2-2022.figure1.json`.

    lower limit        20.5 degC up to theta_rm = 19, rising to 22.0 at 23.5
    upper limit        24.5 degC up to theta_rm = 12, rising to 26.5 at 17.5
    heating setpoint   lower limit + 0.7 K   (21.2 -> 22.7)
    cooling setpoint   upper limit - 0.7 K   (23.8 -> 25.8)

CROSS-CHECK, two independent documents. SIA 380/2 §5.2.2.5 states the limits
"correspondent a celles de SIA 180:2014, figure 4, pour les locaux d'habitation
et les bureaux". The SIA supplied that figure on 2026-08-04; all eight values
agree -- ordinates 20.5 / 22.0 / 24.5 / 26.5, abscissa breaks 12 / 17.5 / 19 /
23.5. See `refs/reference-data/sia-180-2014.comfort.json`.

WHICH CURVE APPLIES -- SIA 380/2 §5.2.2.3, on the emission-control class of
SN EN ISO 52120-1:2022 table 5:
  - class 1 or 2 (no communication), or the user can influence the room:
        CONSTANT setpoints, at "le maximum de la courbe de la valeur de consigne
        pour le chauffage" (22.7) and "le minimum de la courbe [...] pour le
        refroidissement" (23.8). Drawn dash-dot in the figure.
  - class 3 or 4 (with communication) and no user influence:
        the VARIABLE curves. Drawn dotted.

USAGE SHIFT -- SIA 380/2 §5.2.2.5: "Sans determination plus detaillee des
conditions de confort, les limites seront decalees suivant la difference entre
les valeurs de dimensionnement de l'utilisation correspondante et les
utilisations 1.01 a 3.03 selon SIA 2024:2021, tableau 11." Usages 1.01 to 3.03
are unanimous at 21 degC / 26 degC in table 11, which is what makes that
"difference" a scalar. Hence:

    lower shift = theta_h_design(usage) - 21     upper shift = theta_c_design(usage) - 26

"Pour d'autres utilisations, les courbes se deplacent, mais gardent leur forme."
The shift is applied to the ordinate only; abscissa breaks are untouched.

THE RULE IS VERIFIED, NOT ASSUMED. SIA 4010:2023 §3.1.4 (printed page 10)
enumerates shifts for seven usages -- ten values across the two curves. All ten
are reproduced from table 11 by the formula above; see
`engine/tests/test_setpoint_curves.py`. That single check validates both our
transcription of table 11 and our reading of §5.2.2.5.

WHAT THIS MODULE DOES NOT DECIDE. §5.2.2.1: "Les valeurs de consigne peuvent
etre fixees pour la temperature moyenne de l'air interieur OU pour la
temperature operative simplifiee. Le choix est a discuter avec le mandant."
The curves are identical either way; only the simulated quantity they are
compared against changes. That choice belongs to the caller.

Pure Python, no dependencies, no `import iesve`: testable in CI without a VE
licence and runnable as-is inside VEScripts.
"""


# --------------------------------------------------------------------------
# Figure 1 of SIA 380/2:2022, page 27. Vertices as (theta_rm, temperature) in
# degC, extracted from the vector drawing (residual < 0.001 degC).
#
# The figure is DEFINED on theta_rm in [10, 25]. Both curves are flat on their
# first and last segment, so clamping outside that interval extends a value the
# figure already draws rather than inventing one -- but the figure does not
# formally cover it. See `evaluate()`.
# --------------------------------------------------------------------------
LOWER_LIMIT = ((10.0, 20.5), (19.0, 20.5), (23.5, 22.0), (25.0, 22.0))
UPPER_LIMIT = ((10.0, 24.5), (12.0, 24.5), (17.5, 26.5), (25.0, 26.5))

# Emission-control deviation, SIA 380/2 §5.2.2.2: the gap between a setpoint and
# its limit "correspond a l'ecart de regulation pour l'emission de chaleur et de
# froid delta_theta_ctr selon SN EN 15316-2:2017".
#
# 0.7 K is what figure 1 DRAWS, measured on both sides. SN EN 15316-2:2017 --
# which defines the quantity -- is not in our possession, so we cannot tell
# whether 0.7 K is the general prescription or an illustration for one control
# class. # -- A VERIFIER
DELTA_THETA_CTR_K = 0.7

# Reference usage group of §5.2.2.5, and its table 11 design values. Unanimity
# across the seven usages is asserted by the tests, not assumed here.
REFERENCE_USAGES = ('1.01', '1.02', '2.01', '2.02', '3.01', '3.02', '3.03')
REFERENCE_THETA_H = 21.0
REFERENCE_THETA_C = 26.0

# Design room temperatures of SIA 2024:2021 table 11, columns "Heizfall" and
# "Kuehlfall". Embedded so this module runs standalone inside VEScripts; the
# tests assert identity with `refs/reference-data/sia-2024-2021.tables.json`,
# which is the frozen source. `None` = "-" (nicht relevant) in the table.
DESIGN_TEMPERATURES = {
    '1.01': (21.0, 26.0), '1.02': (21.0, 26.0), '2.01': (21.0, 26.0),
    '2.02': (21.0, 26.0), '3.01': (21.0, 26.0), '3.02': (21.0, 26.0),
    '3.03': (21.0, 26.0), '3.04': (20.0, 26.0), '4.01': (21.0, 26.0),
    '4.02': (21.0, 26.0), '4.03': (21.0, 26.0), '4.04': (21.0, 26.0),
    '4.05': (21.0, 26.0), '5.01': (20.0, 26.0), '5.02': (20.0, 26.0),
    '5.03': (20.0, 26.0), '6.01': (21.0, 26.0), '6.02': (21.0, 26.0),
    '6.03': (20.0, 28.0), '6.04': (20.0, 28.0), '7.01': (21.0, 26.0),
    '7.02': (21.0, 26.0), '7.03': (21.0, 26.0), '8.01': (22.0, 26.0),
    '8.02': (21.0, 26.0), '8.03': (22.0, 26.0), '9.01': (18.0, 30.0),
    '9.02': (21.0, 26.0), '9.03': (21.0, 26.0), '10.01': (18.0, None),
    '11.01': (18.0, None), '11.02': (21.0, 26.0), '11.03': (24.0, None),
    '12.01': (21.0, None), '12.02': (21.0, 26.0), '12.03': (18.0, None),
    '12.04': (18.0, None), '12.05': (21.0, None), '12.06': (21.0, None),
    '12.07': (21.0, None), '12.08': (21.0, None), '12.09': (None, None),
    '12.10': (None, None), '12.11': (None, None), '12.12': (None, 26.0),
}

# Usages for which seasonal clothing does not apply, so the limits are constant
# -- SIA 380/2 §5.2.2.5: "salles de gymnastique, salles de fitness, piscines
# couvertes, vestiaires, douches [...] valeurs limites superieures (pas de
# diminution lorsque les temperatures exterieures sont basses) et valeurs
# limites inferieures (pas d'augmentation lorsque les temperatures exterieures
# sont elevees) constantes". SIA 4010 §3.1.4: the curve "prend la forme d'une
# ligne droite".
#
# # -- A VERIFIER: the standards name the LABELS, not the usage numbers. Mapping
# them onto SIA 2024 numbers is our reading. "12.06 WC, Bad, Dusche" arguably
# also falls under "douches" and is deliberately NOT included: including it
# would silently change results for a usage the standard does not clearly name.
CONSTANT_LIMIT_USAGES = ('11.01', '11.02', '11.03', '12.08')

CONTROL_CLASSES_CONSTANT = (1, 2)
CONTROL_CLASSES_VARIABLE = (3, 4)


class UnknownUsage(KeyError):
    """Raised for a usage absent from SIA 2024:2021 table 11.

    Deliberately an error and never a default: silently falling back to 21/26
    would produce a plausible number with no normative basis.
    """


class UsageNotConditioned(ValueError):
    """Raised when table 11 gives no design value for the requested mode.

    Example: usage 11.01 Turnhalle has "-" in the cooling column. There is no
    cooling setpoint to shift, so no cooling curve can be built.
    """


def evaluate(vertices, theta_rm):
    """Piecewise-linear value of a curve at `theta_rm`, in degC.

    Outside the figure's domain the value is CLAMPED to the end vertex. Both
    curves are flat on their first and last segment, so this extends a value the
    figure already draws. It remains an extrapolation of the figure's scope.
    """
    if theta_rm <= vertices[0][0]:
        return vertices[0][1]
    if theta_rm >= vertices[-1][0]:
        return vertices[-1][1]
    for (x0, y0), (x1, y1) in zip(vertices, vertices[1:]):
        if x0 <= theta_rm <= x1:
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (theta_rm - x0) / (x1 - x0)
    raise AssertionError('theta_rm %r fell through the segments' % (theta_rm,))


def usage_shift(usage):
    """Ordinate shift of the two limit curves for `usage`, in K.

    Returns `(lower_shift, upper_shift)`, either of which may be `None` when
    table 11 gives no design value for that mode.

    SIA 380/2 §5.2.2.5. Verified against the ten values of SIA 4010 §3.1.4.
    """
    try:
        theta_h, theta_c = DESIGN_TEMPERATURES[usage]
    except KeyError:
        raise UnknownUsage(
            'usage %r absent from SIA 2024:2021 table 11' % (usage,))
    lower = None if theta_h is None else theta_h - REFERENCE_THETA_H
    upper = None if theta_c is None else theta_c - REFERENCE_THETA_C
    return lower, upper


def _shifted(vertices, shift):
    return tuple((x, y + shift) for x, y in vertices)


def _flattened(vertices, keep):
    """Collapse a curve to a constant, for the non-seasonal-clothing usages.

    `keep` is `min` for the lower limit ("pas d'augmentation lorsque les
    temperatures exterieures sont elevees") and `max` for the upper limit ("pas
    de diminution lorsque les temperatures exterieures sont basses").
    """
    value = keep(y for _, y in vertices)
    return tuple((x, value) for x, y in vertices)


def limits(usage, shift=True):
    """The two comfort limits for `usage`, as vertex tuples.

    `shift=False` returns the unshifted curves of figure 1, i.e. the limits for
    dwellings and offices, which are also SIA 180:2014 figure 4.
    """
    lower, upper = LOWER_LIMIT, UPPER_LIMIT

    if usage in CONSTANT_LIMIT_USAGES:
        lower = _flattened(lower, min)
        upper = _flattened(upper, max)

    if not shift:
        return lower, upper

    lower_shift, upper_shift = usage_shift(usage)
    lower = None if lower_shift is None else _shifted(lower, lower_shift)
    upper = None if upper_shift is None else _shifted(upper, upper_shift)
    return lower, upper


def setpoint_curves(usage, shift=True):
    """The heating and cooling setpoint curves for `usage`.

    Each is its limit offset inward by `DELTA_THETA_CTR_K` -- SIA 380/2 §5.2.2.2.
    """
    lower, upper = limits(usage, shift=shift)
    heating = None if lower is None else _shifted(lower, DELTA_THETA_CTR_K)
    cooling = None if upper is None else _shifted(upper, -DELTA_THETA_CTR_K)
    return heating, cooling


def constant_setpoints(usage, shift=True):
    """The two constant setpoints, for emission-control class 1 or 2.

    SIA 380/2 §5.2.2.3: "valeurs constantes au MAXIMUM de la courbe de la valeur
    de consigne pour le chauffage ou au MINIMUM de la courbe de la valeur de
    consigne pour le refroidissement". Unshifted, that is 22.7 and 23.8 -- the
    dash-dot lines drawn in figure 1.
    """
    heating, cooling = setpoint_curves(usage, shift=shift)
    return (None if heating is None else max(y for _, y in heating),
            None if cooling is None else min(y for _, y in cooling))


def setpoints(usage, theta_rm, control_class, shift=True):
    """Heating and cooling setpoints in degC, for the applicable control class.

    `control_class` is HEAT_EMIS_CTRL_DEF / CLG_EMIS_CTRL_DEF of
    SN EN ISO 52120-1:2022 table 5, assumed equal for both. Classes 1 and 2 give
    constant setpoints, 3 and 4 the variable curves -- SIA 380/2 §5.2.2.3.

    `theta_rm` is the 48-hour running mean of outdoor temperature, in degC. It is
    ignored for classes 1 and 2, by construction rather than by oversight.

    # -- A VERIFIER: which class an IESVE control corresponds to. Table 5 of
    # SN EN ISO 52120-1:2022 is not in our possession, so the caller must supply
    # the class; this module will not guess it.
    """
    if control_class in CONTROL_CLASSES_CONSTANT:
        return constant_setpoints(usage, shift=shift)
    if control_class in CONTROL_CLASSES_VARIABLE:
        heating, cooling = setpoint_curves(usage, shift=shift)
        return (None if heating is None else evaluate(heating, theta_rm),
                None if cooling is None else evaluate(cooling, theta_rm))
    raise ValueError(
        'emission-control class %r outside 1..4 of SN EN ISO 52120-1:2022 '
        'table 5' % (control_class,))


def within_limits(usage, theta_rm, temperature):
    """Is `temperature` inside the comfort band for `usage` at `theta_rm`?

    Returns `(inside, lower, upper)`. A limit that table 11 does not define is
    returned as `None` and is not tested against.

    Used by the SIA 380/2 §3.2.4 overheating check, which counts the hours above
    the upper limit during occupancy (>100 h/a: cooling necessary; <=100 h/a:
    desirable; 0 h: unnecessary -- §3.2.4.3), and by §3.2.4.4, which forbids
    dropping below the lower limit at any occupied hour.
    """
    lower_curve, upper_curve = limits(usage, shift=True)
    lower = None if lower_curve is None else evaluate(lower_curve, theta_rm)
    upper = None if upper_curve is None else evaluate(upper_curve, theta_rm)
    if lower is not None and temperature < lower:
        return False, lower, upper
    if upper is not None and temperature > upper:
        return False, lower, upper
    return True, lower, upper


def running_mean_48h(hourly_outdoor, index):
    """48-hour running mean of outdoor temperature ending at `index`, in degC.

    The abscissa of figure 1 is "Temperature exterieure moyenne glissante sur
    48 heures". The standard does not say how the first 47 hours of a run are
    handled; averaging over what is available is our choice, and it is the only
    hour range where the abscissa is ambiguous.

    # -- A VERIFIER against SN EN 16798-1 / SIA 180, which may define a weighted
    # running mean rather than a flat 48-hour window.
    """
    if index < 0 or index >= len(hourly_outdoor):
        raise IndexError('hour %r outside the series' % (index,))
    start = max(0, index - 47)
    window = hourly_outdoor[start:index + 1]
    return sum(window) / float(len(window))
