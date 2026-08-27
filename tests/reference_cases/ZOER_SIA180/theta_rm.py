"""Moyenne glissante extérieure θrm sur 48 heures (SIA 180 / rapport §3.1).

Le rapport-oracle §3.1 définit :

    θrm(H) = (1/48) · Σ_{j=H-48}^{H} θe(j)

soit la MOYENNE ARITHMÉTIQUE SIMPLE de la température extérieure sèche sur les
48 heures écoulées (« gleitender Mittelwert der Aussenlufttemperatur über die
letzten zwei Tage »). Ce n'est PAS la moyenne exponentielle pondérée d'EN 15251.

Convention de fenêtre : moyenne des 48 valeurs horaires ``[H-47 … H]`` (heure
courante incluse). Le verdict ZOER est insensible au choix 48 vs 49 termes
(vérifié : 0 dépassement dans les deux cas).

Convention de bord (48 premières heures — ``[À VÉRIFIER]`` du rapport, non
précisé) : option (a) fenêtre TRONQUÉE sur les heures disponibles. Choix
documenté ; sans effet sur le verdict (les premières heures sont en avril, θrm
bas, opérative ~21 °C, très loin des courbes). Les pas dont la température
extérieure est absente (premier pas de la série C1) sont ignorés dans la moyenne.
"""

from __future__ import annotations

from typing import List, Optional

WINDOW_HOURS = 48


def rolling_mean_48h(
    exterior: List[Optional[float]], window: int = WINDOW_HOURS
) -> List[Optional[float]]:
    """θrm pour chaque pas, à partir d'une série extérieure alignée au pas horaire.

    ``exterior[i]`` est la température extérieure (°C) du pas ``i`` (ou ``None``
    si absente). Retourne une liste de même longueur : ``theta_rm[i]`` = moyenne
    des valeurs non-``None`` dans ``[i-window+1 … i]``, ou ``None`` si la fenêtre
    ne contient aucune valeur.
    """
    out: List[Optional[float]] = []
    for i in range(len(exterior)):
        lo = max(0, i - window + 1)
        vals = [v for v in exterior[lo : i + 1] if v is not None]
        out.append(sum(vals) / len(vals) if vals else None)
    return out
