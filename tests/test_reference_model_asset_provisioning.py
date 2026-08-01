"""Tests for source-traced creation of VE assets from scratch."""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from swiss_sia.reference_model.asset_manifest import load_asset_manifest
from swiss_sia.reference_model.compliance_config import build_default_registry
from swiss_sia.reference_model.exceptions import ConfigurationError, VeMutationError
from swiss_sia.reference_model.results import ValidationStatus
from swiss_sia.reference_model.ve_api import VeGateway
from swiss_sia.reference_model.ve_asset_provisioner import (
    IesVeAssetProvisioner,
    _values_match,
)
from swiss_sia.reference_model.workflow import ReferenceModelWorkflow


TEST_ROOT = Path(__file__).resolve().parents[1]
TEST_OUTPUT_ROOT = TEST_ROOT / ".codex_tmp" / "reference_model_asset_tests"


def _test_dir(name):
    """Return a stable writable test directory."""

    path = TEST_OUTPUT_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _field(value, expected_type="any", minimum=None, maximum=None):
    """Build a compact source-traced test field."""

    validation_range = {"expected_type": expected_type, "allow_none": False}
    if minimum is not None:
        validation_range["minimum"] = minimum
    if maximum is not None:
        validation_range["maximum"] = maximum
    return {
        "value": value,
        "description": "Approved unit-test field value.",
        "units": "test units",
        "source": "Approved unit-test evidence",
        "source_locator": "TEST-ASSET-EVIDENCE-001",
        "validation_range": validation_range,
        "required": True,
    }


def _evidence(description):
    """Return approved object-level evidence for a test asset."""

    return {
        "description": description,
        "source": "Approved unit-test asset evidence",
        "source_locator": "TEST-ASSET-EVIDENCE-001",
    }


def _valid_manifest_payload():
    """Return a complete non-regulatory manifest fixture."""

    assignments = (
        ("wall", "external_wall_construction_id", "wall", "opaque"),
        ("roof", "roof_construction_id", "roof", "opaque"),
        ("floor", "ground_floor_construction_id", "ground_floor", "opaque"),
        ("partition", "internal_wall_construction_id", "partition", "opaque"),
        ("door", "door_construction_id", "door", "opaque"),
        ("glazing", "glazing_construction_id", "ext_glazing", "glazed"),
    )
    constructions = []
    for key, assignment, category, construction_class in assignments:
        construction = {
            "key": key,
            "assignment_parameter": assignment,
            "category": category,
            "construction_class": construction_class,
            "properties": {},
            "layers": [
                {
                    "material_key": "test_material",
                    "is_cavity": False,
                    "properties": {"thickness": _field(0.1, "number", 0.001, 1.0)},
                }
            ],
        }
        construction.update(_evidence("Approved {} test construction.".format(key)))
        constructions.append(construction)

    gains = []
    for key, category, subtype, units in (
        ("people", "people", "people", "square_metres_per_person"),
        ("lighting", "lighting", "general", "watts_per_square_metre"),
        ("equipment", "energy", "computers", "watts_per_square_metre"),
    ):
        gain = {
            "key": key,
            "category": category,
            "subtype": subtype,
            "units": units,
            "properties": {
                "name": _field("TEST_{}".format(key.upper()), "string"),
                "variation_profile": _field(
                    {"profile_ref": "test_profile"}, "object"
                ),
            },
        }
        gain.update(_evidence("Approved {} test gain.".format(key)))
        gains.append(gain)

    material = {
        "key": "test_material",
        "category": "other",
        "properties": {
            "description": _field("TEST MATERIAL", "string"),
            "conductivity": _field(0.1, "number", 0.001, 10.0),
        },
    }
    material.update(_evidence("Approved unit-test material."))
    profile = {
        "key": "test_profile",
        "profile_type": "daily",
        "reference": "TEST_PROFILE",
        "modulating": True,
        "units": -1,
        "data": _field([[0.0, 1.0, ""], [24.0, 1.0, ""]], "array"),
    }
    profile.update(_evidence("Approved unit-test profile."))
    exchange = {
        "key": "infiltration",
        "exchange_type": "infiltration",
        "units": "ach",
        "adjacent_condition": "external_air",
        "properties": {
            "name": _field("TEST INFILTRATION", "string"),
            "max_flow": _field(0.1, "number", 0.0, 10.0),
            "variation_profile": _field(
                {"profile_ref": "test_profile"}, "object"
            ),
        },
    }
    exchange.update(_evidence("Approved unit-test air exchange."))
    template = {
        "name": "TEST NEW TEMPLATE",
        "standard": "generic",
        "room_conditions": {"heating_setpoint": _field(20.0, "number", 0.0, 40.0)},
        "system_data": {"conditioned": _field(True, "boolean")},
        "gain_keys": ["people", "lighting", "equipment"],
        "air_exchange_keys": ["infiltration"],
    }
    template.update(_evidence("Approved unit-test thermal template."))
    return {
        "schema_version": "1.0",
        "on_existing": "fail",
        "metadata": {"purpose": "unit test"},
        "profiles": [profile],
        "materials": [material],
        "constructions": constructions,
        "gains": gains,
        "air_exchanges": [exchange],
        "thermal_template": template,
        "apache_system": None,
    }


