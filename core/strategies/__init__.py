"""Stratégies de validation : prévalidation PDF ou validation officielle."""

from core.strategies.official_validation_strategy import OfficialValidationStrategy
from core.strategies.pdf_validation_strategy import PdfValidationStrategy
from core.strategies.validation_strategy import ValidationStrategy

__all__ = [
    "OfficialValidationStrategy",
    "PdfValidationStrategy",
    "ValidationStrategy",
]
