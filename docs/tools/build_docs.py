"""Build helper for the Sphinx documentation.

The VE workflow must stay independent from documentation tooling. This script is
intended for developer machines and CI only.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
SOURCE_DIR = DOCS_DIR / "source"
BUILD_DIR = DOCS_DIR / "build"


def build_docs(language: str, builder: str, output_root: Path = BUILD_DIR) -> int:
    """Run Sphinx for one builder/language combination under an output root."""
    if importlib.util.find_spec("sphinx") is None:
        print(
            "Sphinx is not installed in this Python environment.\n"
            "Install the documentation dependencies first:\n"
            f"{sys.executable} -m pip install -r {DOCS_DIR / 'requirements-docs.txt'}",
            file=sys.stderr,
        )
        return 2

    if builder == "gettext":
        output_dir = output_root / "gettext"
        doctree_dir = output_root / "doctrees" / "gettext"
        command = [
            sys.executable,
            "-m",
            "sphinx",
            "-b",
            "gettext",
            "-d",
            str(doctree_dir),
            str(SOURCE_DIR),
            str(output_dir),
        ]
    else:
        output_dir = output_root / builder / language
        doctree_dir = output_root / "doctrees" / language
        command = [
            sys.executable,
            "-m",
            "sphinx",
            "-b",
            builder,
            "-d",
            str(doctree_dir),
            str(SOURCE_DIR),
            str(output_dir),
            "-D",
            f"language={language}",
        ]

    print("Running:", " ".join(command))
    return subprocess.call(command, cwd=str(ROOT))


def main() -> int:
    """Parse command-line arguments and build the documentation."""
    parser = argparse.ArgumentParser(description="Build Swiss SIA checker documentation.")
    parser.add_argument("--language", default="en", choices=["en", "fr", "it", "de"])
    parser.add_argument("--builder", default="html", choices=["html", "singlehtml", "gettext"])
    parser.add_argument(
        "--output-root",
        type=Path,
        default=BUILD_DIR,
        help="Root directory for generated HTML and doctrees.",
    )
    args = parser.parse_args()
    return build_docs(
        language=args.language,
        builder=args.builder,
        output_root=args.output_root.resolve(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
