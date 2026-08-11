"""Pydantic schemas for the SIA 4010 / SIA 380-2 domain.

These models are the typed border between IESVE extraction and the validation
engines: everything entering a checker passes through them, which moves data
errors from the moment of calculation to the moment of reading. A wrong number
that reaches a calculation comes back as a plausible result; a wrong number
stopped at the border comes back as an error naming the field.

VEScripts COMPATIBILITY, CHECKED 2026-08-06. VE 2025's embedded Python is
3.12.3 and ships ``pydantic`` 2.12.5, ``typing_extensions`` and
``annotated_types``. These schemas therefore run inside VE, not only in CI --
which is not a given for a third-party dependency and is why the versions are
written down.

Example:
    >>> from schemas import Surface, Opening, Room
    >>> wall = Surface(id="S1", area=12.0, u_value=0.17, orientation=180.0,
    ...                is_external=True)
    >>> window = Opening(id="O1", area=3.0, g_value=0.6, u_value=1.1)
    >>> room = Room(id="R1", volume=30.0, surfaces=[wall], openings=[window])
    >>> round(room.opaque_area, 1)
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
