"""Compatibility adapters for version-sensitive Boost.Python VE signatures."""

from __future__ import annotations

from typing import Any, Dict


def thermal_templates(
    project: Any, assigned: bool = False, allow_ncm: bool = False
) -> Dict[str, Any]:
    """Return VE thermal templates across one- and two-argument API builds.

    Some VE 2025 Boost.Python builds expose ``thermal_templates`` without
    keyword-argument support and require the documented optional arguments to
    be passed positionally. Older test/runtime builds accept only ``assigned``.
    """

    errors = []
    for arguments in ((assigned, allow_ncm), (assigned,)):
        try:
            return project.thermal_templates(*arguments)
        except Exception as exc:
            errors.append("{}: {}".format(arguments, exc))
    raise RuntimeError(
        "VEProject.thermal_templates is unavailable for supported positional "
        "signatures: {}".format(" | ".join(errors))
    )
