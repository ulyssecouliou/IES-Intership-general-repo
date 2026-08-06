"""Exemple : lire un modèle IESVE et inventorier les fichiers officiels SIA.

Exécution :
    python examples/usage_repositories.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permet `python examples/usage_*.py` depuis n'importe quel dossier : sans
# cela, la racine du dépôt n'est pas sur sys.path et `import schemas` échoue.
_RACINE = Path(__file__).resolve().parent.parent
if str(_RACINE) not in sys.path:
    sys.path.insert(0, str(_RACINE))

from core.factories import CheckerFactory  # noqa: E402 -- après le bootstrap sys.path
from core.repositories import (  # noqa: E402
    JsonIESVERepository,
    SIA4010Repository,
)  # noqa: E402 -- après le bootstrap sys.path

#: Instantané minimal, tel que l'adaptateur IESVE le produira.
INSTANTANE = {
    "rooms": [
        {
            "id": "101",
            "volume": 1057.9,
            "usage": "4.04",
            "floor_area": 165.81,
            "surfaces": [
                {"id": "TOIT_101", "area": 165.81, "u_value": 0.17},
                {"id": "MUR_S_101", "area": 48.0, "u_value": 0.17, "orientation": 180.0},
            ],
            "openings": [],
        },
        {"id": "102", "volume": 314.8, "usage": "3.02", "floor_area": 104.94},
    ]
}


def demontrer_depot_iesve() -> None:
    """Lit un instantané et interroge les locaux."""
    depot = JsonIESVERepository.from_mapping(INSTANTANE)
    print("locaux            :", [local.id for local in depot.get_rooms()])
    print("volume total      : %.1f m3" % depot.total_volume())

    horsaal = depot.get_room("101")
    print(
        "local 101         : usage %s, %.2f m2 opaques"
        % (horsaal.usage, horsaal.opaque_area)
    )
    print("usage 3.02        :", [r.id for r in depot.get_rooms_by_usage("3.02")])


def demontrer_depot_sia() -> None:
    """Inventorie les fichiers officiels et montre l'erreur d'absence."""
    depot = SIA4010Repository("data/sia4010_official")
    disponibles = depot.available_tests()
    print("tests officiels   :", disponibles or "(aucun — dossier vide)")

    try:
        depot.require_evaluation("test_7")
    except FileNotFoundError as erreur:
        print("absence signalée  :", str(erreur).splitlines()[0])


def demontrer_strategies() -> None:
    """Montre qu'une prévalidation ne peut pas conclure comme une validation."""
    depot = JsonIESVERepository.from_mapping(INSTANTANE)

    pdf = CheckerFactory.create_strategy("pdf_prevalidation")
    resultat = pdf.validate("test_1", depot)
    print(
        "prévalidation PDF : %s (fait autorité : %s)"
        % (resultat.status.value, pdf.is_authoritative)
    )

    officielle = CheckerFactory.create_strategy("official")
    resultat_officiel = officielle.validate("test_7", {})
    print(
        "validation off.   : %s — %s"
        % (resultat_officiel.status.value, resultat_officiel.errors[0].splitlines()[0])
    )


if __name__ == "__main__":
    print("=== dépôt IESVE ===")
    demontrer_depot_iesve()
    print()
    print("=== dépôt SIA 4010 ===")
    demontrer_depot_sia()
    print()
    print("=== stratégies ===")
    demontrer_strategies()
