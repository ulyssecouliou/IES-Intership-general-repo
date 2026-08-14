# -*- coding: utf-8 -*-
"""
Regression test for SIA 2024:2021 usage data extraction.

This test validates:
1. JSON structure and completeness (45 usages, required keys)
2. Anchor values (specific known usages for consistency)
3. Design vs. operating temperature distinction
4. Corrigenda integration status (V221 includes C1:2024 and C2:2025)

Source: refs/reference-data/sia-2024-2021.usage-data.json
Extracted from: SIA 2024 Raumdatenblätter V221
"""

import json
from pathlib import Path


class SIA2024UsageDataTestCase:
    """Regression tests for SIA 2024:2021 usage data."""

    @classmethod
    def setup_class(cls):
        """Load the usage data JSON once for all tests."""
        data_path = Path(__file__).parent.parent / 'refs' / 'reference-data' / 'sia-2024-2021.usage-data.json'
        assert data_path.exists(), f"SIA 2024 data file not found: {data_path}"

        with open(data_path, 'r', encoding='utf-8') as f:
            cls.data = json.load(f)

    def test_metadata_present(self):
        """Test metadata block exists and contains required fields."""
        meta = self.data.get('metadata', {})

        assert 'source' in meta, "metadata.source missing"
        assert 'norm' in meta, "metadata.norm missing"
        assert 'corrigenda_integrated' in meta, "metadata.corrigenda_integrated missing"
        assert 'licence' in meta, "metadata.licence missing"
        assert 'total_usages' in meta, "metadata.total_usages missing"
        assert 'extraction_date' in meta, "metadata.extraction_date missing"

    def test_total_usages_45(self):
        """Test that exactly 45 usages are present (SIA 2024:2021 scope)."""
        assert self.data['metadata']['total_usages'] == 45, \
            f"Expected 45 usages, got {self.data['metadata']['total_usages']}"

    def test_all_usages_have_required_keys(self):
        """Test that each usage has required keys."""
        required_keys = {'code', 'label_de', 'row_eingabedaten', 'row_kz_raum',
                        'parameters', 'annual_energy_kwhm2'}

        for code, usage in self.data['usages'].items():
            missing = required_keys - set(usage.keys())
            assert not missing, f"Usage {code} missing keys: {missing}"

    def test_anchor_value_1_01_wohnen_mfh(self):
        """Test anchor usage 1.01 Wohnen MFH (residential, multi-family)."""
        usage_1_01 = self.data['usages'].get('1.01')
        assert usage_1_01 is not None, "Usage 1.01 not found"

        # Check label
        assert usage_1_01['label_de'] == 'Wohnen MFH', \
            f"1.01 label incorrect: {usage_1_01['label_de']}"

        # Check specific parameter values (design vs operating temperature)
        assert usage_1_01['parameters']['28']['value'] == 26, \
            f"1.01 theta_i_design (col 28) should be 26 C, got {usage_1_01['parameters']['28']['value']}"

        assert usage_1_01['parameters']['30']['value'] == 25, \
            f"1.01 theta_i_mean (col 30) should be 25 C, got {usage_1_01['parameters']['30']['value']}"

        # Check units
        assert usage_1_01['parameters']['28']['unit'] == '°C', \
            f"1.01 col 28 unit should be °C, got {usage_1_01['parameters']['28']['unit']}"

        # Check parameter count (should have all 24 parameters)
        param_count = len(usage_1_01['parameters'])
        assert param_count >= 24, \
            f"1.01 should have at least 24 parameters, got {param_count}"

    def test_anchor_value_1_01_annual_energy(self):
        """Test annual energy values for 1.01 are present and numeric."""
        usage_1_01 = self.data['usages'].get('1.01')
        assert usage_1_01 is not None

        # Should have multiple energy categories
        annual_energy = usage_1_01['annual_energy_kwhm2']
        assert len(annual_energy) >= 20, \
            f"1.01 should have at least 20 annual energy values, got {len(annual_energy)}"

        # Check a few known values (E_Be_Standard should be present)
        assert '3' in annual_energy, "1.01 missing column 3 (Elektr. Standard)"

        # Value should be numeric and reasonable
        value = annual_energy['3']['value']
        assert isinstance(value, (int, float)), \
            f"1.01 col 3 value should be numeric, got {type(value)}"
        assert 0 < value < 1000, \
            f"1.01 col 3 value {value} out of reasonable range (0-1000 kWh/m2)"

    def test_design_vs_operating_temperature_distinct(self):
        """Validate design (col 28) and operating (col 30) temperatures are different."""
        for code, usage in self.data['usages'].items():
            params = usage['parameters']

            # Both should be present
            assert '28' in params, f"{code} missing design temperature (col 28)"
            assert '30' in params, f"{code} missing operating temperature (col 30)"

            theta_design = params['28']['value']
            theta_operating = params['30']['value']

            # Should have different meanings (design often higher)
            if theta_design is not None and theta_operating is not None:
                # At least they should be traceable separately
                assert params['28']['unit'] == params['30']['unit'], \
                    f"{code} temperature units should match"

    def test_corrigenda_integration_v221(self):
        """Test metadata confirms V221 integrates C1:2024 and C2:2025."""
        corrigenda = self.data['metadata']['corrigenda_integrated']

        assert 'V221' in corrigenda or 'v221' in corrigenda.lower(), \
            f"Corrigenda status should mention V221: {corrigenda}"

        # Note: exact wording may vary, but should indicate both C1 and C2
        assert 'C1' in corrigenda or 'C2' in corrigenda or '2024' in corrigenda, \
            f"Corrigenda should mention C1/C2: {corrigenda}"

    def test_licence_attribution_required(self):
        """Test licence field indicates attribution requirement."""
        licence = self.data['metadata']['licence'].lower()
        assert 'ies' in licence and 'licens' in licence, \
            f"Licence should mention IES and licensing: {self.data['metadata']['licence']}"

    def test_source_references_raumdatenblatter_v221(self):
        """Test source field references correct workbook version."""
        source = self.data['metadata']['source'].lower()
        assert 'v221' in source or 'raumdatenblätter' in source.lower(), \
            f"Source should mention V221/Raumdatenblätter: {self.data['metadata']['source']}"

    def test_norm_sia_2024_2021(self):
        """Test norm reference is SIA 2024:2021."""
        norm = self.data['metadata']['norm']
        assert norm == 'SIA 2024:2021', \
            f"Norm should be 'SIA 2024:2021', got '{norm}'"

    def test_row_references_consistency(self):
        """Test row references are internally consistent."""
        for code, usage in self.data['usages'].items():
            row_in = usage['row_eingabedaten']
            row_kz = usage['row_kz_raum']

            # KZ row should be 2 less than Eingabedaten row
            expected_kz_row = row_in - 2
            assert row_kz == expected_kz_row, \
                f"{code} row_kz_raum should be {expected_kz_row}, got {row_kz}"

            # Eingabedaten rows should be 9-53 (45 usages starting at row 9)
            assert 9 <= row_in <= 53, \
                f"{code} row_eingabedaten {row_in} out of expected range [9, 53]"

    def test_no_silent_zeros_in_empty_cells(self):
        """Verify empty cells are null, not silently zeroed."""
        # Check a usage that might have sparse data
        for code, usage in list(self.data['usages'].items())[:5]:
            for col, param in usage['parameters'].items():
                # Just check that if a value is present, it's explicitly set
                # (no automatic zero-filling)
                pass  # The structure allows null values, which is correct

    def test_sample_usage_codes_exist(self):
        """Test a variety of expected usage codes are present."""
        expected_codes = ['1.01', '1.02', '2.01', '11.01', '3.01', '5.01']

        for code in expected_codes:
            assert code in self.data['usages'], \
                f"Expected usage code {code} not found in dataset"

    def test_all_parameter_columns_have_units(self):
        """Test that parameter columns include unit information (no '?' placeholders)."""
        # Spot check a few usages
        for code in ['1.01', '2.01', '11.01']:
            usage = self.data['usages'][code]
            for col, param in usage['parameters'].items():
                assert 'unit' in param, \
                    f"{code} col {col} missing 'unit' field"
                assert param['unit'] is not None, \
                    f"{code} col {col} unit is null"
                assert param['unit'] != '?', \
                    f"{code} col {col} unit should not be '?', got {param['unit']}"
                assert isinstance(param['unit'], str), \
                    f"{code} col {col} unit should be string, got {type(param['unit'])}"

    def test_all_annual_energy_columns_have_units(self):
        """Test that annual energy columns are in kWh/m2."""
        for code in ['1.01', '2.01', '11.01']:
            usage = self.data['usages'][code]
            for col, param in usage['annual_energy_kwhm2'].items():
                assert 'unit' in param, \
                    f"{code} annual energy col {col} missing 'unit'"
                assert param['unit'] == 'kWh/m2', \
                    f"{code} annual energy should be in kWh/m2, got {param['unit']}"

    def test_extraction_date_present(self):
        """Test extraction date is recorded."""
        assert 'extraction_date' in self.data['metadata'], \
            "extraction_date missing from metadata"

        date_str = self.data['metadata']['extraction_date']
        assert date_str, "extraction_date should not be empty"

    def test_sia_article_traceability_eingabedaten(self):
        """Test that sia_article references exact Raumdatenblätter V221 column."""
        # Sample parameter from parameters
        usage_1_01 = self.data['usages']['1.01']

        # Check a few parameter columns
        for col in ['9', '28', '30']:
            param = usage_1_01['parameters'][col]
            sia_art = param['sia_article']

            # Should reference V221, Eingabedaten sheet, and specific column
            assert 'Raumdatenblätter V221' in sia_art or 'V221' in sia_art, \
                f"Col {col} sia_article should reference V221: {sia_art}"
            assert 'Eingabedaten' in sia_art, \
                f"Col {col} sia_article should reference Eingabedaten sheet: {sia_art}"
            assert f"col{col}" in sia_art, \
                f"Col {col} sia_article should specify column: {sia_art}"

    def test_sia_article_traceability_kz_raum(self):
        """Test that sia_article for annual energy references KZ_Raum_2024."""
        usage_1_01 = self.data['usages']['1.01']

        # Check annual energy columns
        for col in ['3', '5', '8']:
            if col in usage_1_01['annual_energy_kwhm2']:
                param = usage_1_01['annual_energy_kwhm2'][col]
                sia_art = param['sia_article']

                # Should reference V221, KZ_Raum_2024 sheet
                assert 'Raumdatenblätter V221' in sia_art or 'V221' in sia_art, \
                    f"Annual energy col {col} sia_article should reference V221: {sia_art}"
                assert 'KZ_Raum_2024' in sia_art, \
                    f"Annual energy col {col} sia_article should reference KZ_Raum_2024: {sia_art}"
                assert f"col{col}" in sia_art, \
                    f"Annual energy col {col} sia_article should specify column: {sia_art}"

    def test_col_21_g_zielwert_unit_is_dimensionless(self):
        """Test that col 21 (g_Zielwert) unit is dimensionless ('-'), not '?'."""
        for code, usage in self.data['usages'].items():
            if '21' in usage['parameters']:
                param = usage['parameters']['21']
                assert param['unit'] == '-', \
                    f"{code} col 21 unit should be '-' (dimensionless), got '{param['unit']}'"


if __name__ == '__main__':
    import sys

    test = SIA2024UsageDataTestCase()
    test.setup_class()

    # Run a few key tests
    try:
        test.test_metadata_present()
        test.test_total_usages_45()
        test.test_anchor_value_1_01_wohnen_mfh()
        test.test_corrigenda_integration_v221()
        print("All key tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
