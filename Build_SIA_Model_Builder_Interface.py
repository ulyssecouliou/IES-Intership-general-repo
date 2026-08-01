"""Build the dependency-free local Swiss VE Model Builder interface."""

import json
from pathlib import Path

from swiss_sia.reference_model.sia4010.model_scenario import build_feature_catalog
from swiss_sia.reference_model.sia4010.ui_translations import (
    DEFAULT_LANGUAGE,
    LANGUAGE_LABELS,
    LANGUAGES,
    full_catalog,
)


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "templates" / "sia_model_builder.html"
OUTPUT = (
    ROOT
    / "sia4010_evidence"
    / "model_builder"
    / "sia_model_builder.html"
)


def _embed(payload):
    """Serialize one payload for safe inlining inside a <script> element."""

    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")


def build():
    """Inject the feature catalog and the translations into the HTML interface."""

    replacements = {
        "__CATALOG_JSON__": _embed(build_feature_catalog()),
        "__I18N_JSON__": _embed(
            {
                "default": DEFAULT_LANGUAGE,
                "languages": list(LANGUAGES),
                "labels": {code: LANGUAGE_LABELS[code] for code in LANGUAGES},
                "strings": full_catalog(),
            }
        ),
    }
    html = TEMPLATE.read_text(encoding="utf-8")
    for placeholder, payload in replacements.items():
        html = html.replace(placeholder, payload)
        if placeholder in html:
            raise RuntimeError(
                "Model Builder injection failed for {}".format(placeholder)
            )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print("Swiss VE Model Builder: {}".format(OUTPUT))
    return OUTPUT


if __name__ == "__main__":
    build()
