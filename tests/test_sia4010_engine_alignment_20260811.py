# -*- coding: utf-8 -*-
"""Regression tests locking in the SIA workbook + authority alignment.

These tests are attached to the alignment note
``docs/project/SIA4010_ENGINE_ALIGNMENT_2026-08-11.md`` and back its claims
by direct assertions.  They cover:

* Test 7 corrected workbook: conditional-formatting rule uses lower/upper
  bounds ($N8, $M8), the ``Zusammenfassung`` header uses the German verbatim
  ``Mittelwert / Obere Grenze / Untere Grenze`` and the frozen reference
  matches the imported workbook via SHA-256.
* Distribution engine: envelope min/max is the binding reading (a candidate
  outside the envelope FAILS even when inside the symmetric band).
* Distribution engine: out-of-class hours are preserved and never absorbed
  silently into the last class.
* Test 1: the six normative cases (600, 640, 900, 940, 600FF, 900FF) remain
  informative-only; only 1E carries a pass/fail criterion.  The engine must
  never invent a tolerance for the six normative cases.

Openpyxl is required for the workbook probes and skipped when unavailable.
"""

from __future__ import annotations

import hashlib
import json
import os
import unittest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEST7_WORKBOOK = os.path.join(
    REPO_ROOT,
    "SIA_4010_geteilter_Link",
    "Test7",
    "Resultaterfassung Test7.xlsx",
)
TEST7_REF = os.path.join(REPO_ROOT, "refs", "reference-data", "test-7.ref.json")

# Frozen SHA-256 of the corrected Test 7 workbook confirmed by the
# 2026-08-10 audit and re-verified on 2026-08-11.
TEST7_WORKBOOK_SHA256 = (
    "24937d8f421daa74a7f957025bfeb17a42fe2dc807b1a301a6752f4c0e808958"
)


try:
    import openpyxl  # noqa: F401
    _OPENPYXL_AVAILABLE = True
except Exception:  # pragma: no cover
    _OPENPYXL_AVAILABLE = False


