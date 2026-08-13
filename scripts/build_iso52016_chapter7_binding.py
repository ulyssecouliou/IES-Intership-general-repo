# -*- coding: utf-8 -*-
u"""Écrit l'artefact de liaison normalisé de la cellule d'essai du chapitre 7.

POURQUOI CE SCRIPT EXISTE. Le manifeste d'entrées déléguées ne consomme jamais
la source primaire : il consomme un artefact normalisé, lié à l'empreinte exacte
de cette source. Cet artefact doit donc être **reproductible** — reconstructible
à l'identique depuis la source — sinon la chaîne de preuve s'arrête à un fichier
que personne ne sait refaire.

CE QU'IL NE FAIT PAS. Il ne convertit pas d'unités, ne complète aucune valeur
absente et ne choisit aucune convention. Il transcrit, réordonne les couches dans
le sens que le contrat attend, et **déclare** le seul champ que la source ne
porte pas.

LA VALEUR PROVISOIRE. `config/iso52016_chapter7_confirmed_inputs.json` ne porte
aucune émissivité infrarouge, que le contrat exige. Plutôt que d'en inventer une,
le script la dérive des coefficients radiatifs que la source porte déjà, puis la
déclare dans `declared_provisional_values` avec sa dérivation, son hypothèse et
ce qui la lève. Le chargeur refuse une telle déclaration si l'artefact
n'interdit pas simultanément toute revendication de conformité, et le contrat
générateur du Test 2A la transforme en bloqueur de verdict. Une valeur
provisoire rend la chaîne exécutable ; elle ne fonde jamais un résultat.
"""

from __future__ import print_function

import argparse
import hashlib
import io
import json
import os
import sys


_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RACINE)

#: Constante de Stefan-Boltzmann, W/(m2 K4).
SIGMA = 5.670374419e-8

#: Températures de référence supposées pour les coefficients radiatifs de la
#: source. La source ne les énonce pas : c'est l'hypothèse à confirmer.
T_INTERIEUR_K = 293.15
T_EXTERIEUR_K = 273.15

#: Identifiants attendus par le contrat normalisé.
SCHEMA_ID = 'sia4010.iso52016_chapter7_test_cell.v1'
SCHEMA_VERSION = '1.0'


def _empreinte(chemin):
    u"""Renvoie le SHA-256 d'un fichier.

    Args:
        chemin: Chemin absolu du fichier.

    Returns:
        str: Empreinte hexadécimale minuscule.
    """
    digest = hashlib.sha256()
    with open(chemin, 'rb') as flux:
        for bloc in iter(lambda: flux.read(65536), b''):
            digest.update(bloc)
    return digest.hexdigest()


def emissivite_derivee(coefficient_radiatif, temperature_k):
    u"""Dérive une émissivité d'un coefficient radiatif linéarisé.

    La linéarisation usuelle du transfert radiatif s'écrit
    h_r = 4 epsilon sigma T^3, d'où epsilon = h_r / (4 sigma T^3).

    Args:
        coefficient_radiatif: h_r en W/(m2 K).
        temperature_k: Température de référence supposée, en K.

    Returns:
        float: Émissivité dérivée, sans unité.
    """
    return coefficient_radiatif / (4.0 * SIGMA * temperature_k ** 3)


def _construction(identifiant, couches_interieur_vers_exterieur, emissivite,
                  absorptance):
    u"""Transcrit une construction opaque dans le sens attendu par le contrat.

    La source liste les couches de l'intérieur vers l'extérieur ; le contrat
    normalisé les attend de l'extérieur vers l'intérieur. Le renversement est
    le seul traitement appliqué.

    Args:
        identifiant: Identifiant stable de la construction.
        couches_interieur_vers_exterieur: Couches telles que la source les liste.
        emissivite: Émissivité provisoire dérivée, appliquée aux deux faces.
        absorptance: Absorptance solaire que la source énonce.

    Returns:
        dict: Bloc de construction normalisé.
    """
    return {
        'construction_id': identifiant,
        'layers_outside_to_inside': [
            {
                'material_id': couche['material'],
                'thickness_m': couche['thickness_m'],
                'conductivity_w_mk': couche['conductivity_w_mk'],
                'density_kg_m3': couche['density_kg_m3'],
                'specific_heat_j_kgk': couche['specific_heat_j_kgk'],
            }
            for couche in reversed(couches_interieur_vers_exterieur)
        ],
        'surface_properties': {
            'inside_ir_emissivity': emissivite,
            'outside_ir_emissivity': emissivite,
            'inside_solar_absorptance': absorptance,
            'outside_solar_absorptance': absorptance,
        },
    }


