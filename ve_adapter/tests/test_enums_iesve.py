# -*- coding: utf-8 -*-
"""Tests des enumeres `iesve` figes, et de la correction qu'ils ont permise.

Ces valeurs viennent d'une VE reellement ouverte, pas de la documentation :
le tableau §6.1.32 de `refs/VEScripts-API-VE2023.pdf` est corrompu par
l'extraction texte multi-colonnes.

Le test le plus important est `test_les_enums_vivent_sur_le_module` : il
verrouille la correction du defaut qui faisait echouer la sonde.
"""

import io
import json
import os

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
_REFERENCE = os.path.join(_RACINE, 'refs', 'reference-data',
                          'iesve-enums-ve2025.json')
_ADAPTATEUR = os.path.join(_RACINE, 've_adapter', 'test1_adapter.py')


@pytest.fixture(scope='module')
def enums():
    if not os.path.exists(_REFERENCE):
        pytest.skip(u'enumeres non figes : lancer scripts/freeze_iesve_enums.py')
    with io.open(_REFERENCE, encoding='utf-8') as flux:
        return json.load(flux)


def _source_adaptateur():
    with io.open(_ADAPTATEUR, encoding='utf-8') as flux:
        return flux.read()


# --------------------------------------------------------------------------
# La correction que la sonde a permise
# --------------------------------------------------------------------------

def test_les_enums_vivent_sur_le_module_pas_sur_vecdbproject():
    """Le defaut qui faisait echouer la sonde dans VE.

    « Enum 'iesve.<class 'iesve.VECdbProject'>.element_categories'
    introuvable » : l'adaptateur interrogeait la classe alors que ces
    enumeres appartiennent au module.
    """
    source = _source_adaptateur()
    assert "iesve.VECdbProject, 'element_categories'" not in source
    assert "iesve.VECdbProject, 'construction_class'" not in source
    assert "iesve.VECdbProject, 'material_categories'" not in source


def test_material_categories_na_pas_de_membre_opaque(enums):
    """Seconde erreur, plus subtile : `opaque` appartient a
    `construction_class`, pas a `material_categories`. Les deux enums avaient
    ete confondus, et l'appel aurait echoue meme sur le bon conteneur."""
    assert 'opaque' not in enums['material_categories']
    assert 'opaque' in enums['construction_class']


def test_ladaptateur_ne_cherche_plus_opaque_dans_les_materiaux():
    source = _source_adaptateur()
    assert "'material_categories', 'opaque'" not in source


# --------------------------------------------------------------------------
# Contenu du releve
# --------------------------------------------------------------------------

def test_les_quatre_enums_utilises_sont_figes(enums):
    for nom in ('element_categories', 'construction_class',
                'material_categories', 'AirExchange_type'):
        assert enums[nom], nom


@pytest.mark.parametrize('membre,valeur', [
    ('roof', 0), ('wall', 2), ('partition', 3), ('ground_floor', 4),
    ('ext_glazing', 6), ('int_glazing', 7), ('door', 8)])
def test_valeurs_delement_categories(enums, membre, valeur):
    assert enums['element_categories'][membre] == valeur


@pytest.mark.parametrize('membre,valeur', [
    ('none', -1), ('opaque', 0), ('glazed', 1), ('shade', 4), ('misc', 5)])
def test_valeurs_de_construction_class(enums, membre, valeur):
    assert enums['construction_class'][membre] == valeur


def test_les_alias_de_valeur_sont_conserves(enums):
    """`ceiling` et `int_floor` valent tous deux 1, `struct_fram` et
    `struct_frame` valent 26. Ce sont des alias de l'API : les ecarter
    donnerait un releve incomplet."""
    categories = enums['element_categories']
    assert categories['ceiling'] == categories['int_floor'] == 1
    assert categories['struct_fram'] == categories['struct_frame'] == 26


def test_soft_landscaping_vaut_bien_3(enums):
    """Une version ecrite a la main affirmait que la valeur 3 etait absente de
    construction_class. Le releve montre `soft_landscaping = 3`. C'est
    exactement pourquoi ce fichier est extrait et non redige."""
    assert enums['construction_class']['soft_landscaping'] == 3


def test_aucun_bruit_herite_dint(enums):
    """Les IntEnum exposent `numerator`, `real`, `bit_length`... Les laisser
    ferait passer des attributs de `int` pour des membres d'enumere."""
    for nom in ('element_categories', 'construction_class',
                'material_categories', 'AirExchange_type'):
        for membre in enums[nom]:
            assert membre not in ('numerator', 'real', 'imag', 'denominator',
                                  'bit_length', 'to_bytes', 'values', 'name')


