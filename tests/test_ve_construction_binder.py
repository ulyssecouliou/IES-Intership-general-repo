"""Unit tests for ``ve_construction_binder``.

The binder is proven with two fake CDB projects: one exposing only the
single-arg ``get_construction(id)``, and one exposing the two-arg
``get_construction(id, construction_class)`` variant.  A third fake proves
the fail-closed path.
"""

import unittest
from types import SimpleNamespace

from swiss_sia.reference_model.ve_construction_binder import (
    BindStatus,
    ConstructionBinder,
)


class _SingleArgCdb:
    def __init__(self, mapping):
        self._mapping = mapping
        # Deliberately no ``uvalue_types`` attribute -> forces single-arg path.

    def get_construction(self, ident):
        if not isinstance(ident, str):
            raise TypeError("expected str")
        return self._mapping.get(ident)


class _TwoArgCdb:
    def __init__(self, mapping):
        self._mapping = mapping
        self.uvalue_types = SimpleNamespace(iso=object())

    def get_construction(self, ident, construction_class):
        if construction_class is not self.uvalue_types.iso:
            raise ValueError("wrong construction class")
        return self._mapping.get(ident)


class _AlwaysRaisesCdb:
    def get_construction(self, *args, **kwargs):
        raise RuntimeError("VE side error")


class ConstructionBinderTests(unittest.TestCase):

    def test_single_arg_signature_resolves(self) -> None:
        obj = object()
        cdb = _SingleArgCdb({"WALL_A": obj})
        binder = ConstructionBinder(iesve_module=SimpleNamespace(), cdb_project=cdb)
        result = binder.resolve("WALL_A")
        self.assertEqual(result.status, BindStatus.RESOLVED)
        self.assertIs(result.construction, obj)
        self.assertIn("get_construction(id)", result.signatures_tried)

    def test_two_arg_signature_resolves(self) -> None:
        obj = object()
        cdb = _TwoArgCdb({"WALL_A": obj})
        binder = ConstructionBinder(iesve_module=SimpleNamespace(), cdb_project=cdb)
        result = binder.resolve("WALL_A")
        self.assertEqual(result.status, BindStatus.RESOLVED)
        self.assertIs(result.construction, obj)
        self.assertIn(
            "get_construction(id, construction_class)", result.signatures_tried
        )

    def test_missing_construction_is_not_found(self) -> None:
        cdb = _SingleArgCdb({})
        binder = ConstructionBinder(iesve_module=SimpleNamespace(), cdb_project=cdb)
        result = binder.resolve("NOPE")
        self.assertEqual(result.status, BindStatus.NOT_FOUND)
        self.assertIsNone(result.construction)

    def test_missing_get_construction_attr_yields_runtime_unavailable(self) -> None:
        cdb = SimpleNamespace()  # no get_construction attr at all
        binder = ConstructionBinder(iesve_module=SimpleNamespace(), cdb_project=cdb)
        result = binder.resolve("ANY")
        self.assertEqual(result.status, BindStatus.RUNTIME_UNAVAILABLE)

    def test_all_variants_raise_records_last_exception(self) -> None:
        cdb = _AlwaysRaisesCdb()
        cdb.uvalue_types = SimpleNamespace(iso=object())
        binder = ConstructionBinder(iesve_module=SimpleNamespace(), cdb_project=cdb)
        result = binder.resolve("WALL_A")
        self.assertEqual(result.status, BindStatus.NOT_FOUND)
        self.assertIn("VE side error", result.last_exception_repr)
        # Both attempts were tried.
        self.assertEqual(len(result.signatures_tried), 2)

    def test_non_str_identifier_raises_type_error(self) -> None:
        cdb = _SingleArgCdb({})
        binder = ConstructionBinder(iesve_module=SimpleNamespace(), cdb_project=cdb)
        with self.assertRaises(TypeError):
            binder.resolve(42)  # type: ignore[arg-type]

    def test_resolve_or_raise_raises_lookup_error_on_miss(self) -> None:
        cdb = _SingleArgCdb({})
        binder = ConstructionBinder(iesve_module=SimpleNamespace(), cdb_project=cdb)
        with self.assertRaises(LookupError):
            binder.resolve_or_raise("NOPE")


if __name__ == "__main__":
    unittest.main()