def _write_manifest(name, payload=None):
    """Write and return one manifest fixture path."""

    path = _test_dir(name) / "reference_model_assets.json"
    path.write_text(
        json.dumps(payload or _valid_manifest_payload(), indent=2), encoding="utf-8"
    )
    return path


class _Profile:
    """Minimal mutable VE profile test double."""

    def __init__(self, identifier, reference, profile_type="daily"):
        """Initialize profile identity and empty data."""

        self.id = identifier
        self.reference = reference
        self.profile_type = profile_type
        self._data = None

    def set_data(self, data):
        """Persist profile data and report success."""

        if self.profile_type == "daily":
            self._data = [
                [row[0], row[1], "-" if row[2] == "" else row[2]]
                for row in data
            ]
        else:
            self._data = json.loads(json.dumps(data))
        return True

    def get_data(self):
        """Return persisted profile data."""

        return self._data

    def is_weekly(self):
        """Report whether this fixture represents a weekly group."""

        return self.profile_type == "weekly"

    def is_yearly(self):
        """Report whether this fixture represents a yearly group."""

        return self.profile_type == "yearly"

    def is_compact(self):
        """Report whether this fixture represents a compact group."""

        return self.profile_type == "compact"

    def is_freeform(self):
        """Report whether this fixture represents a free-form group."""

        return self.profile_type == "freeform"


class _Record:
    """Generic VE gain or air-exchange test double."""

    def __init__(self, identifier):
        """Initialize record identity and empty properties."""

        self.id = identifier
        self._data = {}

    def set(self, data):
        """Persist a VE-style property dictionary."""

        self._data.update(data)

    def get(self):
        """Return the persisted VE-style property dictionary."""

        result = dict(self._data)
        result.setdefault("id", self.id)
        return result


class _Material:
    """Minimal CDB material test double."""

    def __init__(self, identifier):
        """Initialize material identity and properties."""

        self.id = identifier
        self._properties = {}

    def set_properties(self, properties):
        """Persist supplied material properties."""

        self._properties.update(properties)

    def get_properties(self):
        """Return persisted material properties with identity."""

        result = dict(self._properties)
        result["id"] = self.id
        return result


class _Layer:
    """Minimal CDB construction-layer test double."""

    def __init__(self, material_id, is_cavity=False):
        """Initialize layer material identity and properties."""

        self.material_id = material_id
        self.is_cavity = is_cavity
        self._properties = {}

    def set_properties(self, properties):
        """Persist supplied layer properties."""

        self._properties.update(properties)

    def get_properties(self):
        """Return persisted layer properties."""

        return dict(self._properties)

    def get_id(self):
        """Return a stable synthetic layer ID."""

        return self.material_id

    def get_material(self, opaque):
        """Return a material handle exposing the persistent ID."""

        if self.is_cavity:
            return None
        return SimpleNamespace(id=self.material_id)


class _Construction:
    """Minimal layered CDB construction test double."""

    def __init__(self, identifier, category):
        """Initialize construction identity with VE's default layer."""

        self.id = identifier
        self.category = category
        self._properties = {}
        self._layers = [_Layer("DEFAULT-LAYER")]
        self.construction_class = None

    def set_const_class(self, construction_class):
        """Persist the assigned construction class."""

        self.construction_class = construction_class

    def set_properties(self, properties):
        """Persist supplied construction properties."""

        self._properties.update(properties)

    def get_properties(self):
        """Return persisted construction properties."""

        return dict(self._properties)

    def add_layer(self, material_id, is_cavity):
        """Append one material layer to the construction."""

        self._layers.append(_Layer(material_id, is_cavity=is_cavity))

    def delete_layer(self, layer_id):
        """Delete the layer matching the supplied persistent ID."""

        if self.construction_class == "glazed" and len(self._layers) <= 1:
            raise RuntimeError("VE invariant: glazed construction needs one layer")
        self._layers = [
            layer for layer in self._layers if layer.get_id() != layer_id
        ]

    def get_layers(self):
        """Return all persisted construction layers."""

        return list(self._layers)


class _CdbProject:
    """Minimal project CDB supporting creation methods."""

    def __init__(self):
        """Initialize empty material and construction stores."""

        self.materials = []
        self.constructions = []

    def get_material_ids(self, category):
        """Return IDs of all created test materials."""

        return [material.id for material in self.materials]

    def create_material(self, category):
        """Create and store one test material."""

        material = _Material("MAT-{}".format(len(self.materials) + 1))
        self.materials.append(material)
        return material

    def get_material(self, identifier):
        """Return one material by persistent ID."""

        return next(material for material in self.materials if material.id == identifier)

    def create_construction(self, category):
        """Create and store one test construction."""

        construction = _Construction(
            "CON-{}".format(len(self.constructions) + 1), category
        )
        self.constructions.append(construction)
        return construction

    def get_construction_ids(self, construction_class):
        """Return construction IDs for the requested class."""

        return [
            construction.id
            for construction in self.constructions
            if construction.construction_class == construction_class
        ]

    def get_construction(self, identifier, construction_class=None):
        """Return one construction by persistent ID."""

        return next(
            construction
            for construction in self.constructions
            if construction.id == identifier
            and (
                construction_class is None
                or construction.construction_class == construction_class
            )
        )


