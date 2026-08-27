"""Tests for guarded, profile-only Test 2A runtime qualification."""

import json
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from swiss_sia.reference_model.exceptions import (
    ConfigurationError,
    VeMutationError,
)
from swiss_sia.reference_model.sia4010.normalized_external_inputs import (
    NormalizedOfficeProfiles,
    NormalizedVeProfileGraph,
    NormalizedVeProfileNode,
)
from swiss_sia.reference_model.sia4010.test2a_profile_qualification import (
    qualify_test2a_profile_graph,
)

ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "test2a_profile_qualification"


class _Profile:
    def __init__(self, identifier, reference, kind):
        self.id = identifier
        self.reference = reference
        self.kind = kind
        self.data = None

    def set_data(self, data):
        self.data = json.loads(json.dumps(data))
        return True

    def get_data(self):
        return self.data

    def is_weekly(self):
        return self.kind == "weekly"

    def is_yearly(self):
        return self.kind == "yearly"

    @staticmethod
    def is_compact():
        return False

    @staticmethod
    def is_freeform():
        return False


class _Project:
    def __init__(self, path):
        self.path = str(path)
        self.name = "DISPOSABLE_TEST2A"
        self._profiles = {}
        self.save_count = 0

    def profiles(self):
        return (dict(self._profiles), {})

    def create_profile(self, profile_type, reference, _modulating, _units):
        identifier = "PRO-{}".format(len(self._profiles) + 1)
        profile = _Profile(identifier, reference, profile_type)
        self._profiles[identifier] = profile
        return profile

    def save_profiles(self):
        self.save_count += 1
        return True


def _office_profiles():
    graph = NormalizedVeProfileGraph(
        nodes=(
            NormalizedVeProfileNode(
                key="day",
                profile_type="daily",
                reference="SIA2A_DAY",
                modulating=True,
                units=-1,
                data=((0.0, 0.0, ""), (24.0, 0.0, "")),
                source_locator="authorized day",
            ),
            NormalizedVeProfileNode(
                key="week",
                profile_type="weekly",
                reference="SIA2A_WEEK",
                modulating=True,
                units=-1,
                data=tuple({"profile_ref": "day"} for _ in range(12)),
                source_locator="authorized week",
            ),
            NormalizedVeProfileNode(
                key="year",
                profile_type="yearly",
                reference="SIA2A_YEAR",
                modulating=True,
                units=-1,
                data=(({"profile_ref": "week"}, 1, 365),),
                source_locator="authorized year",
            ),
        ),
        outputs=(
            ("occupancy_profile", "year"),
            ("equipment_profile", "year"),
            ("lighting_profile", "year"),
        ),
        source_locator="authorized graph",
    )
    return NormalizedOfficeProfiles(
        use_category="authorized category",
        value_set="authorized values",
        calendar_basis="authorized calendar",
        annual_simultaneity_method="authorized method",
        profiles=(),
        source_locator="authorized SIA 2024",
        ve_profile_graph=graph,
    )


def _scenario(variant="test_2A", case_id="2A"):
    return SimpleNamespace(
        is_official=True,
        variant=variant,
        case_id=case_id,
        to_dict=lambda: {
            "profile": "SIA4010_OFFICIAL",
            "selection": {"variant": variant, "case_id": case_id},
        },
    )


class Test2AProfileQualificationTests(unittest.TestCase):
    """The mutation boundary is narrow, collision-safe and auditable."""

    def setUp(self):
        self.project_path = WORK_ROOT / self._testMethodName
        if self.project_path.exists():
            shutil.rmtree(self.project_path)
        self.project_path.mkdir(parents=True)
        (self.project_path / "sia_model_scenario.json").write_text(
            '{"prepared": true}\n',
            encoding="utf-8",
        )
        self.project = _Project(self.project_path)

    def tearDown(self):
        if self.project_path.exists():
            shutil.rmtree(self.project_path)

    def _patches(self, scenario=None):
        bindings = SimpleNamespace(
            office_profiles=_office_profiles(),
            evidence_sha256=(
                ("iso52016_2017_chapter7_test_cell", "1" * 64),
                ("sia2028_dry_normal_zurich_kloten", "2" * 64),
                ("sia2024_office_3_1_standard_profiles", "3" * 64),
            ),
        )
        return (
            patch(
                "swiss_sia.reference_model.sia4010."
                "test2a_profile_qualification.ModelScenario.load",
                return_value=scenario or _scenario(),
            ),
            patch(
                "swiss_sia.reference_model.sia4010."
                "test2a_profile_qualification.external_input_readiness",
                return_value=SimpleNamespace(),
            ),
            patch(
                "swiss_sia.reference_model.sia4010."
                "test2a_profile_qualification.load_test2a_external_bindings",
                return_value=bindings,
            ),
        )

    def test_qualifies_daily_weekly_yearly_and_writes_checksum(self):
        first, second, third = self._patches()
        with first, second, third:
            report = qualify_test2a_profile_graph(
                SimpleNamespace(),
                self.project,
            )

        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["created_profile_count"], 3)
        self.assertEqual(
            payload["output_profile_ids"],
            {
                "occupancy_profile": "PRO-3",
                "equipment_profile": "PRO-3",
                "lighting_profile": "PRO-3",
            },
        )
        self.assertEqual(self.project.save_count, 3)
        self.assertTrue(report.with_suffix(report.suffix + ".sha256").is_file())

    def test_repeat_fails_on_collision_without_new_profile(self):
        patches = self._patches()
        with patches[0], patches[1], patches[2]:
            qualify_test2a_profile_graph(SimpleNamespace(), self.project)
        patches = self._patches()
        with patches[0], patches[1], patches[2]:
            with self.assertRaisesRegex(VeMutationError, "Profile already exists"):
                qualify_test2a_profile_graph(
                    SimpleNamespace(),
                    self.project,
                )
        self.assertEqual(len(self.project._profiles), 3)

    def test_wrong_scenario_fails_before_profile_creation(self):
        first, second, third = self._patches(scenario=_scenario("test_2B", "2B"))
        with first, second, third:
            with self.assertRaisesRegex(
                ConfigurationError, "restricted to the official test_2A/2A"
            ):
                qualify_test2a_profile_graph(
                    SimpleNamespace(),
                    self.project,
                )
        self.assertEqual(self.project._profiles, {})


if __name__ == "__main__":
    unittest.main()