# --------------------------------------------------------------------------
# Concordance avec la documentation
# --------------------------------------------------------------------------

_PDF_API = os.path.join(_RACINE, 'refs', 'VEScripts-API-VE2023.pdf')

#: Membres releves en VE 2025 mais absents de §6.1.32.4 (VE 2023). Les nommer
#: un par un : une liste ouverte laisserait passer n'importe quelle derive.
#:
#:   struct_fram  -- alias non documente de struct_frame, meme valeur (26).
#:   surface_tile -- membre AJOUTE apres VE 2023 (valeur 37, apres
#:                   double_facade=36). Seule derive d'API constatee entre les
#:                   deux versions sur les quatre enumeres employes.
MEMBRES_HORS_DOC = frozenset(('struct_fram', 'surface_tile'))


def _membres_documentes(nom_enum):
    """Lit la liste des membres d'un enum dans §6.1.32.4 du PDF.

    Args:
        nom_enum: Nom de l'enum, tel qu'il figure en tete de bloc.

    Returns:
        set[str] | None: Membres documentes, ou None si illisible.
    """
    fitz = pytest.importorskip('fitz', reason=u'PyMuPDF absent')
    if not os.path.exists(_PDF_API):
        pytest.skip(u'documentation API absente (fichier sous licence)')
    document = fitz.open(_PDF_API)
    try:
        for page in document:
            texte = page.get_text()
            depart = texte.find('\n' + nom_enum + ' \n')
            if depart < 0:
                continue
            bloc = texte[depart + len(nom_enum) + 2:]
            # Le bloc court jusqu'au prochain nom d'enum. Les lignes de
            # continuation ne sont PAS indentees : seule la premiere l'est.
            # On s'arrete donc a la premiere ligne sans virgule qui ne
            # prolonge pas une enumeration laissee ouverte.
            accumule = ''
            for ligne in bloc.splitlines():
                nue = ligne.strip()
                if not nue:
                    continue
                if ',' not in nue and not accumule.rstrip().endswith(','):
                    break
                accumule += ' ' + nue
            return set(m.strip() for m in accumule.split(',') if m.strip())
    finally:
        document.close()
    return None


@pytest.mark.parametrize('nom_enum', [
    'construction_class', 'element_categories', 'material_categories',
    # Documente ailleurs (§6.1.2 AirExchange, p. 23), pas sous VECdbProject --
    # ce qui corrobore que le regroupement de §6.1.32.4 n'est pas un conteneur.
    'AirExchange_type'])
def test_les_membres_releves_concordent_avec_la_documentation(enums, nom_enum):
    """La documentation vise VE 2023, le releve une VE 2025.

    Leur concordance est un resultat, pas une hypothese : c'est elle qui
    autorise a dire que l'API n'a pas derive entre les deux versions. Une
    divergence future doit faire echouer ce test, pas passer inapercue.
    """
    documentes = _membres_documentes(nom_enum)
    if documentes is None:
        pytest.skip(u'bloc §6.1.32.4 introuvable pour %s' % nom_enum)
    releves = set(enums[nom_enum])
    assert releves - documentes <= MEMBRES_HORS_DOC
    # Rien n'a DISPARU : un membre documente qui manquerait a l'execution
    # signalerait une rupture, pas un ajout.
    assert not documentes - releves


def test_la_seule_derive_dapi_constatee_est_un_ajout(enums):
    """VE 2023 -> VE 2025 : `surface_tile` (37) s'ajoute a
    `element_categories`, apres `double_facade` (36). Aucun autre ecart sur les
    quatre enumeres employes. Ce test fige ce constat pour qu'une derive
    ulterieure se voie."""
    documentes = _membres_documentes('element_categories')
    if documentes is None:
        pytest.skip(u'bloc §6.1.32.4 introuvable')
    ajouts = set(enums['element_categories']) - documentes - {'struct_fram'}
    assert ajouts == {'surface_tile'}
    assert enums['element_categories']['surface_tile'] == 37
    assert enums['element_categories']['double_facade'] == 36


def test_la_documentation_ne_place_pas_opaque_dans_les_materiaux():
    """L'erreur corrigee n'etait pas une erreur de documentation.

    §6.1.32.4 liste 20 familles de bibliotheque pour `material_categories` et
    n'y a jamais fait figurer `opaque` : la confusion avec `construction_class`
    etait de notre fait.
    """
    documentes = _membres_documentes('material_categories')
    if documentes is None:
        pytest.skip(u'bloc §6.1.32.4 introuvable')
    assert 'opaque' not in documentes