class _Template:
    """Minimal mutable thermal-template test double."""

    def __init__(self, name):
        """Initialize template name and empty linked data."""

        self.name = name
        self._room_conditions = {}
        self._systems = {}
        self._gains = []
        self._exchanges = []

    def set_room_conditions(self, data):
        """Persist room-condition data."""

        self._room_conditions = dict(data)

    def set_apache_systems(self, data):
        """Persist simplified-system data."""

        self._systems = dict(data)

    def add_gain(self, gain):
        """Attach one created gain."""

        self._gains.append(gain)

    def add_air_exchange(self, exchange):
        """Attach one created air exchange."""

        self._exchanges.append(exchange)

    def apply_changes(self):
        """Simulate persistence of template changes."""

        return None

    def get_room_conditions(self):
        """Return persisted room-condition data."""

        return dict(self._room_conditions)

    def get_apache_systems(self):
        """Return persisted simplified-system data."""

        return dict(self._systems)

    def get_casual_gains(self):
        """Return all linked gains."""

        return list(self._gains)

    def get_air_exchanges(self):
        """Return all linked air exchanges."""

        return list(self._exchanges)


class _Project:
    """Minimal VE project supporting source-traced asset creation."""

    def __init__(self):
        """Initialize empty project-level asset stores."""

        self._profiles = {}
        self._templates = {}
        self._records = 0
        self.last_profile_units = None
        self.profile_creation_order = []
        self.save_profiles_count = 0
        self.created_gain_types = []
        self.created_exchange_types = []
        self._gains = []
        self._exchanges = []

    def profiles(self):
        """Return daily and group profile dictionaries."""

        return self._profiles, {}

    def create_profile(self, profile_type, reference, modulating, units):
        """Create and index one test profile."""

        self.last_profile_units = units
        identifier = "PRO-{}".format(len(self._profiles) + 1)
        profile = _Profile(identifier, reference, profile_type)
        self._profiles[identifier] = profile
        self.profile_creation_order.append(reference)
        return profile

    def save_profiles(self):
        """Report successful profile persistence."""

        self.save_profiles_count += 1
        return True

    def create_casual_gain(self, subtype):
        """Create one generic gain record."""

        self.created_gain_types.append(subtype)
        self._records += 1
        record = _Record("GAIN-{}".format(self._records))
        record._data["type_val"] = {
            "create_people": "people",
            "create_general_lighting": "general",
            "create_computers": "computers",
        }[subtype]
        self._gains.append(record)
        return record

    def casual_gains(self):
        """Return all persisted gain records."""

        return list(self._gains)

    def create_air_exchange(self, exchange_type):
        """Create one generic air-exchange record."""

        self.created_exchange_types.append(exchange_type)
        self._records += 1
        record = _Record("AIR-{}".format(self._records))
        self._exchanges.append(record)
        return record

    def air_exchanges(self):
        """Return all persisted air-exchange records."""

        return list(self._exchanges)

    def thermal_templates(self, assigned=False):
        """Return all project thermal templates by handle."""

        return dict(self._templates)

    def create_thermal_template(self, name):
        """Create and index one new thermal template."""

        template = _Template(name)
        self._templates["TPL-1"] = template
        return template

    def apache_systems(self):
        """Return no pre-existing Apache systems."""

        return []


def _iesve_namespace():
    """Return documented enum layouts used by the provisioner."""

    profile_units_none = object()
    return SimpleNamespace(
        ProfileUnits=SimpleNamespace(none=profile_units_none),
        CasualGain_type=SimpleNamespace(
            people="create_people",
            general_lighting="create_general_lighting",
            computers="create_computers",
        ),
        AirExchange_type=SimpleNamespace(
            infiltration="infiltration",
            mechanical_ventilation="mechanical_ventilation",
        ),
        AdjacentCondition_type=SimpleNamespace(external_air="external_air"),
        AirChange_unit=SimpleNamespace(
            ac_per_h="ach",
            l_per_s_per_person="l_per_s_per_person",
        ),
        VECdbConstruction=SimpleNamespace(delete_layer=lambda *args: None),
        VECdbLayer=SimpleNamespace(get_id=lambda *args: None),
        VECdbProject=SimpleNamespace(
            material_categories=SimpleNamespace(other="other", glass="glass"),
            element_categories=SimpleNamespace(
                wall="wall",
                roof="roof",
                ground_floor="ground_floor",
                partition="partition",
                door="door",
                ext_glazing="ext_glazing",
            ),
            construction_class=SimpleNamespace(opaque="opaque", glazed="glazed"),
        ),
        PeopleGain=SimpleNamespace(PeopleGain_type=SimpleNamespace(people="people")),
        LightingGain=SimpleNamespace(LightingGain_type=SimpleNamespace(general="general")),
        EnergyGain=SimpleNamespace(EnergyGain_type=SimpleNamespace(computers="computers")),
        AirExchange=SimpleNamespace(
            AirExchange_type=SimpleNamespace(infiltration="infiltration"),
            AirChange_unit=SimpleNamespace(ach="ach"),
            AdjacentCondition_type=SimpleNamespace(external_air="external_air"),
        ),
    )


