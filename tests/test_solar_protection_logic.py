"""Regression tests for active solar-protection and g-total applicability."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from swiss_sia.excel_report import ExcelReportGenerator
from swiss_sia.model_analyzer import OpeningData, RoomData, has_active_solar_protection
from swiss_sia.rule_engine import RuleEngine
from swiss_sia.sia380_checker import SIA3802Checker


class SolarProtectionLogicTests(unittest.TestCase):
    """Ensure disabled CDB shade fields never create a false evidence requirement."""

    @staticmethod
    def _opening(*, active: bool) -> OpeningData:
        """Return a complete window with explicit VE shade activation fields."""
        return OpeningData(
            id="window-1",
            name="Reference window",
            area=3.15,
            u_value=0.613825,
            solar_factor=0.526887774,
            solar_factor_source="properties.g_values.bs_en_410",
            cdb_g_value=0.75,
            g_value_bs_en_410=0.526887774,
            visible_transmittance=0.65,
            frame_fraction=0.10,
            shading_type="external fabric" if active else "none declared in CDB",
            shading_control="irradiance profile" if active else "none declared in CDB",
            shading_properties={
                "external_shade_active": 1 if active else 0,
                "internal_shade_active": 0,
                "local_shade_active": 0,
            },
            g_total=None,
            opening_type="window",
            is_external=True,
            construction_id="STD_EXT2",
        )

    @staticmethod
    def _check(opening: OpeningData) -> set[str]:
        """Run the opening checks and return all emitted rule identifiers."""
        analyzer = Mock()
        analyzer._normalize_opening_type.return_value = "window"
        analyzer.calculate_wwr.return_value = 0.30
        engine = RuleEngine()
        checker = SIA3802Checker(analyzer, engine)
        checker._check_openings([RoomData(id="room-1", openings=[opening])])
        return {alert.rule for alert in engine.alerts}

    def test_zero_activation_fields_mean_no_active_solar_protection(self) -> None:
        """Treat numeric zero and explicit no-shading labels as disabled."""
        opening = self._opening(active=False)

        self.assertFalse(has_active_solar_protection(opening))
        rules = self._check(opening)
        self.assertNotIn("SIA3802_G_TOTAL_WITH_SHADING_MISSING", rules)
        self.assertNotIn("SIA3802_SOLAR_PROTECTION_TYPE_MISSING", rules)
        self.assertNotIn("SIA3802_SOLAR_PROTECTION_CONTROL_MISSING", rules)
        self.assertEqual(
            ExcelReportGenerator._g_total_status(
                opening.solar_factor,
                opening.g_total,
                0,
                "PROVES_CDB_G_IS_NOT_EN410",
            ),
            "BASE_G_ABOVE_REFERENCE_NO_ACTIVE_SHADING",
        )

    def test_active_protection_requires_reviewed_g_total(self) -> None:
        """Require g-total evidence when an active device is present above 0.50."""
        opening = self._opening(active=True)

        self.assertTrue(has_active_solar_protection(opening))
        self.assertIn("SIA3802_G_TOTAL_WITH_SHADING_MISSING", self._check(opening))
        self.assertEqual(
            ExcelReportGenerator._g_total_status(
                opening.solar_factor,
                opening.g_total,
                1,
                "PROVES_CDB_G_IS_NOT_EN410",
            ),
            "CALCULATION_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