def test_la_provenance_est_declaree(enums):
    """Un referentiel sans provenance ne vaut rien dans un dossier de
    validation."""
    source = enums['source']
    assert 'Sonde' in source['methode'] or 'sonde' in source['methode']
    assert source['nombre_enums_du_module'] > 100
    assert '6.1.32' in source['pourquoi']


def test_les_reserves_signalent_le_piege_des_categories(enums):
    texte = u' '.join(enums['reserves'])
    assert 'BIBLIOTH' in texte.upper()
    assert 'construction_class' in texte


# --------------------------------------------------------------------------
# Proprietes de materiau : les cles reelles, relevees le 2026-08-07
# --------------------------------------------------------------------------

#: Cles rendues par `VECdbMaterial.get_properties()` sur un materiau neuf.
CLES_MATERIAU = ('id', 'description', 'specific_heat_capacity', 'category',
                 'conductivity', 'density', 'vapour_resistivity')


def _source_adaptateur_test1():
    with io.open(_ADAPTATEUR, encoding='utf-8') as flux:
        return flux.read()


def test_lepaisseur_nest_plus_ecrite_sur_le_materiau():
    """`thickness` N EXISTE PAS au niveau materiau : l epaisseur appartient a
    la COUCHE. Physiquement juste — un meme materiau sert a plusieurs
    epaisseurs. La docstring du module le notait deja ; le code la
    contredisait, et VE repondait « could not convert string to float »."""
    source = _source_adaptateur_test1()
    debut = source.index('def creer_materiau')
    corps = source[debut:debut + 4200]
    assert "'thickness': definition" not in corps


def test_la_description_nest_plus_ecrite_par_set_properties():
    """Elle se LIT mais ne s ECRIT pas : apres ecriture elle vaut toujours
    « New Python Material ». La passer levait la ValueError."""
    source = _source_adaptateur_test1()
    debut = source.index('def creer_materiau')
    corps = source[debut:debut + 4200]
    assert "'description': definition" not in corps


def test_les_trois_proprietes_physiques_sont_bien_ecrites():
    source = _source_adaptateur_test1()
    debut = source.index('def creer_materiau')
    corps = source[debut:debut + 4200]
    for cle in ('conductivity', 'density', 'specific_heat_capacity'):
        assert "'%s':" % cle in corps, cle


def test_la_relecture_tolere_le_flottant_32_bits():
    """VE stocke en float32 : 0,16 ecrit ressort en 0,1599999964237213. Une
    comparaison exacte echouerait sur une ecriture pourtant correcte."""
    from ve_adapter import test1_adapter as adaptateur

    class FauxMateriau(object):
        def get_properties(self):
            return {'conductivity': 0.1599999964237213}

    adaptateur._verifier_proprietes_ecrites(
        FauxMateriau(), {'conductivity': 0.16}, 'plasterboard')


def test_une_propriete_non_prise_est_signalee():
    """`set_properties` ne rend rien et ne leve pas toujours : une ecriture
    ignoree ferait simuler sur des valeurs par defaut, en produisant des
    nombres credibles."""
    from ve_adapter import test1_adapter as adaptateur

    class MateriauSourd(object):
        def get_properties(self):
            return {'conductivity': 0.0}

    with pytest.raises(RuntimeError, match='non prise'):
        adaptateur._verifier_proprietes_ecrites(
            MateriauSourd(), {'conductivity': 0.16}, 'plasterboard')


def test_une_propriete_absente_de_la_relecture_est_signalee():
    from ve_adapter import test1_adapter as adaptateur

    class MateriauMuet(object):
        def get_properties(self):
            return {}

    with pytest.raises(RuntimeError, match='absent de la relecture'):
        adaptateur._verifier_proprietes_ecrites(
            MateriauMuet(), {'conductivity': 0.16}, 'x')


def test_lidentifiant_du_materiau_est_une_cle_des_proprietes():
    """`VECdbMaterial` n expose que get_properties, set_properties et
    get_review_summary_string : `materiau.id` n existe pas. L identifiant est
    une CLE du dictionnaire — releve : {'id': 'PYOP3', ...}."""
    from ve_adapter import test1_adapter as adaptateur

    class MateriauReel(object):
        def get_properties(self):
            return {'id': 'PYOP3', 'conductivity': 0.16}

    assert adaptateur._identifiant_materiau(MateriauReel()) == 'PYOP3'


def test_un_attribut_id_reste_prioritaire():
    """Si une version de VE l ajoutait, autant s en servir."""
    from ve_adapter import test1_adapter as adaptateur

    class MateriauAvecAttribut(object):
        id = 'DIRECT'

        def get_properties(self):
            return {'id': 'PARPROPRIETES'}

    assert adaptateur._identifiant_materiau(
        MateriauAvecAttribut()) == 'DIRECT'


