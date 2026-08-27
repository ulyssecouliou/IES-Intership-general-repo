# -*- coding: utf-8 -*-
"""Tests of the frozen `iesve` enums, and of the correction they enabled.

These values come from a real open VE, not from the documentation:
the table at §6.1.32 of `refs/VEScripts-API-VE2023.pdf` is corrupted by
multi-column text extraction.

The most important test is `test_les_enums_vivent_sur_le_module`: it
locks in the fix for the defect that was causing the probe to fail.
"""

import io
import json
import os

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
_REFERENCE = os.path.join(_RACINE, "refs", "reference-data", "iesve-enums-ve2025.json")
_ADAPTATEUR = os.path.join(_RACINE, "ve_adapter", "test1_adapter.py")


@pytest.fixture(scope="module")
def enums():
    if not os.path.exists(_REFERENCE):
        pytest.skip("enumeres non figes : lancer scripts/freeze_iesve_enums.py")
    with io.open(_REFERENCE, encoding="utf-8") as flux:
        return json.load(flux)


def _source_adaptateur():
    with io.open(_ADAPTATEUR, encoding="utf-8") as flux:
        return flux.read()


# --------------------------------------------------------------------------
# The correction the probe enabled
# --------------------------------------------------------------------------


def test_les_enums_vivent_sur_le_module_pas_sur_vecdbproject():
    """The defect that was causing the probe to fail in VE.

    "Enum 'iesve.<class 'iesve.VECdbProject'>.element_categories'
    introuvable": the adapter was querying the class whereas these
    enums belong to the module.
    """
    source = _source_adaptateur()
    assert "iesve.VECdbProject, 'element_categories'" not in source
    assert "iesve.VECdbProject, 'construction_class'" not in source
    assert "iesve.VECdbProject, 'material_categories'" not in source


def test_material_categories_na_pas_de_membre_opaque(enums):
    """Second error, more subtle: `opaque` belongs to
    `construction_class`, not to `material_categories`. The two enums had
    been confused, and the call would have failed even on the right container."""
    assert "opaque" not in enums["material_categories"]
    assert "opaque" in enums["construction_class"]


def test_ladaptateur_ne_cherche_plus_opaque_dans_les_materiaux():
    source = _source_adaptateur()
    assert "'material_categories', 'opaque'" not in source


# --------------------------------------------------------------------------
# Contents of the probe
# --------------------------------------------------------------------------


def test_les_quatre_enums_utilises_sont_figes(enums):
    for nom in (
        "element_categories",
        "construction_class",
        "material_categories",
        "AirExchange_type",
    ):
        assert enums[nom], nom


@pytest.mark.parametrize(
    "membre,valeur",
    [
        ("roof", 0),
        ("wall", 2),
        ("partition", 3),
        ("ground_floor", 4),
        ("ext_glazing", 6),
        ("int_glazing", 7),
        ("door", 8),
    ],
)
def test_valeurs_delement_categories(enums, membre, valeur):
    assert enums["element_categories"][membre] == valeur


@pytest.mark.parametrize(
    "membre,valeur",
    [("none", -1), ("opaque", 0), ("glazed", 1), ("shade", 4), ("misc", 5)],
)
def test_valeurs_de_construction_class(enums, membre, valeur):
    assert enums["construction_class"][membre] == valeur


def test_les_alias_de_valeur_sont_conserves(enums):
    """`ceiling` and `int_floor` both equal 1, `struct_fram` and
    `struct_frame` both equal 26. These are API aliases: discarding them
    would give an incomplete probe."""
    categories = enums["element_categories"]
    assert categories["ceiling"] == categories["int_floor"] == 1
    assert categories["struct_fram"] == categories["struct_frame"] == 26


def test_soft_landscaping_vaut_bien_3(enums):
    """A hand-written version claimed that value 3 was absent from
    construction_class. The probe shows `soft_landscaping = 3`. This is
    exactly why this file is extracted and not written by hand."""
    assert enums["construction_class"]["soft_landscaping"] == 3


def test_aucun_bruit_herite_dint(enums):
    """IntEnums expose `numerator`, `real`, `bit_length`... Leaving them
    would cause `int` attributes to pass as enum members."""
    for nom in (
        "element_categories",
        "construction_class",
        "material_categories",
        "AirExchange_type",
    ):
        for membre in enums[nom]:
            assert membre not in (
                "numerator",
                "real",
                "imag",
                "denominator",
                "bit_length",
                "to_bytes",
                "values",
                "name",
            )


# --------------------------------------------------------------------------
# Agreement with the documentation
# --------------------------------------------------------------------------

