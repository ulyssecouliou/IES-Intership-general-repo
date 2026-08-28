"""Standalone HTML and JSON output for the SIA 4010 validation navigator."""

import html
import json
from pathlib import Path
from typing import Dict, Union

from .navigator import NavigatorEvaluation


def _status_class(status: str) -> str:
    """Map a gate status to a CSS class."""

    return {
        "PASS": "pass",
        "FAIL": "fail",
        "BLOCKED": "blocked",
    }.get(str(status).upper(), "blocked")


def render_navigator_html(evaluation: NavigatorEvaluation) -> str:
    """Render a self-contained, read-only navigator page."""

    gate_cards = []
    for index, gate in enumerate(evaluation.gates, start=1):
        variants = ""
        affected = gate.failed_variants or gate.missing_variants
        if affected:
            variants = "<p><strong>Variants:</strong> {}</p>".format(
                html.escape(", ".join(affected))
            )
        gate_cards.append(
            """
            <section class="gate {css}">
              <div class="step">{index}</div>
              <div>
                <div class="gate-head"><h2>{label}</h2><span>{status}</span></div>
                <p>{message}</p>{variants}
                <p class="action"><strong>Action:</strong> {action}</p>
              </div>
            </section>
            """.format(
                css=_status_class(gate.status),
                index=index,
                label=html.escape(gate.label),
                status=html.escape(gate.status),
                message=html.escape(gate.message),
                variants=variants,
                action=html.escape(gate.next_action),
            )
        )

    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SIA 4010 navigator - class {target}</title>
  <style>
    :root {{ color-scheme: light; --ink:#17202a; --muted:#5f6b76;
      --pass:#197447; --pass-bg:#e9f7ef; --fail:#a32929; --fail-bg:#fff0f0;
      --block:#8a5a00; --block-bg:#fff7e1; --line:#d9e0e6; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#f4f6f8; color:var(--ink);
      font:15px/1.5 "Segoe UI", Arial, sans-serif; }}
    main {{ max-width:960px; margin:0 auto; padding:36px 20px 60px; }}
    header {{ background:#17324d; color:white; border-radius:14px; padding:28px; }}
    h1 {{ margin:0 0 6px; font-size:30px; }}
    header p {{ margin:5px 0; color:#dce8f2; }}
    .summary {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin:18px 0; }}
    .summary div {{ background:white; border:1px solid var(--line);
      border-radius:10px; padding:15px; }}
    .summary small {{ display:block; color:var(--muted); margin-bottom:4px; }}
    .gate {{ display:grid; grid-template-columns:44px 1fr; gap:14px; margin:12px 0;
      padding:18px; border:1px solid var(--line); border-left-width:7px;
      border-radius:10px; background:white; }}
    .gate.pass {{ border-left-color:var(--pass); }}
    .gate.fail {{ border-left-color:var(--fail); background:var(--fail-bg); }}
    .gate.blocked {{ border-left-color:var(--block); background:var(--block-bg); }}
    .step {{ width:34px; height:34px; display:grid; place-items:center;
      border-radius:50%; background:#e7edf2; font-weight:700; }}
    .gate-head {{ display:flex; align-items:center; justify-content:space-between; gap:10px; }}
    h2 {{ margin:0; font-size:19px; }}
    .gate-head span {{ font-weight:800; letter-spacing:.04em; }}
    .action {{ color:var(--muted); margin-bottom:0; }}
    footer {{ margin-top:20px; padding:16px; border-top:1px solid var(--line);
      color:var(--muted); }}
    @media (max-width:640px) {{ .summary {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body><main>
  <header>
    <h1>SIA 4010 validation navigator</h1>
    <p>Target class: {target} - required variants: {variants}</p>
  </header>
  <div class="summary">
    <div><small>Overall status</small><strong>{overall}</strong></div>
    <div><small>Technical status</small><strong>{technical}</strong></div>
  </div>
  {gates}
  <footer>{guardrail}</footer>
</main></body></html>
""".format(
        target=html.escape(evaluation.target_class),
        variants=html.escape(", ".join(evaluation.required_variants)),
        overall=html.escape(evaluation.overall_status),
        technical=html.escape(evaluation.technical_status),
        gates="\n".join(gate_cards),
        guardrail=html.escape(evaluation.claim_guardrail),
    )


def write_navigator_artifacts(
    evaluation: NavigatorEvaluation,
    output_directory: Union[str, Path],
) -> Dict[str, str]:
    """Write deterministic JSON and HTML artifacts and return their paths."""

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    stem = "sia4010_navigator_{}".format(evaluation.target_class.lower())
    json_path = output / "{}.json".format(stem)
    html_path = output / "{}.html".format(stem)
    json_path.write_text(
        json.dumps(evaluation.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    html_path.write_text(render_navigator_html(evaluation), encoding="utf-8")
    return {"json": str(json_path), "html": str(html_path)}
