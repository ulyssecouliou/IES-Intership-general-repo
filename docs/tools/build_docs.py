"""Build helper for the Sphinx documentation.

The VE workflow must stay independent from documentation tooling. This script is
intended for developer machines and CI only.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
SOURCE_DIR = DOCS_DIR / "source"
BUILD_DIR = DOCS_DIR / "build"


def build_docs(language: str, builder: str) -> int:
    """Run sphinx-build for one builder/language combination."""
    if builder == "gettext":
        output_dir = BUILD_DIR / "gettext"
        command = [
            sys.executable,
            "-m",
            "sphinx",
            "-b",
            "gettext",
            str(SOURCE_DIR),
            str(output_dir),
        ]
    else:
        output_dir = BUILD_DIR / builder / language
        command = [
            sys.executable,
            "-m",
            "sphinx",
            "-b",
            builder,
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
    parser.add_argument("--builder", default="html", choices=["html", "gettext"])
    args = parser.parse_args()
    return build_docs(language=args.language, builder=args.builder)


if __name__ == "__main__":
    raise SystemExit(main())