_PDF_API = os.path.join(_RACINE, "refs", "VEScripts-API-VE2023.pdf")

#: Members observed in VE 2025 but absent from §6.1.32.4 (VE 2023). Name them
#: one by one: an open list would let any drift pass through.
#:
#:   struct_fram  -- undocumented alias of struct_frame, same value (26).
#:   surface_tile -- member ADDED after VE 2023 (value 37, after
#:                   double_facade=36). Only API drift observed between the
#:                   two versions across the four employed enums.
MEMBRES_HORS_DOC = frozenset(("struct_fram", "surface_tile"))


def _membres_documentes(nom_enum):
    """Reads the list of members of an enum from §6.1.32.4 of the PDF.

    Args:
        nom_enum: Name of the enum, as it appears at the start of its block.

    Returns:
        set[str] | None: Documented members, or None if unreadable.
    """
    fitz = pytest.importorskip("fitz", reason="PyMuPDF absent")
    if not os.path.exists(_PDF_API):
        pytest.skip("documentation API absente (fichier sous licence)")
    document = fitz.open(_PDF_API)
    try:
        for page in document:
            texte = page.get_text()
            depart = texte.find("\n" + nom_enum + " \n")
            if depart < 0:
                continue
            bloc = texte[depart + len(nom_enum) + 2 :]
            # The block runs until the next enum name. Continuation lines
            # are NOT indented: only the first one is. We therefore stop at
            # the first line without a comma that does not continue an
            # enumeration left open.
            accumule = ""
            for ligne in bloc.splitlines():
                nue = ligne.strip()
                if not nue:
                    continue
                if "," not in nue and not accumule.rstrip().endswith(","):
                    break
                accumule += " " + nue
            return set(m.strip() for m in accumule.split(",") if m.strip())
    finally:
        document.close()
    return None


@pytest.mark.parametrize(
    "nom_enum",
    [
        "construction_class",
        "element_categories",
        "material_categories",
        # Documented elsewhere (§6.1.2 AirExchange, p. 23), not under VECdbProject --
        # which corroborates that the grouping in §6.1.32.4 is not a container.
        "AirExchange_type",
    ],
)
def test_les_membres_releves_concordent_avec_la_documentation(enums, nom_enum):
    """The documentation targets VE 2023, the probe a VE 2025.

    Their agreement is a result, not an assumption: it is what authorises
    saying the API has not drifted between the two versions. A future
    divergence must cause this test to fail, not go unnoticed.
    """
    documentes = _membres_documentes(nom_enum)
    if documentes is None:
        pytest.skip("bloc §6.1.32.4 introuvable pour %s" % nom_enum)
    releves = set(enums[nom_enum])
    assert releves - documentes <= MEMBRES_HORS_DOC
    # Nothing has DISAPPEARED: a documented member missing at runtime
    # would signal a break, not an addition.
    assert not documentes - releves


def test_la_seule_derive_dapi_constatee_est_un_ajout(enums):
    """VE 2023 -> VE 2025: `surface_tile` (37) is added to
    `element_categories`, after `double_facade` (36). No other difference
    across the four employed enums. This test freezes that observation so
    that a future drift becomes visible."""
    documentes = _membres_documentes("element_categories")
    if documentes is None:
        pytest.skip("bloc §6.1.32.4 introuvable")
    ajouts = set(enums["element_categories"]) - documentes - {"struct_fram"}
    assert ajouts == {"surface_tile"}
    assert enums["element_categories"]["surface_tile"] == 37
    assert enums["element_categories"]["double_facade"] == 36


def test_la_documentation_ne_place_pas_opaque_dans_les_materiaux():
    """The corrected error was not a documentation error.

    §6.1.32.4 lists 20 library families for `material_categories` and
    never included `opaque`: the confusion with `construction_class`
    was of our own making.
    """
    documentes = _membres_documentes("material_categories")
    if documentes is None:
        pytest.skip("bloc §6.1.32.4 introuvable")
    assert "opaque" not in documentes


def test_la_provenance_est_declaree(enums):
    """A reference without provenance is worthless in a validation dossier."""
    source = enums["source"]
    assert "Sonde" in source["methode"] or "sonde" in source["methode"]
    assert source["nombre_enums_du_module"] > 100
    assert "6.1.32" in source["pourquoi"]


def test_les_reserves_signalent_le_piege_des_categories(enums):
    texte = " ".join(enums["reserves"])
    assert "BIBLIOTH" in texte.upper()
    assert "construction_class" in texte


# --------------------------------------------------------------------------
# Material properties: the real keys, observed on 2026-08-07
# --------------------------------------------------------------------------

