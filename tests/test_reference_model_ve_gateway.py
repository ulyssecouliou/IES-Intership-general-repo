"""Fake-``iesve`` unit tests for the production ``IesVeGateway``.

These exercise the real gateway mutation/read-back logic outside VE by injecting
a pure-Python fake ``iesve`` module. They cover the capability gate (M2), the
tolerant ``get_construction`` resolution (M3), the ``get_version`` guard (L4),
the post-adjacency construction re-verification (M1), and the negative paths
(missing capability, read-back mismatch, unreadable weather). A fake never
proves real-runtime support; it proves the gateway's own control flow.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from swiss_sia.reference_model.compliance_config import build_default_registry
from swiss_sia.reference_model.exceptions import VeApiUnavailableError, VeMutationError
from swiss_sia.reference_model.ve_api import IesVeGateway

# Distinct sentinel objects for VE enum members.
_ROOM = object()
_CLASS_NONE = object()
_UVALUE_ISO = object()
_MAT_ALL = object()
_CAP_NONE = object()


def _expected_geometry(names):
    """Return a minimal object exposing generated space names."""

    return SimpleNamespace(spaces=[SimpleNamespace(name=name) for name in names])


def _configured_parameters():
    """Return a registry with all existing-mode inputs resolved with provenance."""

    def prov(value, locator):
        return {
            "value": value,
            "source": "Unit-test approved input",
            "source_locator": locator,
        }

    return build_default_registry().with_overrides(
        {
            "external_wall_construction_id": prov("EXTW", "T-1"),
            "roof_construction_id": prov("ROOF", "T-2"),
            "ground_floor_construction_id": prov("GRND", "T-3"),
            "internal_wall_construction_id": prov("INTW", "T-4"),
            "door_construction_id": prov("DOOR", "T-5"),
            "glazing_construction_id": prov("GLAZ", "T-6"),
            "weather_file": prov("C:/wx/test.fwt", "T-7"),
            "thermal_template_name": prov("TEST TEMPLATE", "T-8"),
            "thermal_template_source_record": prov("checksum:abc", "T-9"),
        }
    )


class _Surface:
    def __init__(self, index, surface_type, openings=None):
        self.index = index
        self.type = surface_type
        self._openings = openings or []
        self._constructions = []
        self.persist = True

    def get_properties(self):
        return {"type": self.type, "id": "S{}".format(self.index), "area": 10.0}

    def get_constructions(self):
        return list(self._constructions)

    def get_openings(self):
        return list(self._openings)

    def get_adjacencies(self):
        return []

    def _assign(self, construction_id):
        if self.persist:
            self._constructions = [construction_id]


class _Opening:
    def __init__(self, opening_id, opening_type):
        self._id = opening_id
        self.type = opening_type
        self._construction = ""
        self.persist = True

    def get_properties(self):
        return {"type": self.type, "area": 2.0}

    def get_id(self):
        return self._id

    def get_construction(self):
        return self._construction

    def _assign(self, construction_id):
        if self.persist:
            self._construction = construction_id


class _RoomData:
    def __init__(self):
        self._general = {"thermal_template": "TEST TEMPLATE"}
        self._apache = {"HVAC_system": ""}
        self._gains = []
        self._air_exchanges = []

    def get_general(self):
        return dict(self._general)

    def get_apache_systems(self):
        return dict(self._apache)

    def set_apache_systems(self, data):
        payload = dict(data)
        if "system_air_minimum_flowrate_units" in payload:
            payload["system_air_minimum_flowrate_unit"] = payload.pop(
                "system_air_minimum_flowrate_units"
            )
        self._apache.update(payload)

    def get_internal_gains(self):
        return list(self._gains)

    def get_air_exchanges(self):
        return list(self._air_exchanges)


class _MutableGain:
    """Minimal room-gain fake implementing VE's scalar-set/plural-get shape."""

    def __init__(self, data):
        self._data = dict(data)

    def get(self):
        return dict(self._data)

    def set(self, payload):
        self._data.update(
            {
                key: value
                for key, value in payload.items()
                if not key.startswith("max_")
                and key != "occupancy_density"
            }
        )
        units = int(payload.get("units_val", self._data.get("units_val", 0)))
        mapping = {
            "max_power_consumption": "max_power_consumptions",
            "max_sensible_gain": "max_sensible_gains",
            "max_latent_gain": "max_latent_gains",
            "occupancy_density": "occupancies",
        }
        for scalar, plural in mapping.items():
            if scalar in payload:
                values = dict(self._data.get(plural, {}))
                values[units] = payload[scalar]
                self._data[plural] = values
        for plural in mapping.values():
            if plural in payload:
                self._data[plural] = dict(payload[plural])


class _IsolatedScalarLatentGain(_MutableGain):
    """VE 2025 shape that resets latent in a multi-field payload."""

    def set(self, payload):
        scalar_filtered = dict(payload)
        if len(payload) > 1:
            scalar_filtered.pop("max_latent_gain", None)
        super().set(scalar_filtered)


class _Body:
    def __init__(self, iesve, name, body_id, surfaces):
        self._iesve = iesve
        self.name = name
        self.id = body_id
        self.type = _ROOM
        self._surfaces = surfaces
        self._room_data = _RoomData()

    def get_surfaces(self):
        return list(self._surfaces)

    def get_room_data(self):
        return self._room_data

    def get_areas(self):
        return {"int_floor_area": 10.0, "ext_floor_area": 0.0, "volume": 25.0}

    def assign_construction(self, construction, surface):
        surface._assign(construction)

    def assign_construction_to_opening(self, construction, surface, opening_id):
        for opening in surface.get_openings():
            if opening.get_id() == opening_id:
                opening._assign(construction)


class _Model:
    def __init__(self, bodies):
        self.id = "MODEL-1"
        self._bodies = bodies

    def get_bodies(self, _flag):
        return list(self._bodies)

    def rebuild_adjacencies(self):
        return None

    def assign_thermal_template_to_rooms(self, template, room_ids):
        return None


