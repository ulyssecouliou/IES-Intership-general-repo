"""Normalized SIA 4010 expected/observed result contracts."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ExpectedResult:
    """One official expected metric with source-provided tolerances."""

    test_id: str
    case_id: str
    metric: str
    expected_value: float
    unit: str
    absolute_tolerance: Optional[float]
    relative_tolerance: Optional[float]
    source_locator: str
    source_checksum: str
    # Official reference band, when the SIA workbook supplies explicit
    # lower/upper acceptance bounds ("untere Grenze"/"obere Grenze"). When both
    # are present the band is the acceptance criterion and takes precedence over
    # any tolerance; expected_value then typically carries the reference mean
    # ("Mittelwert") for audit only.
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

    @property
    def has_band(self) -> bool:
        """Return whether an explicit official acceptance band is available."""

        return self.lower_bound is not None and self.upper_bound is not None

    @property
    def key(self) -> str:
        """Return the stable compound identifier for this metric."""

        return "{}|{}|{}".format(self.test_id, self.case_id, self.metric)

    def to_dict(self) -> Dict[str, Any]:
        """Return the expected result as serializable data."""

        return asdict(self)


@dataclass(frozen=True)
class ObservedResult:
    """One metric extracted from a completed VE simulation."""

    test_id: str
    case_id: str
    metric: str
    value: float
    unit: str
    evidence_locator: str

    @property
    def key(self) -> str:
        """Return the stable compound identifier for this metric."""

        return "{}|{}|{}".format(self.test_id, self.case_id, self.metric)

    def to_dict(self) -> Dict[str, Any]:
        """Return the observed result as serializable data."""

        return asdict(self)
