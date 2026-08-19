"""Courbes de confort SIA 180:2014 — Fig.3 et Fig.4.

Fonctions PURES donnant, pour une moyenne glissante extérieure ``theta_rm``
(°C), les limites supérieure/inférieure de température opérative (empfundene
Temperatur, °C).

DOCTRINE : aucune constante n'est ici « inventée ». Provenance de chaque jeu :

* **Fig.3 SIA 180** (Anhang C1, baulische Grundanforderungen) — équations
  IMPRIMÉES comme étiquettes sur la figure du rapport-oracle
  ``32_ZOER_Simulationsbericht_20251208`` §3.2 (Abbildung 3 « Fig.3 SIA 180 ») :
  courbe supérieure ``0,33·θrm + 21,8`` avec un plateau lu à 25 °C, courbe
  inférieure ``0,33·θrm + 14,3``. Ce sont les courbes que le rapport DÉCLARE
  utiliser ; ce sont donc la cible de réplication de la fixture.
  ``[À VÉRIFIER]`` : confrontation directe à SIA 180:2014, Figure 3 publiée
  (plateau haut exact, domaine de validité de θrm, éventuel plateau bas). La
  page correspondante de SIA 180:2014 n'est pas en notre possession.

* **Fig.4 SIA 180** (Anhang C2, obere/untere Behaglichkeitsgrenze) — courbe
  linéaire par morceaux, sommets FIGÉS, extraits du dessin vectoriel de
  SIA 380/2:2022 figure 1 (résidu < 0,001 °C) et recoupés 8/8 contre la capture
  de SIA 180:2014 figure 4 (§5.2.2.5 : identité normative établie). Source :
  ``refs/reference-data/sia-380-2-2022.figure1.json`` /
  ``refs/reference-data/sia-180-2014.comfort.json``. Statut : VÉRIFIÉ.
  (``test_reference.py`` re-vérifie ces sommets contre le JSON figé afin
  qu'ils ne puissent pas dériver silencieusement.)
"""

from __future__ import annotations

from typing import List, Tuple

# --- Fig.3 SIA 180 : Anhang C1 (baulische Grundanforderungen) ----------------
# Étiquettes d'équation imprimées sur Abbildung 3 du rapport-oracle §3.2.
FIG3_UPPER_SLOPE = 0.33      # SIA 180 Fig.3, courbe sup. — pente (étiquette rapport)
FIG3_UPPER_INTERCEPT = 21.8  # SIA 180 Fig.3, courbe sup. — ordonnée (étiquette rapport)
FIG3_UPPER_PLATEAU = 25.0    # SIA 180 Fig.3, plateau bas de la courbe sup. (lecture graphique) [À VÉRIFIER]
FIG3_LOWER_SLOPE = 0.33      # SIA 180 Fig.3, courbe inf. — pente (étiquette rapport)
FIG3_LOWER_INTERCEPT = 14.3  # SIA 180 Fig.3, courbe inf. — ordonnée (étiquette rapport)


def fig3_upper(theta_rm: float) -> float:
    """Limite SUPÉRIEURE de Fig.3 SIA 180 (C1).

    ``max(25 ; 0,33·θrm + 21,8)`` — cf. Abbildung 3 du rapport.
    """
    return max(FIG3_UPPER_PLATEAU, FIG3_UPPER_SLOPE * theta_rm + FIG3_UPPER_INTERCEPT)


def fig3_lower(theta_rm: float) -> float:
    """Limite INFÉRIEURE de Fig.3 SIA 180 (C1).

    ``0,33·θrm + 14,3`` — cf. Abbildung 3 du rapport.
    """
    return FIG3_LOWER_SLOPE * theta_rm + FIG3_LOWER_INTERCEPT


# --- Fig.4 SIA 180 : Anhang C2 (Behaglichkeitsgrenzen) -----------------------
# Sommets (θrm, θ) figés, source refs/reference-data/sia-380-2-2022.figure1.json
# (= SIA 180:2014 figure 4 par identité normative §5.2.2.5). Domaine θrm 10..25.
FIG4_UPPER_VERTICES: List[Tuple[float, float]] = [
    (10.0, 24.5), (12.0, 24.5), (17.5, 26.5), (25.0, 26.5),
]
FIG4_LOWER_VERTICES: List[Tuple[float, float]] = [
    (10.0, 20.5), (19.0, 20.5), (23.5, 22.0), (25.0, 22.0),
]
FIG4_DOMAIN = (10.0, 25.0)  # SIA 180 Fig.4 / SIA 380/2 fig.1, abscisse tracée


def _piecewise_linear(vertices: List[Tuple[float, float]], x: float) -> float:
    """Interpolation linéaire par morceaux, avec CLAMP plat hors domaine.

    Hors de ``[x0, xN]`` on prolonge par la valeur du sommet le plus proche
    (les extrémités de Fig.4 sont des plateaux horizontaux).
    ``[À VÉRIFIER]`` : convention d'extrapolation sous θrm=10 / au-dessus de 25.
    Sans effet sur les verdicts ZOER (marge large — voir TRACEABILITY.md).
    """
    if x <= vertices[0][0]:
        return vertices[0][1]
    if x >= vertices[-1][0]:
        return vertices[-1][1]
    for (x0, y0), (x1, y1) in zip(vertices, vertices[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return vertices[-1][1]  # inatteignable


def fig4_upper(theta_rm: float) -> float:
    """Limite SUPÉRIEURE (obere Behaglichkeitsgrenze) de Fig.4 SIA 180 (C2)."""
    return _piecewise_linear(FIG4_UPPER_VERTICES, theta_rm)


def fig4_lower(theta_rm: float) -> float:
    """Limite INFÉRIEURE de Fig.4 SIA 180 (C2)."""
    return _piecewise_linear(FIG4_LOWER_VERTICES, theta_rm)
