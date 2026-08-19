# -*- coding: utf-8 -*-
"""SIA 180:2014 summer-comfort limit band (figure 4) and the 48-hour running mean.

The figure-4 comfort vertices are loaded from the frozen
``refs/reference-data/sia-380-2-2022.figure1.json`` (extracted from the SIA 380/2
vector drawing, residual < 0.001 °C, and identical to SIA 180:2014 figure 4 by
the §5.2.2.5 normative identity — verified 8/8). Nothing is hard-coded or
invented here: the vertices come from that traceable source at import time.

theta_rm is the simple arithmetic mean of the outdoor dry-bulb temperature over
the last 48 hours (oracle report §3.1). ``[À VÉRIFIER]`` against SIA 180:2014
directly, and PENDING norm-analyst: the operative-temperature definition SIA 180
compares (air / operative / dry-resultant), the exact theta_rm window
convention, and figure 3 (Anhang C1) are not settled here. This module
implements the VERIFIED figure-4 band only, over the plotted domain theta_rm
10..25 °C (clamped flat outside it, as the end segments are horizontal plateaus).

Pure Python, no ``iesve`` import.
"""

from __future__ import annotations

import io
import json
import os
from typing import List, Optional, Sequence, Tuple

WINDOW_HOURS = 48

_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
)
_FIGURE1_PATH = os.path.join(
    _ROOT, "refs", "reference-data", "sia-380-2-2022.figure1.json"
)
SOURCE_LOCATOR = (
    "SIA 180:2014 figure 4 (via SIA 380/2:2022 figure 1, §5.2.2.5) | "
    "refs/reference-data/sia-380-2-2022.figure1.json"
)


def _load_vertices() -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """Load the verified figure-4 upper/lower vertices from the frozen source."""
    with io.open(_FIGURE1_PATH, encoding="utf-8") as handle:
        data = json.load(handle)
    curves = data["courbes"]
    upper = [(float(x), float(y)) for x, y in curves["limite_superieure"]["sommets"]]
    lower = [(float(x), float(y)) for x, y in curves["limite_inferieure"]["sommets"]]
    if not upper or not lower:
        raise RuntimeError("SIA 180 figure-4 vertices missing from the frozen source")
    return upper, lower


_UPPER_VERTICES, _LOWER_VERTICES = _load_vertices()
DOMAIN = (_UPPER_VERTICES[0][0], _UPPER_VERTICES[-1][0])


def _piecewise_linear(vertices: Sequence[Tuple[float, float]], x: float) -> float:
    """Piecewise-linear interpolation, clamped flat outside the plotted domain."""
    if x <= vertices[0][0]:
        return vertices[0][1]
    if x >= vertices[-1][0]:
        return vertices[-1][1]
    for (x0, y0), (x1, y1) in zip(vertices, vertices[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return vertices[-1][1]


def upper_limit(theta_rm: float) -> float:
    """SIA 180 figure-4 UPPER operative-temperature limit for a running mean."""
    return _piecewise_linear(_UPPER_VERTICES, float(theta_rm))


def lower_limit(theta_rm: float) -> float:
    """SIA 180 figure-4 LOWER operative-temperature limit for a running mean."""
    return _piecewise_linear(_LOWER_VERTICES, float(theta_rm))


def rolling_mean(
    exterior: Sequence[Optional[float]], results_per_hour: float
) -> List[Optional[float]]:
    """Return theta_rm per timestep: 48-hour simple mean of the outdoor series.

    ``exterior[i]`` is the outdoor dry-bulb temperature (°C) at timestep ``i`` or
    ``None`` when absent. The averaging window is ``48 * results_per_hour``
    timesteps ending at ``i`` (current step included). Steps with no usable value
    in the window return ``None``.
    """
    rph = int(round(results_per_hour)) if results_per_hour and results_per_hour > 0 else 1
    window = max(1, WINDOW_HOURS * rph)
    out: List[Optional[float]] = []
    for index in range(len(exterior)):
        low = max(0, index - window + 1)
        values = [value for value in exterior[low:index + 1] if value is not None]
        out.append(sum(values) / len(values) if values else None)
    return out


def comfort_limit_series(
    exterior: Sequence[Optional[float]], results_per_hour: float
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """Return per-timestep (upper, lower) SIA 180 limits from the outdoor series.

    ``None`` where theta_rm cannot be computed for that step, so the caller keeps
    a fail-closed alignment with the room temperature/occupancy series.
    """
    theta_rm = rolling_mean(exterior, results_per_hour)
    upper = [None if value is None else upper_limit(value) for value in theta_rm]
    lower = [None if value is None else lower_limit(value) for value in theta_rm]
    return upper, lower