class _DryRunGateway(VeGateway):
    """Gateway proving create-mode preflight performs no VE mutation."""

    def __init__(self, project_path):
        """Initialize a project path and mutation-call counter."""

        self._project_path = Path(project_path)
        self.mutation_calls = 0

    @property
    def project_path(self):
        """Return the synthetic active-project path."""

        return self._project_path

    @property
    def project_name(self):
        """Return the synthetic active-project name."""

        return "Create Mode Dry Run"

    def _unexpected(self):
        """Record and reject any VE operation during dry-run preflight."""

        self.mutation_calls += 1
        raise AssertionError("VE operation must not run during a dry run")

    def check_capabilities(self):
        """Reject capability inspection during a dry run."""

        return self._unexpected()

    def assert_no_existing_generated_rooms(self, expected_names):
        """Reject duplicate-room inspection during a dry run."""

        return self._unexpected()

    def import_geometry(self, gbxml_path):
        """Reject geometry import during a dry run."""

        return self._unexpected()

    def rebuild_adjacencies(self):
        """Reject adjacency mutation during a dry run."""

        return self._unexpected()

    def assign_constructions(self, expected_geometry, parameters):
        """Reject construction assignment during a dry run."""

        return self._unexpected()

    def assign_thermal_template(self, expected_geometry, parameters):
        """Reject template assignment during a dry run."""

        return self._unexpected()

    def assign_hvac_if_configured(self, expected_geometry, parameters):
        """Reject HVAC assignment during a dry run."""

        return self._unexpected()

    def assign_weather(self, weather_file):
        """Reject weather assignment during a dry run."""

        return self._unexpected()

    def snapshot(self, expected_geometry, parameters):
        """Reject VE snapshot extraction during a dry run."""

        return self._unexpected()