def construire(chemin_source):
    u"""Construit la charge utile de l'artefact de liaison.

    Args:
        chemin_source: Chemin absolu de `iso52016_chapter7_confirmed_inputs.json`.

    Returns:
        dict: Charge utile prête à écrire.

    Raises:
        AssertionError: Si les deux dérivations d'émissivité ne convergent pas,
            plutôt que d'écrire une valeur qu'un seul calcul soutient.
    """
    with io.open(chemin_source, encoding='utf-8') as flux:
        source = json.load(flux)
    cellule = source['hourly_test_cell']
    geometrie = cellule['geometry']
    fenetres = geometrie['windows']
    bornes = cellule['solar_and_boundary_conditions']
    coefficients = bornes['combined_surface_coefficients_w_m2k']
    detail = bornes['surface_coefficients_w_m2k']
    absorptance = bornes['opaque_solar_absorptance']

    # La source donne les parts radiatives par orientation. Elles sont égales
    # sur les trois, et la dérivation ne tient que si elles le restent : une
    # source révisée qui les différencierait invaliderait l'émissivité unique.
    radiatifs = {}
    for face in ('internal', 'external'):
        valeurs = set(detail['%s_radiative' % face].values())
        assert len(valeurs) == 1, (face, valeurs)
        radiatifs[face] = valeurs.pop()

    # Vérification de cohérence de la source elle-même : chaque coefficient
    # combiné doit valoir la somme de sa part convective et de sa part
    # radiative. Les quatre tombent exactement ; un écart signalerait une
    # transcription fautive avant qu'elle ne se propage.
    for cle_combinee, face, orientation in (
        ('wall_internal_horizontal', 'internal', 'horizontal'),
        ('roof_internal_upwards', 'internal', 'upwards'),
        ('floor_internal_downwards', 'internal', 'downwards'),
        ('external_all_directions', 'external', 'horizontal'),
    ):
        somme = (detail['%s_convective' % face][orientation]
                 + detail['%s_radiative' % face][orientation])
        assert abs(somme - coefficients[cle_combinee]) < 1e-9, (
            cle_combinee, somme, coefficients[cle_combinee])

    interieur = emissivite_derivee(radiatifs['internal'], T_INTERIEUR_K)
    exterieur = emissivite_derivee(radiatifs['external'], T_EXTERIEUR_K)
    assert abs(interieur - exterieur) < 0.01, (interieur, exterieur)
    emissivite = round((interieur + exterieur) / 2.0, 2)

    leger = cellule['lightweight_opaque']
    return {
        'schema_id': SCHEMA_ID,
        'schema_version': SCHEMA_VERSION,
        'primary_source_sha256': _empreinte(chemin_source),
        # Relatif à la racine du dépôt : l'empreinte est ce qui lie
        # réellement l'artefact à sa source, le chemin n'est qu'un repère,
        # et un chemin absolu porterait le nom d'utilisateur d'une machine.
        'primary_source_path': os.path.relpath(
            chemin_source, _RACINE).replace(os.sep, '/'),
        'source_locator': cellule['source_locator'],
        'cell': {
            'width_m': geometrie['width_m'],
            'depth_m': geometrie['depth_m'],
            'height_m': geometrie['height_m'],
            'south_windows': {
                'count': fenetres['count'],
                'width_m': fenetres['width_m'],
                'height_m': fenetres['height_m'],
                'sill_m': fenetres['sill_m'],
                'side_margin_m': fenetres['side_margin_m'],
                'gap_m': fenetres['gap_m'],
            },
        },
        'surface_coefficients_w_m2k': {
            'wall_inside_horizontal': coefficients['wall_internal_horizontal'],
            'roof_inside_upwards': coefficients['roof_internal_upwards'],
            'floor_inside_downwards': coefficients['floor_internal_downwards'],
            'external_all_directions': coefficients['external_all_directions'],
        },
        'lightweight_opaque_constructions': {
            'external_wall': _construction(
                'ISO_CH7_LW_EXTERNAL_WALL',
                leger['wall_layers_inside_to_outside'],
                emissivite, absorptance),
            'roof': _construction(
                'ISO_CH7_LW_ROOF',
                leger['roof_layers_inside_to_outside'],
                emissivite, absorptance),
            'floor': _construction(
                'ISO_CH7_LW_FLOOR',
                leger['floor_layers_inside_to_outside'],
                emissivite, absorptance),
        },
        'status': 'PROVISIONAL_VALUES_PRESENT_RECALCULATION_REQUIRED',
        'compliance_claim_allowed': False,
        'declared_provisional_values': [
            {
                'field': (
                    'lightweight_opaque_constructions.*.surface_properties.'
                    'inside_ir_emissivity et outside_ir_emissivity'
                ),
                'provisional_value': emissivite,
                'why_not_in_source': (
                    u"iso52016_chapter7_confirmed_inputs.json ne porte aucune "
                    u"emissivite infrarouge, que le contrat normalise exige "
                    u"pour les deux faces de chaque construction opaque."
                ),
                'how_derived': (
                    u"epsilon = h_r / (4 sigma T^3) applique aux coefficients "
                    u"radiatifs que la source porte : interieur %.2f / %.3f a "
                    u"%.2f K = %.4f ; exterieur %.2f / %.4f a %.2f K = %.4f. "
                    u"Les deux convergent a %.4f pres, et la valeur retenue est "
                    u"leur moyenne arrondie a deux decimales."
                    % (radiatifs['internal'],
                       4.0 * SIGMA * T_INTERIEUR_K ** 3, T_INTERIEUR_K,
                       interieur,
                       radiatifs['external'],
                       4.0 * SIGMA * T_EXTERIEUR_K ** 3, T_EXTERIEUR_K,
                       exterieur, abs(interieur - exterieur))
                ),
                'assumption_to_confirm': (
                    u"Les temperatures de reference de ces coefficients "
                    u"radiatifs, que la source n'enonce pas : %.2f K a "
                    u"l'interieur et %.2f K a l'exterieur."
                    % (T_INTERIEUR_K, T_EXTERIEUR_K)
                ),
                'cleared_by': (
                    u"ISO EN 52016-1:2017 clauses 7.2.2.7 a 7.2.2.10, "
                    u"registre des demandes externes point I1"
                ),
            },
        ],
        'claim_guardrail': (
            u"Transcription normalisee de la cellule d'essai du chapitre 7. "
            u"Elle porte une valeur PROVISOIRE declaree ci-dessus : elle rend "
            u"la chaine de generation executable, elle ne fonde aucun resultat, "
            u"aucune comparaison SIA et aucune attestation avant recalcul."
        ),
    }