class _Construction:
    def __init__(self, identifier):
        self.id = identifier
        self.reference = "REF-{}".format(identifier)
        self.category = "opaque"
        self.opaque = True

    def get_layers(self):
        return [SimpleNamespace(get_material=lambda opaque: "MAT-1")]

    def get_properties(self):
        return {"u_value": 0.2}

    def get_u_factor(self, _enum):
        return 0.2


class _CdbProject:
    def __init__(self, signature="both"):
        self.signature = signature

    def get_construction(self, *args):
        if self.signature == "single" and len(args) != 1:
            raise TypeError("two-arg form unsupported on this build")
        if self.signature == "two" and len(args) != 2:
            raise TypeError("single-arg form unsupported on this build")
        return _Construction(str(args[0]))

    def get_material_ids(self, _category):
        return []


class _Locate:
    store = {}

    def open_wea_data(self):
        return 0

    def set(self, data):
        type(self).store = dict(data)

    def save_and_close(self):
        return None

    def get(self):
        return dict(type(self).store)

    def close_wea_data(self):
        return None


def _build_iesve(*, bodies, signature="both", weather_readable=True, with_version=True):
    """Assemble a fake iesve module rich enough to drive IesVeGateway."""

    _Locate.store = {}
    model = _Model(bodies)
    project = SimpleNamespace(
        path="C:/proj/test",
        name="TEST PROJECT",
        models=[model],
        thermal_templates=lambda assigned=False: {},
        apache_systems=lambda: [],
    )
    if with_version:
        project.get_version = lambda: "VE 2025 FAKE"

    class _WeatherReader:
        def open_weather_file(self, _path):
            return 1 if weather_readable else -1

        def close(self):
            return None

    cdb_project = _CdbProject(signature=signature)
    iesve = SimpleNamespace(
        conditioned_flag=SimpleNamespace(
            yes="conditioned_yes",
            no_free_floating="conditioned_no_free_floating",
        ),
        VEProject=SimpleNamespace(get_current_project=lambda: project),
        VEBody=SimpleNamespace(
            VEBody_type=SimpleNamespace(room=_ROOM),
            assign_construction=lambda *args, **kwargs: None,
            assign_construction_to_opening=lambda *args, **kwargs: None,
        ),
        ImportGBXML=SimpleNamespace(
            import_file=lambda *args: None,
            VolumeCapMode=SimpleNamespace(none=_CAP_NONE),
        ),
        VELocate=_Locate,
        WeatherFileReader=_WeatherReader,
        VECdbDatabase=SimpleNamespace(
            get_current_database=lambda: SimpleNamespace(
                get_projects=lambda: {0: [cdb_project]}
            )
        ),
        VECdbProject=SimpleNamespace(
            construction_class=SimpleNamespace(none=_CLASS_NONE),
            uvalue_types=SimpleNamespace(iso=_UVALUE_ISO),
            material_categories=SimpleNamespace(all=_MAT_ALL),
            element_categories=SimpleNamespace(
                wall="wall",
                roof="roof",
                ground_floor="ground_floor",
                partition="partition",
                door="door",
                ext_glazing="ext_glazing",
            ),
        ),
    )
    return iesve, project, model


def _default_room():
    """One room with external wall, roof, ground floor, and one window."""

    window = _Opening("O1", "window")
    return _Body(
        None,
        "RM_Z1",
        "B1",
        [
            _Surface(0, "ExternalWall", openings=[window]),
            _Surface(1, "Roof"),
            _Surface(2, "GroundFloor"),
        ],
    )


class VeGatewayCapabilityTests(unittest.TestCase):
    def test_check_capabilities_passes_when_runtime_complete(self):
        iesve, _project, _model = _build_iesve(bodies=[_default_room()])
        gateway = IesVeGateway(iesve_module=iesve)
        capabilities = gateway.check_capabilities()
        self.assertTrue(all(capabilities.values()))
        self.assertIn("ImportGBXML.VolumeCapMode", capabilities)
        # get_version is intentionally not gated (informational-only, see L4).
        self.assertNotIn("VEProject.get_version", capabilities)

    def test_top_level_volume_cap_mode_is_supported(self):
        iesve, _project, _model = _build_iesve(bodies=[_default_room()])
        iesve.VolumeCapMode = iesve.ImportGBXML.VolumeCapMode
        del iesve.ImportGBXML.VolumeCapMode
        gateway = IesVeGateway(iesve_module=iesve)
        capabilities = gateway.check_capabilities()
        self.assertTrue(capabilities["ImportGBXML.VolumeCapMode"])

        gateway.import_geometry(Path(__file__))

    def test_missing_mutation_member_fails_at_preflight(self):
        iesve, _project, _model = _build_iesve(bodies=[_default_room()])
        del iesve.ImportGBXML.VolumeCapMode  # documented member removed
        gateway = IesVeGateway(iesve_module=iesve)
        with self.assertRaises(VeApiUnavailableError):
            gateway.check_capabilities()

    def test_version_less_runtime_still_passes_capabilities(self):
        """get_version is informational-only and must not block preflight."""

        iesve, _project, _model = _build_iesve(
            bodies=[_default_room()], with_version=False
        )
        gateway = IesVeGateway(iesve_module=iesve)
        capabilities = gateway.check_capabilities()  # must not raise
        self.assertNotIn("VEProject.get_version", capabilities)


