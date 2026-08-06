"""Exemple : validation de données par les schémas Pydantic.

Montre surtout ce qui est REFUSÉ — c'est là que les schémas gagnent leur place.

Exécution :
    python examples/usage_schemas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permet `python examples/usage_*.py` depuis n'importe quel dossier : sans
# cela, la racine du dépôt n'est pas sur sys.path et `import schemas` échoue.
_RACINE = Path(__file__).resolve().parent.parent
if str(_RACINE) not in sys.path:
    sys.path.insert(0, str(_RACINE))

from pydantic import ValidationError  # noqa: E402 -- après le bootstrap sys.path

from schemas import (  # noqa: E402 -- après le bootstrap sys.path
    Opening,
    Room,
    Surface,
    TestResult,
    TestStatus,
    ValidationClass,
)


def construire_un_local() -> Room:
    """Assemble un local valide et affiche ses agrégats.

    Returns:
        Room: Le local construit.
    """
    local = Room(
        id="101",
        volume=1057.9,
        usage="4.04",
        floor_area=165.81,
        surfaces=(
            Surface(id="TOIT", area=165.81, u_value=0.17),
            Surface(id="MUR_S", area=48.0, u_value=0.17, orientation=180.0),
        ),
        openings=(Opening(id="F_S", area=12.0, g_value=0.6, u_value=1.1),),
    )
    print(
        "local %s : %.1f m3, opaque %.2f m2, ouvertures %.2f m2"
        % (local.id, local.volume, local.opaque_area, local.opening_area)
    )
    return local


def montrer_les_refus() -> None:
    """Provoque volontairement chaque refus, pour documenter les bornes."""
    cas = [
        ("aire nulle", lambda: Surface(id="S", area=0.0, u_value=0.2)),
        ("U opaque > 2,0", lambda: Surface(id="S", area=1.0, u_value=2.984)),
        ("g > 1", lambda: Opening(id="O", area=1.0, g_value=1.5, u_value=1.0)),
        ("volume nul", lambda: Room(id="R", volume=0.0)),
        (
            "surfaces en doublon",
            lambda: Room(
                id="R",
                volume=10.0,
                surfaces=(
                    Surface(id="S", area=1.0, u_value=0.2),
                    Surface(id="S", area=2.0, u_value=0.2),
                ),
            ),
        ),
        (
            "échec sans motif",
            lambda: TestResult(
                test_name="t", status=TestStatus.FAIL, criterion_source="x"
            ),
        ),
    ]
    for libelle, fabrique in cas:
        try:
            fabrique()
        except ValidationError:
            print("  refusé : %s" % libelle)
        else:
            print("  ⚠ ACCEPTÉ à tort : %s" % libelle)


def montrer_le_vitrage_du_cas_600() -> None:
    """Le U d'un vitrage dépasse la borne opaque — et c'est normal."""
    fenetre = Opening(id="F600", area=12.0, g_value=0.787, u_value=2.984)
    print("vitrage cas 600 : U = %.3f W/(m2.K), accepté comme Opening" % fenetre.u_value)
    print("  (la borne opaque de 2,0 rejetterait ce cas de test officiel)")


def montrer_une_classe_incomplete() -> None:
    """Une classe n'est acquise que si TOUS ses tests exigés sont là."""
    reussi = TestResult(
        test_name="test_7", status=TestStatus.PASS, criterion_source="classeur SIA"
    )
    classe_5 = ValidationClass(
        class_name="5", required_tests=("test_7",), results={"test_7": reussi}
    )
    classe_4a = ValidationClass(
        class_name="4A",
        required_tests=(
            "test_1",
            "test_2A",
            "test_3A_to_3F",
            "test_4",
            "test_5",
            "test_6",
            "test_7",
        ),
        results={"test_7": reussi},
    )
    print("classe 5  : %s" % classe_5.status.value)
    print(
        "classe 4A : %s — manquants : %s"
        % (classe_4a.status.value, ", ".join(classe_4a.missing_tests))
    )


if __name__ == "__main__":
    print("=== construction ===")
    construire_un_local()
    print()
    print("=== refus attendus ===")
    montrer_les_refus()
    print()
    print("=== cas limite ===")
    montrer_le_vitrage_du_cas_600()
    print()
    print("=== classes ===")
    montrer_une_classe_incomplete()