def main(argv=None):
    u"""Point d'entrée.

    Args:
        argv: Arguments, `sys.argv[1:]` par défaut.

    Returns:
        int: 0 en succès.
    """
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument(
        '--ecrire', action='store_true',
        help=u"Écrit l'artefact ; sinon affiche seulement le résumé.")
    options = analyseur.parse_args(argv)

    source = os.path.join(_RACINE, 'config',
                          'iso52016_chapter7_confirmed_inputs.json')
    charge = construire(source)
    provisoire = charge['declared_provisional_values'][0]
    print(u"  emissivite provisoire : %s" % provisoire['provisional_value'])
    print(u"  coefficients          : %s"
          % json.dumps(charge['surface_coefficients_w_m2k'], sort_keys=True))
    for nom, bloc in sorted(charge['lightweight_opaque_constructions'].items()):
        print(u"  %-14s : %s" % (nom, ' -> '.join(
            couche['material_id']
            for couche in bloc['layers_outside_to_inside'])))

    cible = os.path.join(_RACINE, 'refs', 'reference-data',
                         'iso52016_chapter7_test_cell.binding.json')
    if not options.ecrire:
        print(u"  (essai a blanc, rien n'est ecrit)")
        return 0
    with io.open(cible, 'w', encoding='utf-8') as flux:
        flux.write(json.dumps(charge, ensure_ascii=False, indent=2) + u"\n")
    print(u"  ecrit : %s" % cible)
    print(u"  sha256: %s" % _empreinte(cible))
    return 0


if __name__ == '__main__':
    sys.exit(main())