def _sha256(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


class Test7CorrectedWorkbookIntegrityTests(unittest.TestCase):

    def test_workbook_sha256_matches_frozen_audit(self) -> None:
        if not os.path.exists(TEST7_WORKBOOK):
            self.skipTest("Corrected Test 7 workbook missing")
        self.assertEqual(_sha256(TEST7_WORKBOOK), TEST7_WORKBOOK_SHA256)

    def test_reference_json_pins_corrected_workbook(self) -> None:
        if not os.path.exists(TEST7_REF):
            self.skipTest("Frozen Test 7 reference missing")
        with open(TEST7_REF, encoding="utf-8") as handle:
            ref = json.load(handle)
        source = ref.get("source", {})
        self.assertEqual(
            source.get("sha256"),
            TEST7_WORKBOOK_SHA256,
            msg="test-7.ref.json is not pinned to the corrected workbook",
        )
        self.assertIn(
            "borne basse",
            (source.get("correction") or "").lower(),
        )

    @unittest.skipUnless(_OPENPYXL_AVAILABLE, "openpyxl unavailable")
    def test_zusammenfassung_conditional_formatting_uses_lower_upper(self) -> None:
        if not os.path.exists(TEST7_WORKBOOK):
            self.skipTest("Test 7 workbook missing")
        wb = openpyxl.load_workbook(TEST7_WORKBOOK, data_only=False)
        ws = wb["Zusammenfassung"]
        # Header verbatim (row 7): L=Mittelwert, M=Obere Grenze, N=Untere Grenze
        self.assertEqual(ws["L7"].value, "Mittelwert")
        self.assertEqual(ws["M7"].value, "Obere Grenze")
        self.assertEqual(ws["N7"].value, "Untere Grenze")
        # Conditional-formatting rule uses $N8 (lower) to $M8 (upper)
        found = False
        for rng, rules in ws.conditional_formatting._cf_rules.items():
            if str(rng.sqref) != "F8:F12 F14:F18 F20":
                continue
            for rule in rules:
                formulas = list(getattr(rule, "formula", []) or [])
                if formulas == ["$N8", "$M8"]:
                    self.assertEqual(getattr(rule, "operator", None), "between")
                    found = True
                    break
        self.assertTrue(
            found,
            msg=(
                "Corrected Test 7 rule must be between $N8 (lower) and $M8 "
                "(upper) on F8:F12 F14:F18 F20"
            ),
        )


class DistributionEngineEnvelopeBindingTests(unittest.TestCase):
    """Envelope min/max is the binding Streubereich reading (2026-08-10)."""

    def _make_bloc(self):
        # Two reference contributors G and H, one bin, envelope [10, 30].
        # Symmetric mean+/-max_dev = [10-10, 10+10] = actually mean=20, max_dev=10
        # -> lower=10, upper=30 -- coincides here so envelope==band.
        # To distinguish, we add a third contributor that pulls the mean and
        # widens the symmetric band beyond the envelope.
        return {
            "cas": "TESTCASE",
            "grandeur": "GrX",
            "unite": "-",
            "colonne_bloc": "Q",
            "contributeurs": [
                {"colonne": "G", "total_heures": 8760},
                {"colonne": "H", "total_heures": 8760},
                {"colonne": "I", "total_heures": 8760},
            ],
            "effectifs": [
                {
                    "borne_superieure": 100.0,
                    "ligne_classeur": 10,
                    "par_colonne": {"G": 10, "H": 30, "I": 40},
                }
            ],
        }

    def test_candidate_outside_envelope_fails_even_inside_symmetric_band(self) -> None:
        from engine import sia_distributions_engine as dist

        bloc = self._make_bloc()
        # Envelope = [10, 40]; mean = 80/3 ~ 26.67; max_dev = ~13.33;
        # symmetric band ~ [13.33, 40.0]. A candidate of 41 is outside the
        # envelope AND outside the band -> FAIL. A candidate of 42 is outside
        # both. Pick 41.
        # But we need to demonstrate the ENVELOPE is binding, so pick a value
        # inside the symmetric band but outside the envelope. With
        # {10, 30, 40}, band=[13.33..40], envelope=[10..40]; here envelope
        # matches band on the upper edge. Rebuild with {10, 20, 40} => mean=23.33,
        # max_dev=16.67, band=[6.67, 40], envelope=[10,40]. Candidate=8 sits
        # inside band but OUTSIDE envelope.
        bloc["effectifs"][0]["par_colonne"] = {"G": 10, "H": 20, "I": 40}
        result = dist.evaluer_bloc(bloc, effectifs_candidats=[8])
        self.assertEqual(result["verdict"], dist.VERDICT_FAIL)
        self.assertEqual(
            result["nb_hors_lecture"][dist.LECTURE_ENVELOPPE],
            1,
            msg="Envelope reading must catch a candidate below the min",
        )
        # The symmetric-band reading is retained for audit only and is not
        # required to also flag this candidate as FAIL for the verdict to be
        # FAIL: envelope is binding.
        self.assertIn(dist.LECTURE_BANDE, result["nb_hors_lecture"])

    def test_candidate_inside_envelope_passes(self) -> None:
        from engine import sia_distributions_engine as dist

        bloc = self._make_bloc()
        bloc["effectifs"][0]["par_colonne"] = {"G": 10, "H": 20, "I": 40}
        result = dist.evaluer_bloc(bloc, effectifs_candidats=[25])
        self.assertEqual(result["verdict"], dist.VERDICT_PASS)
        self.assertEqual(result["nb_hors_lecture"][dist.LECTURE_ENVELOPPE], 0)


class OutOfClassCounterTests(unittest.TestCase):
    """The 8760-total displayed by the workbook is not the whole story."""

    def test_classer_avec_hors_classes_reports_upper_bound_excedents(self) -> None:
        from engine import sia_distributions_engine as dist

        serie = [-5, 5, 10, 15, 20, 25, 30, 35, 40]  # 9 values
        bornes = (10.0, 20.0, 30.0)  # last bin: values up to 30
        outcome = dist.classer_avec_hors_classes(serie, bornes)
        self.assertEqual(outcome["total_numerique"], 9)
        self.assertEqual(
            sum(outcome["effectifs"]),
            7,  # -5, 5, 10 -> bin0; 15, 20 -> bin1; 25, 30 -> bin2
            msg="Values inside declared classes must total the effectifs sum",
        )
        self.assertEqual(
            outcome["hors_classes_superieur"],
            2,
            msg="Values 35 and 40 exceed the last upper bound and are counted separately",
        )

    def test_classer_never_absorbs_out_of_range_into_last_bin(self) -> None:
        from engine import sia_distributions_engine as dist

        effectifs = dist.classer([-5, 5, 100], (10.0, 20.0, 30.0))
        # -5 fits bin 0, 5 fits bin 0, 100 is out-of-range (NOT bin 2).
        self.assertEqual(effectifs, [2, 0, 0])


class Test1SixNormativeCasesRemainInformativeTests(unittest.TestCase):
    """No tolerance may be invented for the six normative Test 1 cases."""

    def test_only_1e_carries_criterion(self) -> None:
        from engine import test1_engine

        self.assertEqual(test1_engine.CAS_AVEC_CRITERE, ("1E",))

    def test_six_normative_cases_absent_from_criterion_set(self) -> None:
        from engine import test1_engine

        for cas in ("600", "640", "900", "940", "600FF", "900FF"):
            self.assertNotIn(
                cas,
                test1_engine.CAS_AVEC_CRITERE,
                msg="Case {} must remain informative-only".format(cas),
            )


if __name__ == "__main__":
    unittest.main()