class VeGatewayConstructionTests(unittest.TestCase):
    def test_native_glazed_cavity_with_positive_resistance_is_resolved(self):
        construction = SimpleNamespace(opaque=False)
        cavity = SimpleNamespace(
            get_material=lambda _opaque: None,
            get_properties=lambda: {
                "resistance": 0.75,
                "convection_coefficient": 0.0,
            },
        )
        self.assertTrue(
            IesVeGateway._construction_layer_is_resolved(construction, cavity)
        )

    def test_materialless_zero_resistance_layer_is_not_resolved(self):
        construction = SimpleNamespace(opaque=False)
        invalid = SimpleNamespace(
            get_material=lambda _opaque: None,
            get_properties=lambda: {
                "resistance": 0.0,
                "convection_coefficient": 0.0,
            },
        )
        self.assertFalse(
            IesVeGateway._construction_layer_is_resolved(construction, invalid)
        )

    def test_get_construction_tolerates_single_arg_signature(self):
        iesve, _project, _model = _build_iesve(
            bodies=[_default_room()], signature="single"
        )
        gateway = IesVeGateway(iesve_module=iesve)
        self.assertEqual(str(gateway._get_construction("EXTW").id), "EXTW")

    def test_get_construction_tolerates_two_arg_signature(self):
        iesve, _project, _model = _build_iesve(
            bodies=[_default_room()], signature="two"
        )
        gateway = IesVeGateway(iesve_module=iesve)
        self.assertEqual(str(gateway._get_construction("EXTW").id), "EXTW")

    def test_assign_constructions_persists_and_reads_back(self):
        room = _default_room()
        iesve, _project, _model = _build_iesve(bodies=[room])
        gateway = IesVeGateway(iesve_module=iesve)
        gateway.assign_constructions(_expected_geometry(["RM_Z1"]), _configured_parameters())
        wall = room.get_surfaces()[0]
        self.assertEqual(wall.get_constructions()[0].id, "EXTW")
        self.assertEqual(wall.get_openings()[0].get_construction().id, "GLAZ")

    def test_assign_constructions_raises_on_readback_mismatch(self):
        room = _default_room()
        room.get_surfaces()[0].persist = False  # assignment silently drops
        iesve, _project, _model = _build_iesve(bodies=[room])
        gateway = IesVeGateway(iesve_module=iesve)
        with self.assertRaises(VeMutationError):
            gateway.assign_constructions(
                _expected_geometry(["RM_Z1"]), _configured_parameters()
            )


class VeGatewayAdjacencyGuardTests(unittest.TestCase):
    def test_verify_passes_when_types_consistent(self):
        room = _default_room()
        iesve, _project, _model = _build_iesve(bodies=[room])
        gateway = IesVeGateway(iesve_module=iesve)
        parameters = _configured_parameters()
        geometry = _expected_geometry(["RM_Z1"])
        gateway.assign_constructions(geometry, parameters)
        gateway.verify_construction_assignments(geometry, parameters)  # no raise

    def test_verify_raises_on_post_adjacency_type_change(self):
        room = _default_room()
        iesve, _project, _model = _build_iesve(bodies=[room])
        gateway = IesVeGateway(iesve_module=iesve)
        parameters = _configured_parameters()
        geometry = _expected_geometry(["RM_Z1"])
        gateway.assign_constructions(geometry, parameters)
        # Simulate adjacency reconciliation relabelling the wall as internal:
        room.get_surfaces()[0].type = "InternalWall"
        with self.assertRaises(VeMutationError):
            gateway.verify_construction_assignments(geometry, parameters)