#: Keys returned by `VECdbMaterial.get_properties()` on a new material.
CLES_MATERIAU = (
    "id",
    "description",
    "specific_heat_capacity",
    "category",
    "conductivity",
    "density",
    "vapour_resistivity",
)


def _source_adaptateur_test1():
    with io.open(_ADAPTATEUR, encoding="utf-8") as flux:
        return flux.read()


def test_lepaisseur_nest_plus_ecrite_sur_le_materiau():
    """`thickness` DOES NOT EXIST at material level: thickness belongs to
    the LAYER. Physically correct -- the same material can be used at
    several thicknesses. The module docstring already noted this; the code
    contradicted it, and VE responded "could not convert string to float"."""
    source = _source_adaptateur_test1()
    debut = source.index("def creer_materiau")
    corps = source[debut : debut + 4200]
    assert "'thickness': definition" not in corps


def test_la_description_nest_plus_ecrite_par_set_properties():
    """It is READ but not WRITTEN: after writing it always reads
    "New Python Material". Passing it raised ValueError."""
    source = _source_adaptateur_test1()
    debut = source.index("def creer_materiau")
    corps = source[debut : debut + 4200]
    assert not any(
        quote + "description" + quote + ": definition" in corps for quote in ('"', "'")
    )


def test_les_trois_proprietes_physiques_sont_bien_ecrites():
    source = _source_adaptateur_test1()
    debut = source.index("def creer_materiau")
    corps = source[debut : debut + 4200]
    for cle in ("conductivity", "density", "specific_heat_capacity"):
        assert any(quote + cle + quote + ":" in corps for quote in ('"', "'")), cle


def test_la_relecture_tolere_le_flottant_32_bits():
    """VE stores in float32: 0.16 written comes back as 0.1599999964237213.
    An exact comparison would fail on a write that is nevertheless correct."""
    from ve_adapter import test1_adapter as adaptateur

    class FauxMateriau(object):
        def get_properties(self):
            return {"conductivity": 0.1599999964237213}

    adaptateur._verifier_proprietes_ecrites(
        FauxMateriau(), {"conductivity": 0.16}, "plasterboard"
    )


def test_une_propriete_non_prise_est_signalee():
    """`set_properties` returns nothing and does not always raise: a silently
    ignored write would cause simulation on default values, producing plausible
    numbers."""
    from ve_adapter import test1_adapter as adaptateur

    class MateriauSourd(object):
        def get_properties(self):
            return {"conductivity": 0.0}

    with pytest.raises(RuntimeError, match="non prise"):
        adaptateur._verifier_proprietes_ecrites(
            MateriauSourd(), {"conductivity": 0.16}, "plasterboard"
        )


def test_une_propriete_absente_de_la_relecture_est_signalee():
    from ve_adapter import test1_adapter as adaptateur

    class MateriauMuet(object):
        def get_properties(self):
            return {}

    with pytest.raises(RuntimeError, match="absent de la relecture"):
        adaptateur._verifier_proprietes_ecrites(
            MateriauMuet(), {"conductivity": 0.16}, "x"
        )


def test_lidentifiant_du_materiau_est_une_cle_des_proprietes():
    """`VECdbMaterial` only exposes get_properties, set_properties and
    get_review_summary_string: `materiau.id` does not exist. The identifier is
    a KEY in the dictionary -- observed: {'id': 'PYOP3', ...}."""
    from ve_adapter import test1_adapter as adaptateur

    class MateriauReel(object):
        def get_properties(self):
            return {"id": "PYOP3", "conductivity": 0.16}

    assert adaptateur._identifiant_materiau(MateriauReel()) == "PYOP3"


def test_un_attribut_id_reste_prioritaire():
    """If a VE version added it, it should be used."""
    from ve_adapter import test1_adapter as adaptateur

    class MateriauAvecAttribut(object):
        id = "DIRECT"

        def get_properties(self):
            return {"id": "PARPROPRIETES"}

    assert adaptateur._identifiant_materiau(MateriauAvecAttribut()) == "DIRECT"


def test_un_materiau_sans_identifiant_rend_none():
    """Absence is a result: it is the caller that raises, with the material
    name in the message."""
    from ve_adapter import test1_adapter as adaptateur

    class MateriauMuet(object):
        def get_properties(self):
            return {}

    assert adaptateur._identifiant_materiau(MateriauMuet()) is None


def test_une_relecture_qui_leve_ne_fait_pas_planter():
    from ve_adapter import test1_adapter as adaptateur

    class MateriauCasse(object):
        def get_properties(self):
            raise RuntimeError("indisponible")

    assert adaptateur._identifiant_materiau(MateriauCasse()) is None


