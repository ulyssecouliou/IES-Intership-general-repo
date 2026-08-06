"""Schémas Pydantic du domaine SIA 4010 / SIA 380-2.

Ces modèles sont la frontière typée entre l'extraction IESVE et les moteurs de
validation : tout ce qui entre dans un checker passe par eux, ce qui déplace
les erreurs de données du moment du calcul vers le moment de la lecture.

Compatibilité VEScripts vérifiée le 2026-08-06 : le Python embarqué de
VE 2025 est en 3.12.3 et fournit ``pydantic`` 2.12.5, ``typing_extensions`` et
``annotated_types``. Ces schémas peuvent donc s'exécuter à l'intérieur de VE,
pas seulement en CI.

Exemple:
    >>> from schemas import Surface, Opening, Room
    >>> mur = Surface(id="S1", area=12.0, u_value=0.17, orientation=180.0,
    ...               is_external=True)
    >>> fenetre = Opening(id="O1", area=3.0, g_value=0.6, u_value=1.1)
    >>> local = Room(id="R1", volume=30.0, surfaces=[mur], openings=[fenetre])
    >>> round(local.opaque_area, 1)
    12.0
"""

from schemas.opening_schema import Opening, OpeningType
from schemas.room_schema import Room
from schemas.surface_schema import Surface
from schemas.test_result_schema import TestResult, TestStatus
from schemas.validation_class_schema import ValidationClass, ValidationClassStatus

__all__ = [
    "Opening",
    "OpeningType",
    "Room",
    "Surface",
    "TestResult",
    "TestStatus",
    "ValidationClass",
    "ValidationClassStatus",
]
