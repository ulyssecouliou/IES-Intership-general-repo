"""Tests for the source-traced Test 2A native VE profile adapter."""

import unittest

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.normalized_external_inputs import (
    NormalizedOfficeProfiles,
    NormalizedVeProfileGraph,
    NormalizedVeProfileNode,
)
from swiss_sia.reference_model.sia4010.test2a_profile_binding import (
    build_test2a_profile_definitions,
)


def _office_profiles(with_graph=True):
    graph = None
    if with_graph:
        graph = NormalizedVeProfileGraph(
            nodes=(
                NormalizedVeProfileNode(
                    key="daily",
                    profile_type="daily",
                    reference="SIA2024_DAY",
                    modulating=True,
                    units=-1,
                    data=((0.0, 0.0, ""), (24.0, 0.0, "")),
                    source_locator="authorized daily row",
                ),
                NormalizedVeProfileNode(
                    key="weekly",
                    profile_type="weekly",
                    reference="SIA2024_WEEK",
                    modulating=True,
                    units=-1,
                    data=tuple({"profile_ref": "daily"} for _ in range(7)),
                    source_locator="authorized weekday mapping",
                ),
                NormalizedVeProfileNode(
                    key="yearly",
                    profile_type="yearly",
                    reference="SIA2024_YEAR",
                    modulating=True,
                    units=-1,
                    data=(({"profile_ref": "weekly"}, 1, 365),),
                    source_locator="authorized annual mapping",
                ),
            ),
            outputs=(
                ("occupancy_profile", "yearly"),
                ("equipment_profile", "yearly"),
                ("lighting_profile", "yearly"),
            ),
            source_locator="authorized SIA 2024 calendar",
        )
    return NormalizedOfficeProfiles(
        use_category="authorized office category",
        value_set="authorized value set",
        calendar_basis="authorized 365-day calendar",
        annual_simultaneity_method="authorized method",
        profiles=(),
        source_locator="authorized SIA 2024 source",
        ve_profile_graph=graph,
    )


class Test2AProfileBindingTests(unittest.TestCase):
    """Only explicit native profile graphs become generic VE definitions."""

    def test_builds_exact_dependency_preserving_profile_definitions(self):
        bundle = build_test2a_profile_definitions(
            _office_profiles(),
            source_sha256="a" * 64,
        )

        self.assertEqual(
            tuple(item.key for item in bundle.definitions),
            ("daily", "weekly", "yearly"),
        )
        self.assertEqual(
            bundle.definitions[1].data.value,
            [{"profile_ref": "daily"}] * 7,
        )
        self.assertEqual(
            bundle.definitions[2].data.value,
            [[{"profile_ref": "weekly"}, 1, 365]],
        )
        self.assertEqual(
            dict(bundle.output_profile_keys)["occupancy_profile"],
            "yearly",
        )
        self.assertEqual(len(bundle.graph_sha256), 64)
        self.assertIn(
            "a" * 64,
            bundle.definitions[0].evidence.source,
        )

    def test_missing_native_graph_fails_before_ve(self):
        with self.assertRaisesRegex(
            ConfigurationError, "native VE profile graph is required"
        ):
            build_test2a_profile_definitions(
                _office_profiles(False),
                source_sha256="a" * 64,
            )

    def test_invalid_source_digest_is_rejected(self):
        with self.assertRaisesRegex(ConfigurationError, "SHA-256"):
            build_test2a_profile_definitions(
                _office_profiles(),
                source_sha256="not-a-checksum",
            )


if __name__ == "__main__":
    unittest.main()