class VeGatewayMiscTests(unittest.TestCase):
    def test_client_template_assignment_is_explicit_and_read_back(self):
        """The public client boundary verifies assignment on named rooms."""

        room = _Body(None, "CLIENT ROOM", "ROOM-1", [])
        iesve, project, model = _build_iesve(bodies=[room])

        class _Template:
            name = "REVIEWED CLIENT TEMPLATE"

            @staticmethod
            def get_casual_gains():
                return []

            @staticmethod
            def get_air_exchanges():
                return []

        template = _Template()
        project.thermal_templates = lambda assigned=False: {8: template}

        def assign_template(_template, room_ids):
            self.assertEqual(room_ids, ["ROOM-1"])
            room._room_data._general.update(
                {
                    "thermal_template": 8,
                    "thermal_template_name": "REVIEWED CLIENT TEMPLATE",
                }
            )

        model.assign_thermal_template_to_rooms = assign_template
        receipt = IesVeGateway(iesve_module=iesve).apply_existing_thermal_template_to_rooms(
            "REVIEWED CLIENT TEMPLATE", ["ROOM-1"]
        )

        self.assertEqual(receipt["room_ids"], ["ROOM-1"])
        self.assertEqual(
            receipt["after"][0]["general"]["thermal_template_name"],
            "REVIEWED CLIENT TEMPLATE",
        )

    def test_client_template_assignment_bridges_and_restores_missing_gain_rows(self):
        """A documented source-template bridge is exact, scoped and restored."""

        room = _Body(None, "CLIENT ROOM", "ROOM-1", [])
        room._room_data._general = {
            "thermal_template": 1,
            "thermal_template_name": "SOURCE TEMPLATE",
        }
        energy = SimpleNamespace(
            get=lambda: {"name": "Target equipment", "type_str": "Computers"}
        )
        people = SimpleNamespace(
            get=lambda: {"name": "Target people", "type_str": "People"}
        )
        lighting = SimpleNamespace(
            get=lambda: {"name": "Target lighting", "type_str": "Lighting"}
        )
        room._room_data._gains = [energy]
        iesve, project, model = _build_iesve(bodies=[room])

        class _Template:
            def __init__(self, name, gains, on_apply=None):
                self.name = name
                self.gains = list(gains)
                self.on_apply = on_apply

            def get_casual_gains(self):
                return list(self.gains)

            @staticmethod
            def get_air_exchanges():
                return []

            def add_gain(self, gain):
                self.gains.append(gain)

            def remove_gain(self, gain):
                self.gains.remove(gain)

            def apply_changes(self):
                if self.on_apply is not None:
                    self.on_apply(self)

        def propagate_source(source):
            if room._room_data._general.get("thermal_template") == 1:
                room._room_data._gains = list(source.gains)

        source = _Template("SOURCE TEMPLATE", [energy], propagate_source)
        target = _Template(
            "REVIEWED CLIENT TEMPLATE", [people, lighting, energy]
        )
        project.thermal_templates = lambda assigned=False: {1: source, 8: target}

        def assign_template(_template, room_ids):
            self.assertEqual(room_ids, ["ROOM-1"])
            room._room_data._general = {
                "thermal_template": 8,
                "thermal_template_name": "REVIEWED CLIENT TEMPLATE",
            }

        model.assign_thermal_template_to_rooms = assign_template
        bridge = [
            {
                "source_template_handle": "1",
                "source_template_name": "SOURCE TEMPLATE",
                "original_gain_record_names": ["Target equipment"],
                "target_gain_records": [
                    {"family": "people", "name": "Target people"},
                    {"family": "lighting", "name": "Target lighting"},
                ],
            }
        ]

        receipt = IesVeGateway(
            iesve_module=iesve
        ).apply_existing_thermal_template_to_rooms(
            "REVIEWED CLIENT TEMPLATE", ["ROOM-1"], structure_bridge=bridge
        )

        self.assertEqual(
            receipt["transient_gain_structure_bridge"]["status"],
            "APPLIED_AND_RESTORED",
        )
        self.assertEqual(
            [gain.get()["name"] for gain in source.get_casual_gains()],
            ["Target equipment"],
        )
        self.assertEqual(len(room._room_data.get_internal_gains()), 3)

    def test_client_template_bridge_restores_source_when_assignment_fails(self):
        """A downstream VE failure cannot leave the source template bridged."""

        room = _Body(None, "CLIENT ROOM", "ROOM-1", [])
        room._room_data._general = {
            "thermal_template": 1,
            "thermal_template_name": "SOURCE TEMPLATE",
        }
        energy = SimpleNamespace(
            get=lambda: {"name": "Target equipment", "type_str": "Computers"}
        )
        people = SimpleNamespace(
            get=lambda: {"name": "Target people", "type_str": "People"}
        )
        room._room_data._gains = [energy]
        iesve, project, model = _build_iesve(bodies=[room])

        class _Template:
            def __init__(self, name, gains, on_apply=None):
                self.name = name
                self.gains = list(gains)
                self.on_apply = on_apply

            def get_casual_gains(self):
                return list(self.gains)

            @staticmethod
            def get_air_exchanges():
                return []

            def add_gain(self, gain):
                self.gains.append(gain)

            def remove_gain(self, gain):
                self.gains.remove(gain)

            def apply_changes(self):
                if self.on_apply is not None:
                    self.on_apply(self)

        def propagate_source(source):
            if room._room_data._general.get("thermal_template") == 1:
                room._room_data._gains = list(source.gains)

        source = _Template("SOURCE TEMPLATE", [energy], propagate_source)
        target = _Template("REVIEWED CLIENT TEMPLATE", [people, energy])
        project.thermal_templates = lambda assigned=False: {1: source, 8: target}

        def fail_assignment(_template, _room_ids):
            raise RuntimeError("synthetic VE setter failure")

        model.assign_thermal_template_to_rooms = fail_assignment
        bridge = [
            {
                "source_template_handle": "1",
                "source_template_name": "SOURCE TEMPLATE",
                "original_gain_record_names": ["Target equipment"],
                "target_gain_records": [
                    {"family": "people", "name": "Target people"},
                ],
            }
        ]

        with self.assertRaisesRegex(VeMutationError, "synthetic VE setter failure"):
            IesVeGateway(
                iesve_module=iesve
            ).apply_existing_thermal_template_to_rooms(
                "REVIEWED CLIENT TEMPLATE", ["ROOM-1"], structure_bridge=bridge
            )

        self.assertEqual(
            [gain.get()["name"] for gain in source.get_casual_gains()],
            ["Target equipment"],
        )

    def test_room_control_sync_writes_only_changed_supported_fields(self):
        """Never replay read-only getter fields such as VE 2025 ``dhw_unit``."""

        room = _default_room()
        iesve, project, model = _build_iesve(bodies=[room])
        room_data = room.get_room_data()
        actual_conditions = {
            "heating_profile": "WEEK0048",
            "heating_setpoint_type": 0,
            "heating_setpoint_profile": "0",
            "dhw_unit": "l/h",
        }
        submitted = []

        room_data.get_room_conditions = lambda: dict(actual_conditions)

        def set_room_conditions(payload):
            payload = dict(payload)
            if "dhw_unit" in payload:
                raise RuntimeError("unrecognised option: dhw_unit")
            submitted.append(payload)
            actual_conditions.update(
                {
                    key: value
                    for key, value in payload.items()
                    if not key.endswith("_from_template")
                }
            )

        room_data.set_room_conditions = set_room_conditions
        room_data._apache = {
            "conditioned": True,
            "HVAC_system": "SYST0000",
        }
        expected_conditions = {
            "heating_profile": "ON",
            "heating_setpoint_type": 1,
            "heating_setpoint_profile": "WEEK0048",
        }
        template = SimpleNamespace(
            name="TEST TEMPLATE",
            apply_changes=lambda: None,
            get_casual_gains=lambda: [],
            get_air_exchanges=lambda: [],
            get_room_conditions=lambda: dict(expected_conditions),
            get_apache_systems=lambda: dict(room_data._apache),
        )
        project.thermal_templates = lambda assigned=False: {5: template}

        def assign_template(_template, _room_ids):
            room_data._general = {
                "thermal_template": 5,
                "thermal_template_name": "TEST TEMPLATE",
            }

        model.assign_thermal_template_to_rooms = assign_template

        IesVeGateway(iesve_module=iesve).assign_thermal_template(
            _expected_geometry(["RM_Z1"]), _configured_parameters()
        )

        self.assertEqual(len(submitted), 1)
        self.assertNotIn("dhw_unit", submitted[0])
        self.assertEqual(submitted[0]["heating_profile"], "ON")
        self.assertEqual(submitted[0]["heating_setpoint_type"], 1)
        self.assertEqual(
            submitted[0]["heating_setpoint_profile"], "WEEK0048"
        )
        self.assertFalse(submitted[0]["heating_setpoint_from_template"])
        self.assertNotIn(
            "heating_setpoint_profile_from_template", submitted[0]
        )
        self.assertNotIn(
            "cooling_setpoint_profile_from_template", submitted[0]
        )

    def test_assign_thermal_template_accepts_native_handle_and_name_readback(self):
        room = _default_room()
        iesve, project, model = _build_iesve(bodies=[room])
        gain = SimpleNamespace(get=lambda: {"name": "TEST GAIN"})
        exchange = SimpleNamespace(get=lambda: {"name": "TEST AIR"})
        template = SimpleNamespace(
            name="TEST TEMPLATE",
            apply_changes=lambda: None,
            get_casual_gains=lambda: [gain],
            get_air_exchanges=lambda: [exchange],
        )
        project.thermal_templates = lambda assigned=False: {5: template}

        def assign_template(_template, room_ids):
            self.assertEqual(room_ids, ["B1"])
            room.get_room_data()._general = {
                "thermal_template": 5,
                "thermal_template_name": "TEST TEMPLATE",
            }
            room.get_room_data()._gains = [gain]
            room.get_room_data()._air_exchanges = [exchange]

        model.assign_thermal_template_to_rooms = assign_template
        gateway = IesVeGateway(iesve_module=iesve)

        gateway.assign_thermal_template(
            _expected_geometry(["RM_Z1"]), _configured_parameters()
        )
        self.assertEqual(
            room.get_room_data().get_general()["thermal_template"], 5
        )

    def test_assign_thermal_template_applies_deferred_free_floating_to_room(self):
        """Verify effective OFF profiles despite VE's advisory conditioned enum."""

        room = _default_room()
        room_data = room.get_room_data()
        room_data._apache = {
            "conditioned": "conditioned_yes",
            "conditioned_from_template": True,
        }
        room_conditions = {
            "heating_profile": "ON",
            "cooling_profile": "ON",
        }
        room_data.get_room_conditions = lambda: dict(room_conditions)

        def set_room_conditions(payload):
            room_conditions.update(
                {
                    key: value
                    for key, value in dict(payload).items()
                    if not key.endswith("_from_template")
                }
            )

        room_data.set_room_conditions = set_room_conditions
        iesve, project, model = _build_iesve(bodies=[room])
        template = SimpleNamespace(
            name="TEST TEMPLATE",
            apply_changes=lambda: None,
            get_casual_gains=lambda: [],
            get_air_exchanges=lambda: [],
            get_room_conditions=lambda: {
                "heating_profile": "OFF",
                "cooling_profile": "OFF",
            },
            get_apache_systems=lambda: dict(room_data._apache),
        )
        project.thermal_templates = lambda assigned=False: {5: template}

        def assign_template(_template, _room_ids):
            room_data._general = {
                "thermal_template": 5,
                "thermal_template_name": "TEST TEMPLATE",
            }

        model.assign_thermal_template_to_rooms = assign_template
        gateway = IesVeGateway(iesve_module=iesve)
        gateway._provisioned_conditioned_state = False

        gateway.assign_thermal_template(
            _expected_geometry(["RM_Z1"]), _configured_parameters()
        )

        self.assertEqual(room_conditions["heating_profile"], "OFF")
        self.assertEqual(room_conditions["cooling_profile"], "OFF")
        self.assertEqual(
            room_data.get_apache_systems()["conditioned"], "conditioned_yes"
        )
        warnings = gateway.consume_runtime_compatibility_warnings()
        self.assertEqual(
            warnings[0]["control_changes"]["free_floating"]["expected"],
            {"heating_profile": "OFF", "cooling_profile": "OFF"},
        )

    def test_assign_thermal_template_rejects_default_room_content(self):
        """A matching template name must not hide unresolved default room data."""
        room = _default_room()
        iesve, project, model = _build_iesve(bodies=[room])
        expected_gain = SimpleNamespace(get=lambda: {"name": "SIA_REF_LIGHTING"})
        default_gain = SimpleNamespace(get=lambda: {"name": "Default Office Lighting"})
        template = SimpleNamespace(
            name="TEST TEMPLATE",
            apply_changes=lambda: None,
            get_casual_gains=lambda: [expected_gain],
            get_air_exchanges=lambda: [],
        )
        project.thermal_templates = lambda assigned=False: {5: template}

        def assign_template(_template, _room_ids):
            room.get_room_data()._general = {
                "thermal_template": 5,
                "thermal_template_name": "TEST TEMPLATE",
            }
            room.get_room_data()._gains = [default_gain]

        model.assign_thermal_template_to_rooms = assign_template
        gateway = IesVeGateway(iesve_module=iesve)

        with self.assertRaisesRegex(VeMutationError, "gain content did not resolve"):
            gateway.assign_thermal_template(
                _expected_geometry(["RM_Z1"]), _configured_parameters()
            )

    def test_assign_thermal_template_synchronises_and_verifies_room_gain_physics(self):
        room = _default_room()
        iesve, project, model = _build_iesve(bodies=[room])
        expected_gain = SimpleNamespace(
            get=lambda: {
                "name": "SIA600_EQUIPMENT_200W",
                "type_str": "Computers",
                "units_val": 0,
                "max_power_consumption": 200.0 / 48.0,
                "max_sensible_gain": 200.0 / 48.0,
                "max_latent_gain": 0.0,
                "radiant_fraction": 0.6,
                "variation_profile": "DAY_CASE600",
            }
        )
        room_gain = _MutableGain(
            {
                "name": "Default Office Equipment",
                "type_str": "Miscellaneous",
                "units_val": 0,
                "max_power_consumptions": {0: 10.0},
                "max_sensible_gains": {0: 10.0},
                "max_latent_gains": {0: 0.0},
                "radiant_fraction": 0.22,
                "variation_profile": "WEEK_DEFAULT",
            }
        )
        template = SimpleNamespace(
            name="TEST TEMPLATE",
            apply_changes=lambda: None,
            get_casual_gains=lambda: [expected_gain],
            get_air_exchanges=lambda: [],
        )
        project.thermal_templates = lambda assigned=False: {5: template}

        def assign_template(_template, _room_ids):
            room.get_room_data()._general = {
                "thermal_template": 5,
                "thermal_template_name": "TEST TEMPLATE",
            }
            room.get_room_data()._gains = [room_gain]

        model.assign_thermal_template_to_rooms = assign_template
        gateway = IesVeGateway(iesve_module=iesve)
        gateway.assign_thermal_template(
            _expected_geometry(["RM_Z1"]), _configured_parameters()
        )

        readback = room_gain.get()
        self.assertAlmostEqual(readback["max_sensible_gains"][0] * 48.0, 200.0)
        self.assertEqual(readback["radiant_fraction"], 0.6)
        self.assertEqual(readback["variation_profile"], "DAY_CASE600")
        warnings = gateway.consume_runtime_compatibility_warnings()
        self.assertEqual(warnings[0]["code"], "VE-TEMPLATE-CONTENT-DIRECT-SYNC")

    def test_assign_template_uses_isolated_scalar_people_latent_fallback(self):
        room = _default_room()
        iesve, project, model = _build_iesve(bodies=[room])
        expected_gain = SimpleNamespace(
            get=lambda: {
                "name": "SIA_REF_PEOPLE",
                "type_str": "People",
                "units_val": 0,
                "occupancy_density": 15.0,
                "max_sensible_gain": 75.0,
                "max_latent_gain": 45.0,
                "diversity_factor": 1.0,
                "variation_profile": "DAY_0035",
            }
        )
        room_gain = _IsolatedScalarLatentGain(
            {
                "name": "Default People",
                "type_str": "People",
                "units_val": 0,
                "occupancies": {0: 15.0, 1: 4.0},
                "max_sensible_gains": {0: 75.0, 1: 300.0},
                "max_latent_gains": {0: 0.0, 1: 0.0},
                "diversity_factor": 1.0,
                "variation_profile": "DAY_0035",
            }
        )
        template = SimpleNamespace(
            name="TEST TEMPLATE",
            apply_changes=lambda: None,
            get_casual_gains=lambda: [expected_gain],
            get_air_exchanges=lambda: [],
        )
        project.thermal_templates = lambda assigned=False: {5: template}

        def assign_template(_template, _room_ids):
            room.get_room_data()._general = {
                "thermal_template": 5,
                "thermal_template_name": "TEST TEMPLATE",
            }
            room.get_room_data()._gains = [room_gain]

        model.assign_thermal_template_to_rooms = assign_template
        gateway = IesVeGateway(iesve_module=iesve)
        gateway.assign_thermal_template(
            _expected_geometry(["RM_Z1"]), _configured_parameters()
        )

        readback = room_gain.get()
        self.assertEqual(readback["max_latent_gains"][0], 45.0)
        warnings = gateway.consume_runtime_compatibility_warnings()
        self.assertEqual(
            warnings[0]["gain_changes"][0]["people_latent_fallback"],
            "isolated_scalar",
        )

    def test_missing_mechanical_exchange_maps_to_apache_system_air(self):
        room = _default_room()
        room.get_room_data()._apache = {
            "HVAC_methodology": "apache_system",
            "system_air_minimum_flowrate": 0.8,
            "system_air_minimum_flowrate_unit": 2,
            "system_air_variation_profile": "OFF",
            "system_air_minimum_flowrate_from_template": True,
            "system_air_variation_profile_from_template": True,
        }
        iesve, project, model = _build_iesve(bodies=[room])
        outdoor_air = SimpleNamespace(
            get=lambda: {
                "name": "SIA_REF_OUTDOOR_AIR",
                "type_str": "Auxiliary Ventilation",
                "type_val": "mechanical_ventilation",
                "max_flow": 10.0,
                "units_val": 3,
                "variation_profile": "DAY_0035",
            }
        )
        template = SimpleNamespace(
            name="TEST TEMPLATE",
            apply_changes=lambda: None,
            get_casual_gains=lambda: [],
            get_air_exchanges=lambda: [outdoor_air],
            get_apache_systems=lambda: {},
        )
        project.thermal_templates = lambda assigned=False: {5: template}

        def assign_template(_template, _room_ids):
            room.get_room_data()._general = {
                "thermal_template": 5,
                "thermal_template_name": "TEST TEMPLATE",
            }

        model.assign_thermal_template_to_rooms = assign_template
        gateway = IesVeGateway(iesve_module=iesve)
        gateway.assign_thermal_template(
            _expected_geometry(["RM_Z1"]), _configured_parameters()
        )

        system = room.get_room_data().get_apache_systems()
        self.assertEqual(system["system_air_minimum_flowrate"], 10.0)
        self.assertEqual(system["system_air_minimum_flowrate_unit"], 3)
        self.assertEqual(system["system_air_variation_profile"], "DAY_0035")
        warnings = gateway.consume_runtime_compatibility_warnings()
        change = warnings[0]["air_exchange_changes"][0]
        self.assertEqual(
            change["binding"], "apache_system.system_air_minimum_flowrate"
        )

    def test_mechanical_exchange_uses_plural_unit_setter_with_singular_readback(self):
        room = _default_room()
        room_data = room.get_room_data()
        room_data._apache = {
            "HVAC_methodology": "apache_system",
            "system_air_minimum_flowrate": 0.8,
            "system_air_minimum_flowrate_unit": 2,
            "system_air_variation_profile": "OFF",
        }

        def set_apache_systems(data):
            payload = dict(data)
            if "system_air_minimum_flowrate_unit" in payload:
                raise RuntimeError(
                    "unrecognised option: system_air_minimum_flowrate_unit"
                )
            unit = payload.pop("system_air_minimum_flowrate_units", None)
            room_data._apache.update(payload)
            if unit is not None:
                room_data._apache["system_air_minimum_flowrate_unit"] = unit

        room_data.set_apache_systems = set_apache_systems
        iesve, project, model = _build_iesve(bodies=[room])
        outdoor_air = SimpleNamespace(
            get=lambda: {
                "name": "SIA_REF_OUTDOOR_AIR",
                "type_str": "Auxiliary Ventilation",
                "type_val": "mechanical_ventilation",
                "max_flow": 10.0,
                "units_val": 3,
                "variation_profile": "DAY_0035",
            }
        )
        template = SimpleNamespace(
            name="TEST TEMPLATE",
            apply_changes=lambda: None,
            get_casual_gains=lambda: [],
            get_air_exchanges=lambda: [outdoor_air],
            get_apache_systems=lambda: {},
        )
        project.thermal_templates = lambda assigned=False: {5: template}

        def assign_template(_template, _room_ids):
            room_data._general = {
                "thermal_template": 5,
                "thermal_template_name": "TEST TEMPLATE",
            }

        model.assign_thermal_template_to_rooms = assign_template
        gateway = IesVeGateway(iesve_module=iesve)
        gateway.assign_thermal_template(
            _expected_geometry(["RM_Z1"]), _configured_parameters()
        )

        system = room_data.get_apache_systems()
        self.assertEqual(system["system_air_minimum_flowrate"], 10.0)
        self.assertEqual(system["system_air_minimum_flowrate_unit"], 3)
        self.assertEqual(system["system_air_variation_profile"], "DAY_0035")

    def test_mechanical_exchange_converts_when_room_unit_is_read_only(self):
        room = _default_room()
        room_data = room.get_room_data()
        room_data._apache = {
            "HVAC_methodology": "apache_system",
            "system_air_minimum_flowrate": 0.8,
            "system_air_minimum_flowrate_unit": 2,
            "system_air_minimum_flowrates": {
                0: 0.96,
                1: 48.0,
                2: 0.8,
                3: 12.0,
                4: 1.0,
            },
            "system_air_variation_profile": "OFF",
        }

        def set_apache_systems(data):
            payload = dict(data)
            for rejected in (
                "system_air_minimum_flowrate_units",
                "system_air_minimum_flowrate_unit",
            ):
                if rejected in payload:
                    raise RuntimeError("unrecognised option: {}".format(rejected))
            old_flow = room_data._apache["system_air_minimum_flowrate"]
            new_flow = payload.get("system_air_minimum_flowrate", old_flow)
            scale = float(new_flow) / float(old_flow)
            room_data._apache["system_air_minimum_flowrates"] = {
                key: value * scale
                for key, value in room_data._apache[
                    "system_air_minimum_flowrates"
                ].items()
            }
            room_data._apache.update(payload)

        room_data.set_apache_systems = set_apache_systems
        iesve, project, model = _build_iesve(bodies=[room])
        outdoor_air = SimpleNamespace(
            get=lambda: {
                "name": "SIA_REF_OUTDOOR_AIR",
                "type_str": "Auxiliary Ventilation",
                "type_val": "mechanical_ventilation",
                "max_flow": 10.0,
                "units_val": 3,
                "variation_profile": "DAY_0035",
            }
        )
        template = SimpleNamespace(
            name="TEST TEMPLATE",
            apply_changes=lambda: None,
            get_casual_gains=lambda: [],
            get_air_exchanges=lambda: [outdoor_air],
            get_apache_systems=lambda: {},
        )
        project.thermal_templates = lambda assigned=False: {5: template}

        def assign_template(_template, _room_ids):
            room_data._general = {
                "thermal_template": 5,
                "thermal_template_name": "TEST TEMPLATE",
            }

        model.assign_thermal_template_to_rooms = assign_template
        gateway = IesVeGateway(iesve_module=iesve)
        gateway.assign_thermal_template(
            _expected_geometry(["RM_Z1"]), _configured_parameters()
        )

        system = room_data.get_apache_systems()
        self.assertAlmostEqual(system["system_air_minimum_flowrate"], 2.0 / 3.0)
        self.assertEqual(system["system_air_minimum_flowrate_unit"], 2)
        self.assertAlmostEqual(system["system_air_minimum_flowrates"][3], 10.0)
        change = gateway.consume_runtime_compatibility_warnings()[0][
            "air_exchange_changes"
        ][0]
        self.assertEqual(
            change["binding_mode"], "converted_existing_native_unit"
        )

    def test_assign_thermal_template_rejects_missing_native_readback(self):
        room = _default_room()
        room.get_room_data()._general = {
            "thermal_template": 1,
            "thermal_template_name": "DEFAULT",
        }
        iesve, project, _model = _build_iesve(bodies=[room])
        project.thermal_templates = lambda assigned=False: {
            5: SimpleNamespace(
                name="TEST TEMPLATE",
                get_casual_gains=lambda: [],
                get_air_exchanges=lambda: [],
            )
        }
        gateway = IesVeGateway(iesve_module=iesve)

        with self.assertRaises(VeMutationError):
            gateway.assign_thermal_template(
                _expected_geometry(["RM_Z1"]), _configured_parameters()
            )

    def test_snapshot_resolves_native_template_handle_to_name(self):
        room = _default_room()
        room.get_room_data()._general = {
            "thermal_template": 5,
            "thermal_template_name": "TEST TEMPLATE",
        }
        iesve, project, _model = _build_iesve(bodies=[room])
        project.thermal_templates = lambda assigned=False: {}
        gateway = IesVeGateway(iesve_module=iesve)

        snapshot = gateway.snapshot(
            _expected_geometry(["RM_Z1"]), _configured_parameters()
        )
        self.assertEqual(snapshot.rooms[0].thermal_template_name, "TEST TEMPLATE")

    def test_assert_no_existing_generated_rooms_raises_on_collision(self):
        iesve, _project, _model = _build_iesve(bodies=[_default_room()])
        gateway = IesVeGateway(iesve_module=iesve)
        with self.assertRaises(VeMutationError):
            gateway.assert_no_existing_generated_rooms(["RM_Z1"])

    def test_assign_weather_raises_when_unreadable(self):
        iesve, _project, _model = _build_iesve(
            bodies=[_default_room()], weather_readable=False
        )
        gateway = IesVeGateway(iesve_module=iesve)
        with self.assertRaises(VeMutationError):
            gateway.assign_weather("C:/wx/test.fwt")

    def test_assign_weather_verifies_readback(self):
        iesve, _project, _model = _build_iesve(bodies=[_default_room()])
        gateway = IesVeGateway(iesve_module=iesve)
        gateway.assign_weather("C:/wx/test.fwt")  # no raise

    def test_assign_weather_uses_basename_for_identical_ve_weather_file(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_folder = root / "project"
            installed_folder = root / "weather"
            source_folder.mkdir()
            installed_folder.mkdir()
            source = source_folder / "DRYCOLD_IESVE.epw"
            installed = installed_folder / source.name
            source.write_bytes(b"same-qualified-weather")
            installed.write_bytes(source.read_bytes())
            iesve, _project, _model = _build_iesve(bodies=[_default_room()])
            iesve.get_weather_file_paths = lambda: [str(installed_folder)]
            gateway = IesVeGateway(iesve_module=iesve)

            gateway.assign_weather(str(source))

            self.assertEqual(_Locate.store["weather_file"], source.name)

    def test_normalize_weather_uses_basename_for_project_local_epw(self):
        with TemporaryDirectory() as temporary:
            project_path = Path(temporary)
            source = project_path / "DRYCOLD_IESVE.epw"
            source.write_bytes(b"qualified-project-local-weather")
            iesve, project, _model = _build_iesve(bodies=[_default_room()])
            project.path = str(project_path)
            _Locate.store["weather_file"] = str(source)
            gateway = IesVeGateway(iesve_module=iesve)

            before, after = gateway.normalize_weather_reference_for_apachesim()

            self.assertEqual(before, str(source))
            self.assertEqual(after, source.name)
            self.assertEqual(_Locate.store["weather_file"], source.name)

    def test_assign_weather_verifies_project_local_basename_via_absolute_path(self):
        with TemporaryDirectory() as temporary:
            project_path = Path(temporary)
            source = project_path / "DRYCOLD_IESVE.epw"
            source.write_bytes(b"qualified-project-local-weather")
            iesve, project, _model = _build_iesve(bodies=[_default_room()])
            project.path = str(project_path)

            class _ProjectLocalWeatherReader:
                basename_attempts = 0

                def open_weather_file(self, reference):
                    path = Path(str(reference))
                    if not path.is_absolute():
                        type(self).basename_attempts += 1
                        # The qualification in _apache_weather_reference works,
                        # while the post-VELocate basename read-back reproduces
                        # the inconsistent VE runtime behavior.
                        return 1 if type(self).basename_attempts == 1 else -1
                    return 1 if path == source else -1

                def close(self):
                    return None

            iesve.WeatherFileReader = _ProjectLocalWeatherReader
            gateway = IesVeGateway(iesve_module=iesve)

            gateway.assign_weather(str(source))

            self.assertEqual(_Locate.store["weather_file"], source.name)
            self.assertGreaterEqual(
                _ProjectLocalWeatherReader.basename_attempts, 2
            )

    def test_assign_weather_accepts_prequalified_source_when_post_save_probe_fails(self):
        with TemporaryDirectory() as temporary:
            project_path = Path(temporary)
            source = project_path / "DRYCOLD_IESVE.epw"
            source.write_bytes(b"qualified-project-local-weather")
            iesve, project, _model = _build_iesve(bodies=[_default_room()])
            project.path = str(project_path)

            class _PostSaveUnreadableWeatherReader:
                def open_weather_file(self, reference):
                    path = Path(str(reference))
                    if not _Locate.store and path == source:
                        return 1
                    return -1

                def close(self):
                    return None

            iesve.WeatherFileReader = _PostSaveUnreadableWeatherReader
            gateway = IesVeGateway(iesve_module=iesve)

            gateway.assign_weather(str(source))

            self.assertEqual(_Locate.store["weather_file"], source.name)
            warnings = gateway.consume_runtime_compatibility_warnings()
            self.assertEqual(warnings[0]["code"], "VE-WEATHER-POST-SAVE-READBACK")
            self.assertEqual(warnings[0]["qualified_source"], str(source))

    def test_assign_weather_rejects_basename_collision_by_retaining_path(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_folder = root / "project"
            installed_folder = root / "weather"
            source_folder.mkdir()
            installed_folder.mkdir()
            source = source_folder / "DRYCOLD_IESVE.epw"
            installed = installed_folder / source.name
            source.write_bytes(b"qualified-weather")
            installed.write_bytes(b"different-weather")
            iesve, _project, _model = _build_iesve(bodies=[_default_room()])
            iesve.get_weather_file_paths = lambda: [str(installed_folder)]
            gateway = IesVeGateway(iesve_module=iesve)

            gateway.assign_weather(str(source))

            self.assertEqual(_Locate.store["weather_file"], str(source))

    def test_import_geometry_missing_file_raises(self):
        iesve, _project, _model = _build_iesve(bodies=[_default_room()])
        gateway = IesVeGateway(iesve_module=iesve)
        with self.assertRaises(VeMutationError):
            gateway.import_geometry(Path("does_not_exist_reference_model.gbxml"))

    def test_snapshot_uses_safe_version_when_accessor_missing(self):
        iesve, _project, _model = _build_iesve(
            bodies=[_default_room()], with_version=False
        )
        gateway = IesVeGateway(iesve_module=iesve)
        snapshot = gateway.snapshot(_expected_geometry(["RM_Z1"]), _configured_parameters())
        self.assertEqual(snapshot.ve_version, "unknown")
        self.assertEqual(len(snapshot.rooms), 1)


if __name__ == "__main__":
    unittest.main()