# --------------------------------------------------------------------------
# Roof materials: reservation lifted by an independent source
# --------------------------------------------------------------------------

_ISO_52016 = os.path.join(_RACINE, "config", "iso52016_chapter7_confirmed_inputs.json")


def test_les_cp_du_toit_concordent_avec_iso_52016_table_23():
    """The reservation was not lifted by re-reading the same text extraction --
    whose column was shifted -- but by confronting an INDEPENDENT capture
    of Table 23, page 124, whose sha256 is recorded."""
    if not os.path.exists(_ISO_52016):
        pytest.skip("entrees ISO 52016-1 absentes")
    from ve_adapter import test1_adapter as adaptateur

    with io.open(_ISO_52016, encoding="utf-8") as flux:
        source = json.load(flux)
    couches = source["hourly_test_cell"]["lightweight_opaque"][
        "roof_layers_inside_to_outside"
    ]
    iso = dict((c["material"], c) for c in couches)

    for couche in adaptateur.MATERIAUX_LEGERS["toit"]:
        reference = iso[couche["nom"].replace("_toit", "")]
        assert couche["capacite_thermique"] == reference["specific_heat_j_kgk"]
        assert couche["masse_volumique"] == reference["density_kg_m3"]
        assert couche["conductivite"] == reference["conductivity_w_mk"]
        assert couche["epaisseur"] == reference["thickness_m"]


def test_le_toit_na_plus_aucune_valeur_non_confirmee():
    from ve_adapter import test1_adapter as adaptateur

    for masse in adaptateur.MATERIAUX_PAR_MASSE.values():
        for couche in masse["toit"]:
            assert None not in couche.values(), couche["nom"]


def test_lisolant_de_plancher_vaut_zero_comme_le_veut_iso_52016():
    """RESERVATION LIFTED BY A PROBE. ISO 52016-1 gives 0/0 -- IDEAL
    insulator with no mass -- and ASHRAE 140 note (a) requires "the minimum
    the tested software allows, not < 0". The probe of 2026-08-07 shows that
    VE KEEPS 0.0 EXACTLY. Both standards converge: no compromise."""
    from ve_adapter import test1_adapter as adaptateur

    for masse in adaptateur.MATERIAUX_PAR_MASSE.values():
        isolant = masse["plancher"][-1]
        assert isolant["masse_volumique"] == 0.0
        assert isolant["capacite_thermique"] == 0.0


def test_lisolant_concorde_avec_la_table_iso():
    if not os.path.exists(_ISO_52016):
        pytest.skip("entrees ISO 52016-1 absentes")
    from ve_adapter import test1_adapter as adaptateur

    with io.open(_ISO_52016, encoding="utf-8") as flux:
        source = json.load(flux)
    for cle, jeu in (("legere", "lightweight_opaque"), ("lourde", "heavyweight_opaque")):
        iso = source["hourly_test_cell"][jeu]["floor_layers_inside_to_outside"][-1]
        notre = adaptateur.MATERIAUX_PAR_MASSE[cle]["plancher"][-1]
        assert notre["masse_volumique"] == iso["density_kg_m3"]
        assert notre["capacite_thermique"] == iso["specific_heat_j_kgk"]


def test_plus_aucune_valeur_de_materiau_nest_non_confirmee():
    """The original eight None values are all lifted: three by an independent
    ISO source, two by a probe in VE."""
    from ve_adapter import test1_adapter as adaptateur

    for masse in adaptateur.MATERIAUX_PAR_MASSE.values():
        for couches in masse.values():
            for couche in couches:
                assert None not in couche.values(), couche["nom"]


def test_le_releve_qui_a_leve_la_reserve_est_cite():
    """A value placed without its provenance becomes an assumption again."""
    source = _source_adaptateur()
    assert "VE KEEPS 0.0 EXACTLY" in source
    assert "note (a)" in source


# --------------------------------------------------------------------------
# Layer thicknesses: the hole that green hid
# --------------------------------------------------------------------------


def test_lepaisseur_est_posee_sur_la_couche():
    """`add_layer` writes NO thickness. Without this call, the three wall
    layers came back at 1 mm instead of 12, 66 and 9 -- the construction was
    created without raising, and its resistances were wrong."""
    source = _source_adaptateur()
    assert "_poser_epaisseur_de_couche(construction, definition)" in source
    assert any(
        fragment in source
        for fragment in ('set_properties({"thickness"', "set_properties({'thickness'")
    )


