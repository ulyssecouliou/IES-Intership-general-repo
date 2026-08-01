"""Domain-specific exceptions for reference-model generation."""


class ReferenceModelError(Exception):
    """Base class for controlled reference-model failures."""


class ConfigurationError(ReferenceModelError):
    """Configuration is incomplete, inconsistent, or untraceable."""


class GeometryError(ReferenceModelError):
    """Generated geometry violates the deterministic geometry contract."""


class VeApiUnavailableError(ReferenceModelError):
    """The IESVE Python API is unavailable or lacks a required capability."""


class VeMutationError(ReferenceModelError):
    """A requested IESVE model mutation failed or could not be verified."""


class ValidationGateError(ReferenceModelError):
    """A fail-closed validation gate prevented further mutation."""
