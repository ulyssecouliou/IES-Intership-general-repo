# -*- coding: utf-8 -*-
"""Write the static client SIA 380/2 compliance-criteria manifest to docs/.

Thin writer around ``swiss_sia.compliance_criteria.build_manifest`` (which holds
the pure build logic, shared with the runtime evaluator). Regulatory values come
from ``swiss_sia/config.py``; this script only serialises the manifest.

Pure Python, no ``iesve`` import. Run:

    python scripts/build_client_compliance_criteria.py
"""

import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from swiss_sia.compliance_criteria import build_manifest  # noqa: E402

_OUTPUT = os.path.join(_ROOT, "docs", "project", "CLIENT_COMPLIANCE_CRITERIA.json")


def main():
    manifest = build_manifest()
    os.makedirs(os.path.dirname(_OUTPUT), exist_ok=True)
    with io.open(_OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    counts = {}
    for crit in manifest["criteria"]:
        counts[crit["ve_capability"]] = counts.get(crit["ve_capability"], 0) + 1
    print("Wrote", _OUTPUT)
    print("Criteria:", len(manifest["criteria"]), "| capability breakdown:", counts)


if __name__ == "__main__":
    main()
