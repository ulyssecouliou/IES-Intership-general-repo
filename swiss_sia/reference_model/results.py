"""Shared result and audit contracts."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationStatus(str, Enum):
    """Required three-state validation vocabulary."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ValidationResult:
    """One independently auditable validation control result."""

    control_id: str
    category: str
    status: ValidationStatus
    message: str
    object_id: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Return this control result as machine-readable data."""

        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class AuditEvent:
    """Append-only audit event emitted by the workflow."""

    sequence: int
    timestamp_utc: str
    stage: str
    action: str
    outcome: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return this audit event as machine-readable data."""

        return asdict(self)


def worst_status(results: List[ValidationResult]) -> ValidationStatus:
    """Return the worst status in a result collection."""

    statuses = {result.status for result in results}
    if ValidationStatus.FAIL in statuses:
        return ValidationStatus.FAIL
    if ValidationStatus.WARNING in statuses:
        return ValidationStatus.WARNING
    return ValidationStatus.PASS