def test_lepaisseur_est_relue_apres_ecriture():
    from ve_adapter import test1_adapter as adaptateur

    class Couche(object):
        def __init__(self):
            self.ecrit = None

        def set_properties(self, proprietes):
            self.ecrit = proprietes["thickness"]

        def get_properties(self):
            # VE stores in float32: readback must tolerate rounding.
            return {"thickness": self.ecrit * (1 + 3e-8)}

    class Construction(object):
        def __init__(self):
            self.couche = Couche()

        def get_layers(self):
            return [self.couche]

    construction = Construction()
    adaptateur._poser_epaisseur_de_couche(
        construction, {"nom": "plasterboard", "epaisseur": 0.012}
    )
    assert construction.couche.ecrit == 0.012


def test_une_epaisseur_non_prise_est_signalee():
    """The exact failure mode: VE keeps its default 1 mm."""
    from ve_adapter import test1_adapter as adaptateur

    class CoucheSourde(object):
        def set_properties(self, proprietes):
            pass

        def get_properties(self):
            return {"thickness": adaptateur.EPAISSEUR_PAR_DEFAUT_VE_M}

    class Construction(object):
        def get_layers(self):
            return [CoucheSourde()]

    with pytest.raises(RuntimeError, match="sans rien signaler"):
        adaptateur._poser_epaisseur_de_couche(
            Construction(), {"nom": "plasterboard", "epaisseur": 0.012}
        )


def test_une_couche_introuvable_est_signalee():
    from ve_adapter import test1_adapter as adaptateur

    class ConstructionVide(object):
        def get_layers(self):
            return []

    with pytest.raises(RuntimeError, match="introuvable"):
        adaptateur._poser_epaisseur_de_couche(
            ConstructionVide(), {"nom": "x", "epaisseur": 0.012}
        )


def test_la_resistance_du_mur_reproduit_la_table_iso():
    """THE end-to-end check. Sum of e/lambda for our three layers against
    `wall_total_layer_resistance_m2k_w` from ISO 52016-1 Table 23. If a
    thickness or conductivity drifted, this total would show it."""
    if not os.path.exists(_ISO_52016):
        pytest.skip("entrees ISO 52016-1 absentes")
    from ve_adapter import test1_adapter as adaptateur

    with io.open(_ISO_52016, encoding="utf-8") as flux:
        source = json.load(flux)

    for cle, jeu, paroi, champ in (
        ("legere", "lightweight_opaque", "mur", "wall_total_layer_resistance_m2k_w"),
        ("lourde", "heavyweight_opaque", "mur", "wall_total_layer_resistance_m2k_w"),
    ):
        attendue = source["hourly_test_cell"][jeu][champ]
        notre = sum(
            c["epaisseur"] / c["conductivite"]
            for c in adaptateur.MATERIAUX_PAR_MASSE[cle][paroi]
        )
        assert abs(notre - attendue) < 1e-3, (cle, notre, attendue)


def test_la_resistance_du_toit_reproduit_la_table_iso():
    if not os.path.exists(_ISO_52016):
        pytest.skip("entrees ISO 52016-1 absentes")
    from ve_adapter import test1_adapter as adaptateur

    with io.open(_ISO_52016, encoding="utf-8") as flux:
        source = json.load(flux)
    jeu = source["hourly_test_cell"]["lightweight_opaque"]
    attendue = jeu["roof_total_layer_resistance_m2k_w"]
    notre = sum(
        c["epaisseur"] / c["conductivite"] for c in adaptateur.MATERIAUX_LEGERS["toit"]
    )

    # TOLERANCE AT 2e-3, AND HERE IS WHY. The ISO table is internally
    # inconsistent on the roof: it announces a total of 2.992 whereas the
    # sum of ITS OWN layer resistances (0.063 + 2.794 + 0.136) gives 2.993,
    # and the exact e/lambda calculation gives 2.993214. Its insulation layer
    # is listed as 2.794 where 0.1118 / 0.04 equals exactly 2.795 -- a
    # round-down, not to nearest.
    #
    # Our values reproduce the EXACT calculation. The 1.2e-3 discrepancy
    # therefore comes from the rounding in the published table, not from our
    # layers. Widening the tolerance without saying so would have hidden this
    # information.
    somme_des_couches_annoncees = sum(
        c["resistance_m2k_w"] for c in jeu["roof_layers_inside_to_outside"]
    )
    # Threshold at 5e-4: the discrepancy is 1e-3 in exact arithmetic, but
    # 0.00099999... in floating point. Testing >= 1e-3 would fail on rounding.
    assert (
        abs(somme_des_couches_annoncees - attendue) > 5e-4
    ), "la table est redevenue coherente : resserrer la tolerance"
    assert abs(notre - attendue) < 2e-3, (notre, attendue)
