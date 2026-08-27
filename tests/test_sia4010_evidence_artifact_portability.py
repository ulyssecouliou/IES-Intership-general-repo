"""Portability guards for the tracked SIA 4010 delegated-input evidence.

These artifacts are the traceability chain a third party reviews from a fresh
clone.  Two defects break them there while leaving the authoring machine green,
so neither shows up in any functional test:

* an absolute path, which resolves only on the machine that wrote it;
* a binding artifact written into a directory ``.gitignore`` excludes, which
  simply is not in the clone.

Both happened on 2026-08-13 and are recorded in the MVP completion matrix.  The
tests below are what stops them from coming back.
"""

import io
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Validation report -> the schema its binding artifact must declare.
TRACKED_REPORTS = {
    "refs/reference-data/iso52016_chapter7_test_cell.validation.json": (
        "sia4010.iso52016_chapter7_test_cell.v1"
    ),
    "references/standards/sia2028/KLO_dry.validation.json": (
        "sia4010.sia2028_hourly_weather.v1"
    ),
}

#: Normalized binding artifacts that must travel with the repository.
TRACKED_BINDINGS = (
    "refs/reference-data/iso52016_chapter7_test_cell.binding.json",
    "references/standards/sia2028/KLO_SIA2028_DRY_NORMAL.binding.json",
)

#: A Windows drive-letter path, or a POSIX absolute path in a locator field.
_ABSOLUTE = re.compile(r"[A-Za-z]:[\\/]|^/(?:home|Users|mnt|opt)/")


def _load(relative):
    """Return one tracked JSON artifact.

    Args:
        relative: Repository-relative path.

    Returns:
        dict: Parsed payload.
    """
    with io.open(ROOT / relative, encoding="utf-8") as handle:
        return json.load(handle)


def _path_like_strings(node, trail=""):
    """Yield every string value under a key that names a path.

    Args:
        node: Any JSON node.
        trail: Accumulated key trail, for the failure message.

    Yields:
        tuple[str, str]: Key trail and the string value.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _path_like_strings(value, "{}.{}".format(trail, key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _path_like_strings(value, "{}[{}]".format(trail, index))
    elif isinstance(node, str) and (
        trail.endswith("path")
        or trail.endswith("_path")
        or trail.endswith("with")
        or trail.endswith("truth")
    ):
        yield trail, node


class EvidenceArtifactPortabilityTests(unittest.TestCase):
    def test_no_tracked_evidence_artifact_carries_an_absolute_path(self):
        """A path that names one machine's home directory is not evidence."""

        for relative in list(TRACKED_REPORTS) + list(TRACKED_BINDINGS):
            payload = _load(relative)
            for trail, value in _path_like_strings(payload):
                with self.subTest(artifact=relative, field=trail):
                    self.assertIsNone(
                        _ABSOLUTE.search(value),
                        "{}{} is absolute: {!r}".format(relative, trail, value),
                    )

    def test_report_binding_paths_resolve_from_the_report_directory(self):
        """The reader resolves a relative binding against the report's folder.

        So a relative path is not a convenience here, it is the correct form.
        """

        for relative, schema_id in TRACKED_REPORTS.items():
            with self.subTest(report=relative):
                report = _load(relative)
                binding = report["binding_artifact"]
                self.assertIsNotNone(binding, "{} declares no binding".format(relative))
                declared = Path(binding["path"])
                self.assertFalse(
                    declared.is_absolute(),
                    "{} binding path is absolute".format(relative),
                )
                resolved = ((ROOT / relative).parent / declared).resolve()
                self.assertTrue(
                    resolved.is_file(),
                    "{} binding does not resolve to {}".format(relative, resolved),
                )
                self.assertEqual(
                    _load(resolved.relative_to(ROOT).as_posix())["schema_id"], schema_id
                )

    def test_binding_artifacts_are_not_in_a_git_ignored_directory(self):
        """A binding excluded by .gitignore is absent from every fresh clone."""

        for relative in TRACKED_BINDINGS:
            with self.subTest(binding=relative):
                result = subprocess.run(
                    ["git", "check-ignore", relative],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                )
                # git check-ignore exits 0 when the path IS ignored.
                self.assertNotEqual(
                    result.returncode,
                    0,
                    "{} is git-ignored: {}".format(relative, result.stdout.strip()),
                )

    def test_weather_binding_declares_how_to_regenerate_its_derived_epw(self):
        """The EPW is deliberately not tracked, so the chain must say so.

        `.gitignore` excludes `generated_weather/` as regenerable derived
        output.  That is a valid convention only if the artifact names the
        command, instead of leaving a reviewer with a missing file.
        """

        binding = _load(
            "references/standards/sia2028/KLO_SIA2028_DRY_NORMAL.binding.json"
        )
        declared = binding["derived_artifact_not_in_repository"]
        self.assertIn("generated_weather", declared["why"])
        self.assertIn("KLO", declared["regenerate_with"])
        source = (
            ROOT / "references/standards/sia2028" / declared["source_of_truth"]
        ).resolve()
        self.assertTrue(source.is_file(), source)

    def test_iso_binding_producer_is_deterministic(self):
        """A reproducible artifact must rebuild byte-identically."""

        import scripts.build_iso52016_chapter7_binding as producteur

        source = str(ROOT / "config" / "iso52016_chapter7_confirmed_inputs.json")
        first = json.dumps(producteur.construire(source), sort_keys=True)
        second = json.dumps(producteur.construire(source), sort_keys=True)
        self.assertEqual(first, second)

        on_disk = _load("refs/reference-data/iso52016_chapter7_test_cell.binding.json")
        self.assertEqual(
            json.dumps(on_disk, sort_keys=True),
            first,
            "the committed ISO binding is not what its producer writes",
        )


if __name__ == "__main__":
    unittest.main()