class ReferenceModelAssetProvisioningTests(unittest.TestCase):
    """Exercise manifest validation and capability-gated VE creation."""

    def test_ve_float32_readback_is_tolerated_without_masking_real_changes(self):
        """Accept a float32 round trip but reject a meaningful property drift."""

        self.assertTrue(_values_match(0.7, 0.699999988079071))
        self.assertFalse(_values_match(0.7, 0.699))

    def test_reference_glass_uses_the_observed_ve2025_property_schema(self):
        """Do not write opaque-only density into a VE glass material."""

        manifest = load_asset_manifest(
            TEST_ROOT / "config" / "reference_model_assets.json"
        )
        glass = next(
            material
            for material in manifest.materials
            if material.key == "equivalent_glazing_layer"
        )
        properties = glass.raw_properties()
        self.assertNotIn("density", properties)
        self.assertNotIn("specific_heat_capacity", properties)
        self.assertIn("transmittance", properties)
        self.assertIn("visible_transmittance", properties)

    def test_reuse_verified_audits_glass_optical_rounding_to_three_decimals(self):
        """Accept only the exact VE glass 3-decimal canonical value."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        material = payload["materials"][0]
        material["category"] = "glass"
        material["properties"].update(
            {
                "transmittance": _field(0.86156, "number", 0.0, 1.0),
                "visible_transmittance": _field(
                    0.86156, "number", 0.0, 1.0
                ),
            }
        )
        manifest = load_asset_manifest(
            _write_manifest("glass_optical_rounding", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        cdb.materials[0]._properties["transmittance"] = 0.862
        cdb.materials[0]._properties["visible_transmittance"] = 0.862

        receipt = provisioner.provision(manifest)

        warnings = [
            warning
            for warning in receipt.compatibility_warnings
            if warning["code"] == "VE-GLASS-OPTICAL-PROPERTY-ROUNDED-3DP"
        ]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(
            warnings[0]["fields"]["transmittance"]["requested"], 0.86156
        )
        self.assertEqual(
            warnings[0]["fields"]["transmittance"]["canonical_3dp"], 0.862
        )
        cdb.materials[0]._properties["transmittance"] = 0.86
        with self.assertRaises(VeMutationError):
            provisioner.provision(manifest)

    def test_valid_manifest_has_complete_planned_assignments(self):
        """Accept a complete source-traced package with all runtime outputs."""

        manifest = load_asset_manifest(_write_manifest("valid_manifest"))
        self.assertEqual(manifest.validation_errors(), [])
        self.assertEqual(len(manifest.planned_parameter_names), 8)
        self.assertIn("glazing_construction_id", manifest.planned_parameter_names)
        self.assertIn("thermal_template_name", manifest.planned_parameter_names)

    def test_manifest_rejects_unsupported_and_duplicate_profile_contracts(self):
        """Reject ambiguous references and unknown VE profile kinds."""

        unsupported = _valid_manifest_payload()
        unsupported["profiles"][0]["profile_type"] = "hourly_guess"
        with self.assertRaisesRegex(
            ConfigurationError, "unsupported profile_type"
        ):
            load_asset_manifest(
                _write_manifest("unsupported_profile_type", unsupported)
            )

        duplicate = _valid_manifest_payload()
        second = json.loads(json.dumps(duplicate["profiles"][0]))
        second["key"] = "second_profile"
        duplicate["profiles"].append(second)
        with self.assertRaisesRegex(
            ConfigurationError, "duplicate profile references"
        ):
            load_asset_manifest(
                _write_manifest("duplicate_profile_reference", duplicate)
            )

    def test_manifest_rejects_cyclic_profile_groups_before_mutation(self):
        """Keep weekly/yearly dependency cycles outside the VE process."""

        payload = _valid_manifest_payload()
        first = json.loads(json.dumps(payload["profiles"][0]))
        first.update(
            {
                "key": "week_a",
                "reference": "WEEK_A",
                "profile_type": "weekly",
                "data": _field(
                    [{"profile_ref": "week_b"}],
                    "array",
                ),
            }
        )
        second = json.loads(json.dumps(first))
        second.update(
            {
                "key": "week_b",
                "reference": "WEEK_B",
                "data": _field(
                    [{"profile_ref": "week_a"}],
                    "array",
                ),
            }
        )
        payload["profiles"] = [first, second]
        with self.assertRaisesRegex(
            ConfigurationError, "cyclic logical profile references"
        ):
            load_asset_manifest(
                _write_manifest("cyclic_profile_references", payload)
            )

    def test_profile_groups_are_topologically_created_and_read_back(self):
        """Resolve logical daily -> weekly -> yearly IDs in stable layers."""

        payload = _valid_manifest_payload()
        base = payload["profiles"][0]
        daily = json.loads(json.dumps(base))
        daily.update(
            {
                "key": "weekday",
                "reference": "WEEKDAY",
                "data": _field(
                    [[0.0, 0.0, ""], [8.0, 1.0, ""], [24.0, 0.0, ""]],
                    "array",
                ),
            }
        )
        weekly = json.loads(json.dumps(base))
        weekly.update(
            {
                "key": "office_week",
                "reference": "OFFICE_WEEK",
                "profile_type": "weekly",
                "data": _field(
                    [{"profile_ref": "weekday"}] * 7,
                    "array",
                ),
            }
        )
        yearly = json.loads(json.dumps(base))
        yearly.update(
            {
                "key": "office_year",
                "reference": "OFFICE_YEAR",
                "profile_type": "yearly",
                "data": _field(
                    [[{"profile_ref": "office_week"}, 1, 365]],
                    "array",
                ),
            }
        )
        # Deliberately reverse the dependency order.  The provisioner must
        # validate and reorder this graph before creating the first VE object.
        payload["profiles"] = [yearly, weekly, base, daily]
        manifest = load_asset_manifest(
            _write_manifest("profile_dependency_layers", payload)
        )
        project = _Project()
        receipt = IesVeAssetProvisioner(
            _iesve_namespace(), project, _CdbProject()
        ).provision(manifest)

        self.assertEqual(
            project.profile_creation_order,
            ["TEST_PROFILE", "WEEKDAY", "OFFICE_WEEK", "OFFICE_YEAR"],
        )
        self.assertEqual(project.save_profiles_count, 3)
        weekly_profile = next(
            item
            for item in project._profiles.values()
            if item.reference == "OFFICE_WEEK"
        )
        yearly_profile = next(
            item
            for item in project._profiles.values()
            if item.reference == "OFFICE_YEAR"
        )
        self.assertEqual(
            weekly_profile.get_data(),
            [receipt.profile_ids["weekday"]] * 7,
        )
        self.assertEqual(
            yearly_profile.get_data(),
            [[receipt.profile_ids["office_week"], 1, 365]],
        )

    def test_profile_only_public_boundary_reuses_strict_graph_checks(self):
        """Qualify profiles without provisioning unrelated VE asset families."""

        manifest = load_asset_manifest(_write_manifest("profile_only"))
        project = _Project()
        identifiers = IesVeAssetProvisioner(
            _iesve_namespace(), project, None
        ).provision_profiles(manifest.profiles)

        self.assertEqual(identifiers, {"test_profile": "PRO-1"})
        self.assertEqual(project.profile_creation_order, ["TEST_PROFILE"])
        self.assertEqual(project.save_profiles_count, 1)

    def test_profile_only_public_boundary_rejects_empty_plan(self):
        """Never enter the VE profile API with an empty qualification plan."""

        with self.assertRaisesRegex(
            VeMutationError, "At least one profile definition"
        ):
            IesVeAssetProvisioner(
                _iesve_namespace(), _Project(), None
            ).provision_profiles(())

    def test_placeholder_example_is_deliberately_rejected(self):
        """Keep the distributed skeleton incapable of mutating a VE project."""

        example = TEST_ROOT / "config" / "reference_model_assets.example.json"
        with self.assertRaises(ConfigurationError):
            load_asset_manifest(example)

    def test_provisioner_creates_and_reads_back_all_assets(self):
        """Create profiles, CDB assets, gains, exchanges, and template in order."""

        manifest = load_asset_manifest(_write_manifest("provision_all"))
        project = _Project()
        cdb = _CdbProject()
        receipt = IesVeAssetProvisioner(
            _iesve_namespace(), project, cdb
        ).provision(manifest)
        self.assertIsNotNone(project.last_profile_units)
        self.assertNotEqual(project.last_profile_units, -1)
        self.assertEqual(len(receipt.profile_ids), 1)
        self.assertEqual(len(receipt.material_ids), 1)
        self.assertEqual(len(receipt.construction_ids), 6)
        self.assertEqual(len(receipt.gain_ids), 3)
        self.assertEqual(len(receipt.air_exchange_names), 1)
        self.assertEqual(
            project.created_gain_types,
            ["create_people", "create_general_lighting", "create_computers"],
        )
        self.assertEqual(project.created_exchange_types, ["infiltration"])
        self.assertEqual(receipt.template_name, "TEST NEW TEMPLATE")
        self.assertEqual(receipt.template_handle, "TPL-1")
        self.assertEqual(len(receipt.parameter_overrides), 8)

    def test_reuse_verified_is_idempotent_for_all_asset_types(self):
        """Reuse only exact read-back matches without creating duplicates."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        manifest = load_asset_manifest(_write_manifest("reuse_all", payload))
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        first = provisioner.provision(manifest)
        counts = (
            len(project._profiles),
            len(cdb.materials),
            len(cdb.constructions),
            len(project._gains),
            len(project._exchanges),
            len(project._templates),
        )
        second = provisioner.provision(manifest)
        self.assertEqual(
            counts,
            (
                len(project._profiles),
                len(cdb.materials),
                len(cdb.constructions),
                len(project._gains),
                len(project._exchanges),
                len(project._templates),
            ),
        )
        self.assertEqual(first.profile_ids, second.profile_ids)
        self.assertEqual(first.material_ids, second.material_ids)
        self.assertEqual(first.construction_ids, second.construction_ids)
        self.assertEqual(first.gain_ids, second.gain_ids)
        self.assertEqual(first.template_handle, second.template_handle)

    def test_reuse_verified_supports_native_materialless_glazing_cavity(self):
        """Treat a traced cavity as resolved without inventing a material ID."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        glazing = next(
            item for item in payload["constructions"] if item["key"] == "glazing"
        )
        glass = {
            "material_key": "test_material",
            "is_cavity": False,
            "properties": {},
        }
        cavity = {
            "material_key": "test_material",
            "is_cavity": True,
            "properties": {
                "resistance": _field(0.75, "number", 0.000001, 100.0)
            },
        }
        glazing["layers"] = [glass, cavity, glass]
        manifest = load_asset_manifest(
            _write_manifest("reuse_glazing_cavity", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)

        first = provisioner.provision(manifest)
        second = provisioner.provision(manifest)

        self.assertEqual(first.construction_ids, second.construction_ids)
        construction = next(
            item for item in cdb.constructions if item.construction_class == "glazed"
        )
        self.assertEqual(len(construction.get_layers()), 3)
        self.assertIsNone(construction.get_layers()[1].get_material(False))
        self.assertEqual(
            construction.get_layers()[1].get_properties()["resistance"], 0.75
        )

    def test_reuse_verified_reports_native_glazed_thickness_canonicalization(self):
        """Keep the traced thickness while warning on VE's persisted 0.0 value."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        manifest = load_asset_manifest(
            _write_manifest("reuse_native_glazed_thickness", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        first = provisioner.provision(manifest)
        self.assertEqual(first.compatibility_warnings, ())

        glazed = next(
            construction
            for construction in cdb.constructions
            if construction.construction_class == "glazed"
        )
        glazed.get_layers()[0]._properties["thickness"] = 0.0

        second = provisioner.provision(manifest)
        self.assertEqual(len(second.compatibility_warnings), 1)
        warning = second.compatibility_warnings[0]
        self.assertEqual(
            warning["code"], "VE-GLAZED-LAYER-THICKNESS-NOT-PERSISTED"
        )
        self.assertEqual(warning["requested_thickness_m"], 0.1)
        self.assertEqual(warning["ve_readback_thickness_m"], 0.0)
        self.assertEqual(
            second.to_dict()["compatibility_warnings"][0]["code"],
            "VE-GLAZED-LAYER-THICKNESS-NOT-PERSISTED",
        )

    def test_reuse_verified_audits_glazed_vlt_rounding_to_four_decimals(self):
        """Accept only the native four-decimal construction VLT value."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        glazing = next(
            item for item in payload["constructions"] if item["key"] == "glazing"
        )
        glazing["properties"]["visible_light_transmittance"] = _field(
            0.86156, "number", 0.0, 1.0
        )
        manifest = load_asset_manifest(
            _write_manifest("glazed_vlt_rounding", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        construction = next(
            item
            for item in cdb.constructions
            if item.construction_class == "glazed"
        )
        construction._properties["visible_light_transmittance"] = 0.8616

        receipt = provisioner.provision(manifest)

        warnings = [
            warning
            for warning in receipt.compatibility_warnings
            if warning["code"] == "VE-GLAZED-CONSTRUCTION-VLT-ROUNDED-4DP"
        ]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["canonical_4dp"], 0.8616)
        construction._properties["visible_light_transmittance"] = 0.86
        with self.assertRaises(VeMutationError):
            provisioner.provision(manifest)

    def test_reuse_verified_audits_glazed_layer_resistance_rounding_to_five_decimals(
        self,
    ):
        """Accept only the native five-decimal glazed-layer resistance value."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        glazing = next(
            item for item in payload["constructions"] if item["key"] == "glazing"
        )
        glazing["layers"][0]["properties"]["resistance"] = _field(
            0.1588057805304113, "number", 0.0, 100.0
        )
        manifest = load_asset_manifest(
            _write_manifest("glazed_layer_resistance_rounding", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        construction = next(
            item
            for item in cdb.constructions
            if item.construction_class == "glazed"
        )
        layer = construction.get_layers()[0]
        layer._properties["resistance"] = 0.15881

        receipt = provisioner.provision(manifest)

        warnings = [
            warning
            for warning in receipt.compatibility_warnings
            if warning["code"] == "VE-GLAZED-LAYER-RESISTANCE-ROUNDED-5DP"
        ]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["canonical_5dp"], 0.15881)
        layer._properties["resistance"] = 0.1588
        with self.assertRaises(VeMutationError):
            provisioner.provision(manifest)

    def test_reuse_verified_still_rejects_nonzero_glazed_thickness_drift(self):
        """Do not turn the observed zero canonicalization into a broad tolerance."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        manifest = load_asset_manifest(
            _write_manifest("reuse_bad_glazed_thickness", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        glazed = next(
            construction
            for construction in cdb.constructions
            if construction.construction_class == "glazed"
        )
        glazed.get_layers()[0]._properties["thickness"] = 0.05

        with self.assertRaises(VeMutationError):
            provisioner.provision(manifest)

    def test_reuse_verified_rejects_divergent_profile(self):
        """Fail closed when a homonymous reusable profile has different data."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        manifest = load_asset_manifest(
            _write_manifest("reuse_bad_profile", payload)
        )
        project = _Project()
        profile = project.create_profile("daily", "TEST_PROFILE", True, -1)
        profile.set_data([[0.0, 0.0, ""], [24.0, 0.0, ""]])
        with self.assertRaises(VeMutationError):
            IesVeAssetProvisioner(
                _iesve_namespace(), project, _CdbProject()
            ).provision(manifest)

    def test_controlled_gain_reconciliation_repairs_interrupted_old_manifest(self):
        """Repair only an explicitly selected exact-name reusable gain."""

        original = _valid_manifest_payload()
        original["on_existing"] = "reuse_verified"
        original_manifest = load_asset_manifest(
            _write_manifest("gain_reconcile_original", original)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(original_manifest)

        corrected = _valid_manifest_payload()
        corrected["on_existing"] = "reuse_verified"
        equipment = next(
            item for item in corrected["gains"] if item["key"] == "equipment"
        )
        equipment["properties"].update(
            {
                "max_power_consumption": _field(
                    200.0 / 48.0, "number", 0.0, 1000.0
                ),
                "max_sensible_gain": _field(
                    200.0 / 48.0, "number", 0.0, 1000.0
                ),
                "max_latent_gain": _field(0.0, "number", 0.0, 1000.0),
                "radiant_fraction": _field(0.6, "number", 0.0, 1.0),
            }
        )
        corrected_manifest = load_asset_manifest(
            _write_manifest("gain_reconcile_corrected", corrected)
        )

        receipt = provisioner.reconcile_existing_gain(
            corrected_manifest, "equipment"
        )

        self.assertEqual(receipt["status"], "RECONCILED_AND_VERIFIED")
        self.assertTrue(receipt["changed"])
        provisioner.provision(corrected_manifest)
        gain = next(
            item
            for item in project.casual_gains()
            if item.get()["name"] == "TEST_EQUIPMENT"
        )
        self.assertEqual(gain.get()["radiant_fraction"], 0.6)
        self.assertAlmostEqual(
            gain.get()["max_sensible_gain"] * 48.0, 200.0
        )

    def test_zero_latent_energy_gain_field_omission_is_narrowly_audited(self):
        """Accept only VE's observed missing zero field and emit a warning."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        equipment = next(
            item for item in payload["gains"] if item["key"] == "equipment"
        )
        equipment["properties"]["max_latent_gain"] = _field(
            0.0, "number", 0.0, 1000.0
        )
        manifest = load_asset_manifest(
            _write_manifest("energy_zero_latent_omitted", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        gain = next(
            item
            for item in project.casual_gains()
            if item.get()["name"] == "TEST_EQUIPMENT"
        )
        native_get = gain.get
        gain.get = lambda: {
            key: value
            for key, value in native_get().items()
            if key != "max_latent_gain"
        }

        receipt = provisioner.provision(manifest)

        warnings = [
            warning
            for warning in receipt.compatibility_warnings
            if warning["code"] == "VE-ENERGY-GAIN-ZERO-LATENT-NOT-EXPOSED"
        ]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["requested_max_latent_gain"], 0.0)

    def test_zero_gain_profile_canonicalized_to_on_is_narrowly_audited(self):
        """Accept VE's ON profile only when every gain magnitude is exactly zero."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        people = next(
            item for item in payload["gains"] if item["key"] == "people"
        )
        people["properties"]["max_sensible_gain"] = _field(
            0.0, "number", 0.0, 1000.0
        )
        people["properties"]["max_latent_gain"] = _field(
            0.0, "number", 0.0, 1000.0
        )
        manifest = load_asset_manifest(
            _write_manifest("zero_gain_profile_on", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        gain = next(
            item
            for item in project.casual_gains()
            if item.get()["name"] == "TEST_PEOPLE"
        )
        gain._data["variation_profile"] = "ON"

        receipt = provisioner.provision(manifest)

        warnings = [
            warning
            for warning in receipt.compatibility_warnings
            if warning["code"] == "VE-ZERO-GAIN-PROFILE-CANONICALIZED-ON"
        ]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["gain_key"], "people")

    def test_nonzero_gain_profile_canonicalized_to_on_is_rejected(self):
        """Never apply the zero-gain compatibility rule to a non-zero load."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        equipment = next(
            item for item in payload["gains"] if item["key"] == "equipment"
        )
        equipment["properties"]["max_power_consumption"] = _field(
            4.0, "number", 0.0, 1000.0
        )
        equipment["properties"]["max_sensible_gain"] = _field(
            4.0, "number", 0.0, 1000.0
        )
        equipment["properties"]["max_latent_gain"] = _field(
            0.0, "number", 0.0, 1000.0
        )
        manifest = load_asset_manifest(
            _write_manifest("nonzero_gain_profile_on", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        gain = next(
            item
            for item in project.casual_gains()
            if item.get()["name"] == "TEST_EQUIPMENT"
        )
        gain._data["variation_profile"] = "ON"

        with self.assertRaises(VeMutationError):
            provisioner.provision(manifest)

    def test_controlled_air_exchange_reconciliation_repairs_profile(self):
        """Repair only an explicitly selected exact-name reusable exchange."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        manifest = load_asset_manifest(
            _write_manifest("air_exchange_reconcile", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        exchange = project.air_exchanges()[0]
        exchange._data["variation_profile"] = "ON"

        receipt = provisioner.reconcile_existing_air_exchange(
            manifest, "infiltration"
        )

        self.assertEqual(receipt["status"], "RECONCILED_AND_VERIFIED")
        self.assertTrue(receipt["changed"])
        provisioner.provision(manifest)
        self.assertEqual(
            project.air_exchanges()[0].get()["variation_profile"],
            "PRO-1",
        )

    def test_zero_flow_exchange_profile_on_is_narrowly_audited(self):
        """Accept VE's ON profile only for an exchange with exactly zero flow."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        exchange_definition = payload["air_exchanges"][0]
        exchange_definition["properties"]["max_flow"] = _field(
            0.0, "number", 0.0, 10.0
        )
        manifest = load_asset_manifest(
            _write_manifest("zero_flow_exchange_profile_on", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        exchange = project.air_exchanges()[0]
        exchange._data["variation_profile"] = "ON"

        receipt = provisioner.provision(manifest)

        warnings = [
            warning
            for warning in receipt.compatibility_warnings
            if warning["code"] == "VE-ZERO-AIR-FLOW-PROFILE-CANONICALIZED-ON"
        ]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["exchange_key"], "infiltration")

    def test_nonzero_exchange_profile_on_remains_rejected(self):
        """Never apply the zero-flow rule to a non-zero air exchange."""

        payload = _valid_manifest_payload()
        payload["on_existing"] = "reuse_verified"
        manifest = load_asset_manifest(
            _write_manifest("nonzero_exchange_profile_on", payload)
        )
        project = _Project()
        cdb = _CdbProject()
        provisioner = IesVeAssetProvisioner(_iesve_namespace(), project, cdb)
        provisioner.provision(manifest)
        project.air_exchanges()[0]._data["variation_profile"] = "ON"

        with self.assertRaises(VeMutationError):
            provisioner.provision(manifest)

    def test_unsupported_air_exchange_units_are_rejected(self):
        """Reject an air-exchange unit outside the documented integer layout."""

        payload = _valid_manifest_payload()
        payload["air_exchanges"][0]["units"] = "cubic_furlongs_per_fortnight"
        manifest = load_asset_manifest(_write_manifest("bad_air_units", payload))
        with self.assertRaises(VeMutationError):
            IesVeAssetProvisioner(
                _iesve_namespace(), _Project(), _CdbProject()
            ).provision(manifest)

    def test_existing_template_name_blocks_all_creation(self):
        """Reject a template collision before profiles or CDB assets are created."""

        manifest = load_asset_manifest(_write_manifest("duplicate_template"))
        project = _Project()
        project._templates["EXISTING"] = _Template("TEST NEW TEMPLATE")
        cdb = _CdbProject()
        with self.assertRaises(VeMutationError):
            IesVeAssetProvisioner(_iesve_namespace(), project, cdb).provision(manifest)
        self.assertEqual(project._profiles, {})
        self.assertEqual(cdb.materials, [])

    def test_create_mode_dry_run_accepts_planned_runtime_identifiers(self):
        """Allow manifest-planned IDs while keeping all VE calls disabled."""

        manifest_path = _write_manifest("create_mode_dry_run")
        parameters = build_default_registry().with_overrides(
            {
                "asset_provisioning_mode": "create",
                "asset_manifest_file": manifest_path.name,
                "weather_file": {
                    "value": "approved_test_weather.fwt",
                    "source": "Approved unit-test climate evidence",
                    "source_locator": "TEST-WEATHER-001",
                },
            }
        )
        gateway = _DryRunGateway(manifest_path.parent)
        outcome = ReferenceModelWorkflow(parameters, gateway).run(dry_run=True)
        self.assertEqual(outcome.status, ValidationStatus.WARNING)
        self.assertEqual(gateway.mutation_calls, 0)
        asset_results = [
            result
            for result in outcome.validation_results
            if result.control_id == "ASSET-001"
        ]
        self.assertEqual(len(asset_results), 1)
        self.assertEqual(asset_results[0].status, ValidationStatus.PASS)


if __name__ == "__main__":
    unittest.main()