def test_un_materiau_sans_identifiant_rend_none():
    """L absence est un resultat : c est l appelant qui leve, avec le nom du
    materiau dans le message."""
    from ve_adapter import test1_adapter as adaptateur

    class MateriauMuet(object):
        def get_properties(self):
            return {}

    assert adaptateur._identifiant_materiau(MateriauMuet()) is None


def test_une_relecture_qui_leve_ne_fait_pas_planter():
    from ve_adapter import test1_adapter as adaptateur

    class MateriauCasse(object):
        def get_properties(self):
            raise RuntimeError('indisponible')

    assert adaptateur._identifiant_materiau(MateriauCasse()) is None


# --------------------------------------------------------------------------
# Materiaux du toit : reserve levee par une source independante
# --------------------------------------------------------------------------

_ISO_52016 = os.path.join(_RACINE, 'config',
                          'iso52016_chapter7_confirmed_inputs.json')


def test_les_cp_du_toit_concordent_avec_iso_52016_table_23():
    """La reserve n a pas ete levee en relisant la meme extraction texte —
    dont la colonne etait decalee — mais en confrontant une capture
    INDEPENDANTE de la Table 23, page 124, dont le sha256 est consigne."""
    if not os.path.exists(_ISO_52016):
        pytest.skip(u'entrees ISO 52016-1 absentes')
    from ve_adapter import test1_adapter as adaptateur
    with io.open(_ISO_52016, encoding='utf-8') as flux:
        source = json.load(flux)
    couches = source['hourly_test_cell']['lightweight_opaque'][
        'roof_layers_inside_to_outside']
    iso = dict((c['material'], c) for c in couches)

    for couche in adaptateur.MATERIAUX_LEGERS['toit']:
        reference = iso[couche['nom'].replace('_toit', '')]
        assert couche['capacite_thermique'] == reference['specific_heat_j_kgk']
        assert couche['masse_volumique'] == reference['density_kg_m3']
        assert couche['conductivite'] == reference['conductivity_w_mk']
        assert couche['epaisseur'] == reference['thickness_m']


def test_le_toit_na_plus_aucune_valeur_non_confirmee():
    from ve_adapter import test1_adapter as adaptateur
    for masse in adaptateur.MATERIAUX_PAR_MASSE.values():
        for couche in masse['toit']:
            assert None not in couche.values(), couche['nom']


def test_lisolant_de_plancher_vaut_zero_comme_le_veut_iso_52016():
    """RESERVE LEVEE PAR UN RELEVE. ISO 52016-1 donne 0/0 — isolant IDEAL sans
    masse — et ASHRAE 140 note (a) impose « le minimum que le logiciel teste
    autorise, pas < 0 ». Le releve du 2026-08-07 montre que VE CONSERVE 0,0
    exactement. Les deux normes convergent : aucun compromis."""
    from ve_adapter import test1_adapter as adaptateur
    for masse in adaptateur.MATERIAUX_PAR_MASSE.values():
        isolant = masse['plancher'][-1]
        assert isolant['masse_volumique'] == 0.0
        assert isolant['capacite_thermique'] == 0.0


def test_lisolant_concorde_avec_la_table_iso():
    if not os.path.exists(_ISO_52016):
        pytest.skip(u'entrees ISO 52016-1 absentes')
    from ve_adapter import test1_adapter as adaptateur
    with io.open(_ISO_52016, encoding='utf-8') as flux:
        source = json.load(flux)
    for cle, jeu in (('legere', 'lightweight_opaque'),
                     ('lourde', 'heavyweight_opaque')):
        iso = source['hourly_test_cell'][jeu][
            'floor_layers_inside_to_outside'][-1]
        notre = adaptateur.MATERIAUX_PAR_MASSE[cle]['plancher'][-1]
        assert notre['masse_volumique'] == iso['density_kg_m3']
        assert notre['capacite_thermique'] == iso['specific_heat_j_kgk']


def test_plus_aucune_valeur_de_materiau_nest_non_confirmee():
    """Les huit None du depart sont tous leves : trois par une source ISO
    independante, deux par un releve dans VE."""
    from ve_adapter import test1_adapter as adaptateur
    for masse in adaptateur.MATERIAUX_PAR_MASSE.values():
        for couches in masse.values():
            for couche in couches:
                assert None not in couche.values(), couche['nom']


def test_le_releve_qui_a_leve_la_reserve_est_cite():
    """Une valeur posee sans sa provenance redevient une supposition."""
    source = _source_adaptateur()
    assert 'VE CONSERVE 0,0 EXACTEMENT' in source
    assert 'note (a)' in source
