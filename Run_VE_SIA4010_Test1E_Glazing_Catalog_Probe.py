"""Read-only search for the prescribed Test 1E Planitherm glazing in VE CDB."""

import json
from datetime import datetime
from pathlib import Path

import iesve


TOKENS = ("planitherm", "sgg", "xn", "4/14/4/14/4")
TARGET_U_W_M2K = 0.654
TARGET_G_VALUE = 0.545
TARGET_VISIBLE_TRANSMITTANCE = 0.742


def _sequence(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _construction_ids(cdb_project):
    classes = getattr(iesve.VECdbProject, "construction_class", None) or getattr(
        iesve, "construction_class", None
    )
    none_class = getattr(classes, "none", None) if classes is not None else None
    attempts = [(none_class,)] if none_class is not None else []
    attempts.append(tuple())
    for arguments in attempts:
        try:
            return [str(value) for value in cdb_project.get_construction_ids(*arguments)]
        except Exception:
            continue
    return []


def _construction(cdb_project, identifier):
    classes = getattr(iesve.VECdbProject, "construction_class", None) or getattr(
        iesve, "construction_class", None
    )
    none_class = getattr(classes, "none", None) if classes is not None else None
    attempts = [(identifier, none_class)] if none_class is not None else []
    attempts.append((identifier,))
    for arguments in attempts:
        try:
            value = cdb_project.get_construction(*arguments)
        except Exception:
            continue
        if value is not None:
            return value
    return None


def run():
    project = iesve.VEProject.get_current_project()
    project_root = Path(str(project.path)).resolve()
    database = iesve.VECdbDatabase.get_current_database()
    project_groups = database.get_projects()
    if isinstance(project_groups, dict):
        groups = [
            (str(key), item)
            for key, values in project_groups.items()
            for item in _sequence(values)
        ]
    else:
        groups = [("unknown", item) for item in _sequence(project_groups)]

    matches = []
    inspected = 0
    errors = []
    for group, cdb_project in groups:
        for identifier in _construction_ids(cdb_project):
            inspected += 1
            construction = _construction(cdb_project, identifier)
            if construction is None:
                continue
            try:
                properties = dict(construction.get_properties())
            except Exception as exc:
                errors.append({"id": identifier, "error": str(exc)})
                properties = {}
            haystack = "{} {} {}".format(
                identifier,
                getattr(construction, "reference", ""),
                json.dumps(properties, default=str),
            ).casefold()
            if not any(token in haystack for token in TOKENS):
                continue
            try:
                layers = list(construction.get_layers())
            except Exception:
                layers = []
            matches.append(
                {
                    "database_group": group,
                    "identifier": identifier,
                    "reference": str(getattr(construction, "reference", "")),
                    "properties": properties,
                    "layer_count": len(layers),
                    "layers": [
                        dict(layer.get_properties()) for layer in layers
                    ],
                }
            )

    exact_matches = []
    for match in matches:
        reference = match["reference"].casefold()
        properties = match["properties"]
        if not ("xn" in reference and "4/14/4/14/4" in reference):
            continue
        try:
            exact_performance = (
                abs(float(properties["net_u_value"]) - TARGET_U_W_M2K) <= 0.01
                and abs(float(properties["g_value"]) - TARGET_G_VALUE) <= 0.01
                and abs(
                    float(properties["visible_light_transmittance"])
                    - TARGET_VISIBLE_TRANSMITTANCE
                ) <= 0.01
            )
        except (KeyError, TypeError, ValueError):
            exact_performance = False
        if exact_performance and match["layer_count"] == 5:
            exact_matches.append(match)
    if exact_matches:
        status = "EXACT_GLAZING_CANDIDATES_FOUND"
    elif matches:
        status = "LEXICAL_CANDIDATES_ONLY_NO_EXACT_MATCH"
    else:
        status = "NO_PLANITHERM_CANDIDATE_IN_EXPOSED_CDB"
    payload = {
        "schema_version": "1.0",
        "status": status,
        "project": str(project_root),
        "database_groups": len(groups),
        "constructions_inspected": inspected,
        "search_tokens": list(TOKENS),
        "exact_target": {
            "product": "SGG Planitherm XN 4/14/4/14/4",
            "layer_count": 5,
            "net_u_value_w_m2k": TARGET_U_W_M2K,
            "g_value": TARGET_G_VALUE,
            "visible_light_transmittance": TARGET_VISIBLE_TRANSMITTANCE,
        },
        "matches": matches,
        "exact_matches": exact_matches,
        "read_errors": errors,
        "read_only": True,
        "compliance_claim_allowed": False,
    }
    output = (
        project_root
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_test1e_glazing_catalog_probe_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    print("SIA 4010 TEST 1E GLAZING CATALOG PROBE: {}".format(status))
    print("CDB groups: {}; constructions inspected: {}".format(len(groups), inspected))
    print("Candidates: {}".format(len(matches)))
    for match in matches:
        print(
            "- {} | {} | layers={}".format(
                match["identifier"], match["reference"], match["layer_count"]
            )
        )
    print("Report: {}".format(output))
    print("No VE model, CDB object or project data was changed.")
    return output


if __name__ == "__main__":
    run()
