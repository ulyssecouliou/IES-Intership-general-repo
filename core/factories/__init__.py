"""Fabriques découplant l'appelant des classes concrètes."""

from core.factories.checker_factory import (
    CheckerFactory,
    UnknownCheckerError,
)

__all__ = ["CheckerFactory", "UnknownCheckerError"]
