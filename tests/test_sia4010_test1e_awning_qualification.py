"""Narrow tests for Test 1E target and native construction-ID handling."""

from types import SimpleNamespace

from swiss_sia.reference_model.sia4010.test1e_awning_qualification import (
    EXPECTED_OPENING_IDS,
    PROVISIONAL_ANGULAR_TRANSMITTANCE_PLAN,
    _live_targets,
)


class _Opening:
    def __init__(self, identifier):
        self.identifier = identifier

    def get_id(self):
        return self.identifier

    def get_properties(self):
        return {"area": 6.0}

    def get_construction(self):
        return "EXTW"


class _Surface:
    def get_properties(self):
        return {"orientation": 180.0}

    def get_openings(self):
        return [_Opening(identifier) for identifier in EXPECTED_OPENING_IDS]


class _Body:
    def get_surfaces(self):
        return [_Surface()]


def test_live_targets_resolve_string_construction_ids_to_cdb_objects():
    construction = SimpleNamespace(get_properties=lambda: {})
    gateway = SimpleNamespace(
        model=SimpleNamespace(get_bodies=lambda _include_holes: [_Body()]),
        _construction_identifier=lambda value: str(value),
        _get_construction=lambda identifier: (
            construction if identifier == "EXTW" else None
        ),
    )
    targets = _live_targets(gateway)
    assert len(targets) == 2
    assert {target["construction_id"] for target in targets} == {"EXTW"}
    assert all(target["construction"] is construction for target in targets)


def test_provisional_angular_plan_covers_every_15_degree_increment():
    assert tuple(PROVISIONAL_ANGULAR_TRANSMITTANCE_PLAN.values()) == (
        0.04,
        0.04,
        0.04,
        0.04,
        0.04,
        0.04,
        0.0,
    )
    assert "external_shade_transmitance_15" in PROVISIONAL_ANGULAR_TRANSMITTANCE_PLAN
    assert "external_shade_transmitance_75" in PROVISIONAL_ANGULAR_TRANSMITTANCE_PLAN
