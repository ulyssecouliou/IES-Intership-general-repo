"""Persistent resume ledger for VE model creation.

VE model creation is a long transactional sequence: geometry import, then
per-asset mutation (materials, constructions, profiles, gains, air exchanges,
templates, room assignments). If it is interrupted mid-way and re-launched,
the naive strategy is to re-run every step, which can:

* silently duplicate rooms, gains, air exchanges or templates when the
  provisioner cannot see the previous run's partial state;
* mask a genuine mismatch under the appearance of ``reuse``.

This ledger records, for one target VE project directory, exactly which
provisioning steps completed, with which content fingerprint, and when.
On resume the caller queries the ledger for each intended step:

* ``ReuseDecision.REUSE`` -- the ledger holds a matching fingerprint;
  the caller may skip the mutation and use ``verify_only``.
* ``ReuseDecision.FRESH`` -- no ledger entry; the caller mutates normally
  and calls ``record`` afterwards.
* ``ReuseDecision.FAIL_CLOSED`` -- a ledger entry exists but the requested
  fingerprint differs from the recorded one.  The caller must NOT mutate;
  it must surface the mismatch and let the operator either re-run cleanly on
  a fresh project or explicitly ``discard`` the stale entry.

The ledger is a plain JSON file, atomic on write, human-readable, and safe to
share via version control if the operator chooses.  It stores no VE runtime
handle -- only fingerprints and metadata.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional


LEDGER_SCHEMA_VERSION = "1.0"
LEDGER_STATUS_COMPLETED = "COMPLETED"


class ReuseDecision(Enum):
    """Outcome of a resume-ledger consultation."""

    FRESH = "FRESH"
    REUSE = "REUSE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class LedgerEntry:
    """One immutable ledger row."""

    step_id: str
    fingerprint: str
    recorded_at: str
    payload_summary: Dict[str, Any] = field(default_factory=dict)
    status: str = LEDGER_STATUS_COMPLETED


@dataclass(frozen=True)
class LedgerConsultation:
    """Result of ``ResumeLedger.consult``."""

    decision: ReuseDecision
    step_id: str
    requested_fingerprint: str
    recorded_entry: Optional[LedgerEntry]
    mismatch_summary: Dict[str, Any] = field(default_factory=dict)


def _canonical_json(payload: Any) -> str:
    """Deterministic JSON dump used for fingerprinting."""

    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def compute_fingerprint(payload: Any) -> str:
    """SHA-256 fingerprint of a JSON-serialisable payload."""

    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _atomic_write(path: str, content: str) -> None:
    """Write ``content`` to ``path`` atomically on Windows and POSIX."""

    directory = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=directory,
        prefix=".ledger-",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(content)
        tmp_name = handle.name
    os.replace(tmp_name, path)


class ResumeLedger:
    """JSON-backed idempotent resume ledger for one VE project.

    Instances are lightweight and lazily load the on-disk file.  Concurrent
    writers on the same file are not supported; callers must serialise
    provisioning to one process.
    """

    def __init__(self, ledger_path: str, *, project_id: str, clock=None):
        self._path = ledger_path
        self._project_id = project_id
        self._clock = clock or _iso_now
        self._entries: Dict[str, LedgerEntry] = {}
        self._loaded = False

    # ------------------------------------------------------------------ io

    def _iso_timestamp(self) -> str:
        return self._clock()

    def load(self) -> None:
        """Load the on-disk ledger; a missing file is a valid fresh ledger."""

        if not os.path.exists(self._path):
            self._entries = {}
            self._loaded = True
            return
        with open(self._path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, Mapping):
            raise ValueError(
                "Ledger at {} is not a mapping; refusing to load".format(self._path)
            )
        schema = payload.get("schema_version")
        if schema != LEDGER_SCHEMA_VERSION:
            raise ValueError(
                "Ledger schema_version={} but expected {}".format(
                    schema, LEDGER_SCHEMA_VERSION
                )
            )
        stored_project = payload.get("project_id")
        if stored_project is not None and stored_project != self._project_id:
            raise ValueError(
                "Ledger at {} belongs to project '{}' but caller passed '{}'".format(
                    self._path, stored_project, self._project_id
                )
            )
        self._entries = {}
        for row in payload.get("entries", []) or []:
            step_id = row.get("step_id")
            fingerprint = row.get("fingerprint")
            if not step_id or not fingerprint:
                continue
            self._entries[step_id] = LedgerEntry(
                step_id=str(step_id),
                fingerprint=str(fingerprint),
                recorded_at=str(row.get("recorded_at", "")),
                payload_summary=dict(row.get("payload_summary", {}) or {}),
                status=str(row.get("status", LEDGER_STATUS_COMPLETED)),
            )
        self._loaded = True

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def flush(self) -> None:
        """Persist the current in-memory ledger to disk atomically."""

        payload = {
            "schema_version": LEDGER_SCHEMA_VERSION,
            "project_id": self._project_id,
            "entries": [
                {
                    "step_id": entry.step_id,
                    "fingerprint": entry.fingerprint,
                    "recorded_at": entry.recorded_at,
                    "payload_summary": entry.payload_summary,
                    "status": entry.status,
                }
                for entry in sorted(self._entries.values(), key=lambda e: e.step_id)
            ],
        }
        _atomic_write(self._path, _canonical_json(payload))

    # ------------------------------------------------------------------ query

    def consult(
        self,
        step_id: str,
        payload: Any,
    ) -> LedgerConsultation:
        """Decide whether ``step_id`` can be reused, is fresh, or must fail closed."""

        self._ensure_loaded()
        requested = compute_fingerprint(payload)
        recorded = self._entries.get(step_id)
        if recorded is None:
            return LedgerConsultation(
                decision=ReuseDecision.FRESH,
                step_id=step_id,
                requested_fingerprint=requested,
                recorded_entry=None,
            )
        if recorded.fingerprint == requested:
            return LedgerConsultation(
                decision=ReuseDecision.REUSE,
                step_id=step_id,
                requested_fingerprint=requested,
                recorded_entry=recorded,
            )
        return LedgerConsultation(
            decision=ReuseDecision.FAIL_CLOSED,
            step_id=step_id,
            requested_fingerprint=requested,
            recorded_entry=recorded,
            mismatch_summary={
                "recorded_fingerprint": recorded.fingerprint,
                "requested_fingerprint": requested,
                "recorded_at": recorded.recorded_at,
            },
        )

    # ------------------------------------------------------------------ write

    def record(
        self,
        step_id: str,
        payload: Any,
        *,
        payload_summary: Optional[Mapping[str, Any]] = None,
        status: str = LEDGER_STATUS_COMPLETED,
        flush: bool = True,
    ) -> LedgerEntry:
        """Record ``step_id`` as completed with the fingerprint of ``payload``.

        Recording a step that already exists with a different fingerprint is
        an error: the caller must call ``discard`` first with an explicit
        reason.  This is the anti-duplicate guarantee.
        """

        self._ensure_loaded()
        fingerprint = compute_fingerprint(payload)
        existing = self._entries.get(step_id)
        if existing is not None and existing.fingerprint != fingerprint:
            raise ValueError(
                "Refusing to overwrite ledger entry for step '{}'; existing "
                "fingerprint {} differs from new {}. Discard explicitly first.".format(
                    step_id, existing.fingerprint, fingerprint
                )
            )
        entry = LedgerEntry(
            step_id=step_id,
            fingerprint=fingerprint,
            recorded_at=self._iso_timestamp(),
            payload_summary=dict(payload_summary or {}),
            status=status,
        )
        self._entries[step_id] = entry
        if flush:
            self.flush()
        return entry

    def discard(self, step_id: str, *, reason: str, flush: bool = True) -> Optional[LedgerEntry]:
        """Remove a step's ledger entry; ``reason`` is required for audit trail."""

        if not reason.strip():
            raise ValueError("discard() requires a non-empty reason")
        self._ensure_loaded()
        removed = self._entries.pop(step_id, None)
        if flush and removed is not None:
            self.flush()
        return removed

    def entries(self) -> List[LedgerEntry]:
        self._ensure_loaded()
        return sorted(self._entries.values(), key=lambda e: e.step_id)


def _iso_now() -> str:
    """Fallback clock; the ledger accepts an injected clock for tests."""

    import datetime as _dt

    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


__all__ = [
    "LEDGER_SCHEMA_VERSION",
    "LEDGER_STATUS_COMPLETED",
    "ReuseDecision",
    "LedgerEntry",
    "LedgerConsultation",
    "ResumeLedger",
    "compute_fingerprint",
]
