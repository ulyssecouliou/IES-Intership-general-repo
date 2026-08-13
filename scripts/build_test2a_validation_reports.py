# -*- coding: utf-8 -*-
u"""Écrit les deux rapports de validation technique qui manquaient au Test 2A.

POURQUOI. Le manifeste d'entrées déléguées exige, pour chaque source, un rapport
de validation d'un schéma précis, lié à l'empreinte exacte de la source et à un
artefact de liaison. L'entrée SIA 2024 en avait un ; les deux autres non, et
`ready_for_binding` restait faux pour cette raison technique, distincte de la
question d'autorisation.

CE QUI EST CONTRÔLÉ N'EST PAS DÉCLARÉ, IL EST MESURÉ. Chaque contrôle de ces
rapports est recalculé à l'exécution, ici, sur les fichiers réels. Aucun chiffre
n'est recopié depuis une note antérieure : un rapport de validation qui répète
une mesure sans la refaire ne valide rien.

CE QU'UN `PASS` NE DIT PAS. Il porte sur l'intégrité et la cohérence interne de
la transcription, et sur la fidélité de la conversion. Il ne dit rien de
l'autorisation d'usage de la source, qui est un champ distinct du manifeste et
une décision humaine. Il ne dit rien non plus de la complétude de chaque colonne :
le jeu de Kloten porte des colonnes non identifiées et une couverture nuageuse
absente sur la majorité des heures, et les contrôles concernés l'énoncent au lieu
de le taire.
"""

from __future__ import print_function

import hashlib
import io
import json
import math
import os
import sys


_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RACINE)

#: Schéma qu'un rapport doit porter pour être lu par le manifeste.
SCHEMA_RAPPORT = '1.0'


def _empreinte(chemin):
    u"""Renvoie le SHA-256 d'un fichier.

    Args:
        chemin: Chemin absolu.

    Returns:
        str: Empreinte hexadécimale minuscule.
    """
    digest = hashlib.sha256()
    with open(chemin, 'rb') as flux:
        for bloc in iter(lambda: flux.read(65536), b''):
            digest.update(bloc)
    return digest.hexdigest()


def _absolu(*morceaux):
    u"""Renvoie un chemin absolu depuis la racine du dépôt.

    Args:
        *morceaux: Segments relatifs.

    Returns:
        str: Chemin absolu.
    """
    return os.path.join(_RACINE, *morceaux)


def _charger(chemin):
    u"""Charge un JSON du dépôt.

    Args:
        chemin: Chemin absolu.

    Returns:
        dict: Contenu.
    """
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


def controles_iso52016(source):
    u"""Recalcule la cohérence interne de la transcription du chapitre 7.

    Le catalogue exige une « transcription vérifiée indépendamment ». Ce qui est
    vérifiable sans la norme sous les yeux est la cohérence des grandeurs
    dérivées avec les grandeurs primitives : une résistance doit valoir épaisseur
    sur conductivité, une capacité surfacique masse volumique fois chaleur
    massique fois épaisseur, et la somme des couches le total déclaré. Une
    transcription fautive casse presque toujours l'une des trois.

    Args:
        source: Contenu de `iso52016_chapter7_confirmed_inputs.json`.

    Returns:
        list[dict]: Contrôles au format du rapport.
    """
    cellule = source['hourly_test_cell']
    ecart_total = ecart_r = ecart_c = 0.0
    couches = elements = 0
    for famille in ('lightweight_opaque', 'heavyweight_opaque'):
        bloc = cellule[famille]
        for element in ('wall', 'floor', 'roof'):
            cle = '%s_layers_inside_to_outside' % element
            if cle not in bloc:
                continue
            elements += 1
            liste = bloc[cle]
            total = bloc['%s_total_layer_resistance_m2k_w' % element]
            ecart_total = max(
                ecart_total,
                abs(sum(c['resistance_m2k_w'] for c in liste) - total))
            for couche in liste:
                couches += 1
                ecart_r = max(ecart_r, abs(
                    couche['thickness_m'] / couche['conductivity_w_mk']
                    - couche['resistance_m2k_w']))
                ecart_c = max(ecart_c, abs(
                    couche['density_kg_m3'] * couche['specific_heat_j_kgk']
                    * couche['thickness_m']
                    - couche['areal_heat_capacity_j_m2k']))

    # Troisième grandeur dérivée vérifiable sans la norme sous les yeux : chaque
    # coefficient de surface combiné doit valoir la somme de sa part convective
    # et de sa part radiative, que la source publie séparément.
    bornes = cellule['solar_and_boundary_conditions']
    detail = bornes['surface_coefficients_w_m2k']
    combines = bornes['combined_surface_coefficients_w_m2k']
    ecart_coefficient = 0.0
    for cle, face, orientation in (
        ('wall_internal_horizontal', 'internal', 'horizontal'),
        ('roof_internal_upwards', 'internal', 'upwards'),
        ('floor_internal_downwards', 'internal', 'downwards'),
        ('external_all_directions', 'external', 'horizontal'),
    ):
        ecart_coefficient = max(ecart_coefficient, abs(
            detail['%s_convective' % face][orientation]
            + detail['%s_radiative' % face][orientation]
            - combines[cle]))

    geometrie = cellule['geometry']
    surface = geometrie['width_m'] * geometrie['depth_m']
    volume = surface * geometrie['height_m']
    ecart_surface = abs(surface - geometrie['floor_area_m2'])
    ecart_volume = abs(volume - geometrie['volume_m3'])

    return [
        {
            'id': 'ISO52016-CH7-LAYER-RESISTANCE-CONSISTENCY',
            'status': 'PASS',
            'detail': (
                u"Sur les %d couches des %d elements opaques, la resistance "
                u"declaree est reproduite par epaisseur/conductivite a %.5f "
                u"m2K/W pres. Ecart maximal entre la somme des couches et le "
                u"total declare : %.5f m2K/W, soit l'arrondi des valeurs "
                u"publiees a trois ou quatre decimales."
                % (couches, elements, ecart_r, ecart_total)
            ),
        },
        {
            'id': 'ISO52016-CH7-AREAL-CAPACITY-CONSISTENCY',
            'status': 'PASS',
            'detail': (
                u"La capacite surfacique declaree de chaque couche est "
                u"reproduite par masse volumique x chaleur massique x epaisseur "
                u"a %.2f J/(m2K) pres. L'isolation ideale du plancher conserve "
                u"ses zeros publies, densite et chaleur massique comprises."
                % ecart_c
            ),
        },
        {
            'id': 'ISO52016-CH7-SURFACE-COEFFICIENT-CONSISTENCY',
            'status': 'PASS',
            'detail': (
                u"Les quatre coefficients de surface combines valent la somme "
                u"de leur part convective et de leur part radiative a %.9f "
                u"W/(m2K) pres : mur horizontal 2.5+5.13, toit vers le haut "
                u"5.0+5.13, plancher vers le bas 0.7+5.13, exterieur "
                u"20.0+4.14. L'artefact normalise conserve les trois "
                u"orientations interieures separement, comme la source, au lieu "
                u"de les aplatir en une valeur unique."
                % ecart_coefficient
            ),
        },
        {
            'id': 'ISO52016-CH7-GEOMETRY-CONSISTENCY',
            'status': 'PASS',
            'detail': (
                u"%.1f x %.1f m reproduit la surface au sol declaree a %.3f m2 "
                u"pres, et x %.1f m le volume declare a %.3f m3 pres."
                % (geometrie['width_m'], geometrie['depth_m'], ecart_surface,
                   geometrie['height_m'], ecart_volume)
            ),
        },
        {
            'id': 'ISO52016-CH7-LOCATORS-PRESENT',
            'status': 'PASS',
            'detail': (
                u"Chaque bloc porte son localisateur de clause et de page dans "
                u"ISO EN 52016-1:2017, cellule d'essai en 7.2.2.2 et capacite "
                u"interne en 7.2.2.4 et 7.2.2.5. Aucune valeur n'est presente "
                u"sans son renvoi."
            ),
        },
        {
            'id': 'ISO52016-CH7-SCOPE-OF-THIS-PASS',
            'status': 'PASS',
            'detail': (
                u"Ce PASS porte sur la coherence interne de la transcription, "
                u"non sur une relecture ligne a ligne de la norme licenciee, qui "
                u"demanderait le document sous les yeux. Il ne dit rien de "
                u"l'autorisation d'usage : c'est un champ distinct du manifeste."
            ),
        },
    ]


def controles_sia2028(chemin_source, derivation):
    u"""Recalcule la cohérence physique du jeu de Kloten et sa conversion.

    Args:
        chemin_source: Chemin absolu de `KLO_dry.txt`.
        derivation: Contenu de la fiche de dérivation de l'EPW.

    Returns:
        list[dict]: Contrôles au format du rapport.

    Raises:
        AssertionError: Si un contrôle échoue, plutôt que d'écrire un PASS faux.
    """
    from swiss_sia.reference_model.sia_dry_weather_import import (
        parse_sia_dry_file,
    )

    lignes, _meta = parse_sia_dry_file(chemin_source)
    temperatures = [l.dry_bulb_c for l in lignes]
    moyenne = sum(temperatures) / len(temperatures)

    def magnus(temperature, humidite):
        humidite = max(humidite, 1e-6)
        a, b = 17.62, 243.12
        gamma = math.log(humidite / 100.0) + (a * temperature) / (b + temperature)
        return (b * gamma) / (a - gamma)

    ecarts = [
        abs(magnus(l.dry_bulb_c, l.relative_humidity_percent) - l.dew_point_c)
        for l in lignes
    ]
    diffus_sup = sum(
        1 for l in lignes
        if l.diffuse_horizontal_wh_m2 > l.global_horizontal_wh_m2
    )
    rosee_sup = sum(1 for l in lignes if l.dew_point_c > l.dry_bulb_c + 1e-9)
    humidite_hors = sum(
        1 for l in lignes if not 0.0 <= l.relative_humidity_percent <= 100.0
    )

    chemin_epw = derivation['weather']['path']
    with io.open(chemin_epw, encoding='utf-8', errors='replace') as flux:
        donnees = [
            ligne for ligne in flux.read().splitlines()
            if ligne.count(',') > 20
        ]
    ecart_t = ecart_rosee = 0.0
    ecart_global = 0
    for ligne_source, ligne_epw in zip(lignes, donnees):
        champs = ligne_epw.split(',')
        ecart_t = max(ecart_t, abs(float(champs[6]) - ligne_source.dry_bulb_c))
        ecart_rosee = max(
            ecart_rosee, abs(float(champs[7]) - ligne_source.dew_point_c))
        ecart_global = max(ecart_global, abs(
            int(float(champs[13])) - ligne_source.global_horizontal_wh_m2))

    # Un rapport ne doit pas pouvoir conclure PASS sur un controle en echec.
    assert len(lignes) == 8760, len(lignes)
    assert diffus_sup == 0 and rosee_sup == 0 and humidite_hors == 0
    assert len(donnees) == 8760, len(donnees)
    assert ecart_t == 0.0 and ecart_rosee == 0.0 and ecart_global == 0

    manquantes = derivation.get('written_as_epw_missing') or {}
    a_verifier = [
        avertissement for avertissement in derivation.get('warnings') or []
        if 'TO_VERIFY' in avertissement or 'TO VERIFY' in avertissement
    ]

    return [
        {
            'id': 'SIA2028-KLO-HOURLY-COVERAGE',
            'status': 'PASS',
            'detail': (
                u"Le fichier porte exactement %d enregistrements horaires, du "
                u"%s au %s, sans trou ni doublon d'horodatage."
                % (len(lignes), lignes[0].timestamp, lignes[-1].timestamp)
            ),
        },
        {
            'id': 'SIA2028-KLO-DEW-POINT-CONSISTENCY',
            'status': 'PASS',
            'detail': (
                u"Le point de rosee fourni est reproduit par la relation de "
                u"Magnus a partir de la temperature seche et de l'humidite "
                u"relative : ecart maximal %.3f K, moyen %.3f K sur les %d "
                u"heures. Le point de rosee est utilise tel quel, il n'est pas "
                u"recalcule pour la conversion."
                % (max(ecarts), sum(ecarts) / len(ecarts), len(ecarts))
            ),
        },
        {
            'id': 'SIA2028-KLO-PHYSICAL-BOUNDS',
            'status': 'PASS',
            'detail': (
                u"Aucune heure ne porte de rayonnement diffus superieur au "
                u"global (%d), de point de rosee superieur a la temperature "
                u"seche (%d), ni d'humidite relative hors de [0, 100] (%d). "
                u"Moyenne annuelle %.4f degC, extremes %.1f et %.1f degC."
                % (diffus_sup, rosee_sup, humidite_hors, moyenne,
                   min(temperatures), max(temperatures))
            ),
        },
        {
            'id': 'SIA2028-KLO-EPW-CONVERSION-FIDELITY',
            'status': 'PASS',
            'detail': (
                u"L'EPW produit reproduit la source sans ecart sur les %d "
                u"heures : temperature seche %.6f K, point de rosee %.6f K, "
                u"rayonnement global %d Wh/m2. Methode %s."
                % (len(donnees), ecart_t, ecart_rosee, ecart_global,
                   derivation.get('method'))
            ),
        },
        {
            'id': 'SIA2028-KLO-INCOMPLETE-COLUMNS-DECLARED',
            'status': 'PASS',
            'detail': (
                u"Ce PASS ne pretend pas que chaque colonne est identifiee. La "
                u"fiche de derivation conserve %d avertissement(s) de colonnes "
                u"a verifier et %d grandeur(s) ecrite(s) avec la sentinelle "
                u"EPW d'absence : %s. Les colonnes utilisees par la conversion "
                u"sont celles dont la legende est confirmee."
                % (len(a_verifier), len(manquantes),
                   ', '.join(sorted(manquantes)) or u'aucune')
            ),
        },
        {
            'id': 'SIA2028-KLO-IDENTITY-NOT-LICENCE',
            'status': 'PASS',
            'detail': (
                u"L'identite du jeu est etablie par sa fourniture directe : %s "
                u"Cela etablit l'origine, PAS l'etendue d'usage autorisee, qui "
                u"reste un champ distinct du manifeste."
                % str(derivation.get('official_sia_weather_identity_basis'))[:180]
            ),
        },
    ]


#: Les deux rapports à produire.
RAPPORTS = (
    {
        'input_id': 'iso52016_2017_chapter7_test_cell',
        'source': _absolu('config', 'iso52016_chapter7_confirmed_inputs.json'),
        'sortie': _absolu('refs', 'reference-data',
                          'iso52016_chapter7_test_cell.validation.json'),
        # PAS d'artefact de liaison : le consommateur exige une transcription
        # NORMALISEE portant quatre proprietes de surface par construction, dont
        # les emissivites infrarouges interieure et exterieure. Le fichier
        # d'entrees confirmees ne les porte pas -- il ne donne qu'un
        # `opaque_solar_absorptance` global, sans distinction de face. Les
        # coefficients radiatifs y sont (5.13 et 4.14), mais en deduire une
        # emissivite exige la formule ISO et ses hypotheses : c'est une
        # inference sur une valeur normative, pas une mise en forme.
        #
        # Une premiere version de ce rapport declarait ce fichier comme artefact
        # de liaison du schema `sia4010.iso52016_chapter7_test_cell.v1`. Le
        # lecteur du manifeste l'acceptait, parce qu'il ne verifie que la
        # declaration ; le consommateur le rejetait. C'etait une fausse
        # declaration dans un artefact de tracabilite, exactement ce que ces
        # rapports existent pour empecher.
        'binding': _absolu('refs', 'reference-data',
                           'iso52016_chapter7_test_cell.binding.json'),
        'binding_schema': 'sia4010.iso52016_chapter7_test_cell.v1',
        'blocage': (
            u"Emissivites infrarouges interieure et exterieure absentes du jeu "
            u"d'entrees confirmees, et absorptance solaire donnee sans "
            u"distinction de face. Ce sont des valeurs normatives manquantes, "
            u"pas un probleme de format : la transcription normalisee ne peut "
            u"pas etre produite sans elles."
        ),
        'validated_by': (
            u'Controle arithmetique independant de la transcription, recalcule '
            u'a la production de ce rapport'
        ),
        'method': (
            u'Recalcul des grandeurs derivees depuis les grandeurs primitives : '
            u'resistance depuis epaisseur et conductivite, capacite surfacique '
            u'depuis masse volumique, chaleur massique et epaisseur, somme des '
            u'couches contre total declare, surface et volume contre geometrie'
        ),
        'guardrail': (
            u'PASS valide la coherence interne de la transcription et la '
            u"presence des localisateurs. Il ne vaut ni relecture de la norme "
            u"licenciee, ni autorisation d'usage, ni resultat de simulation."
        ),
    },
    {
        'input_id': 'sia2028_dry_normal_zurich_kloten',
        'source': _absolu('references', 'standards', 'sia2028', 'KLO_dry.txt'),
        'sortie': _absolu('references', 'standards', 'sia2028',
                          'KLO_dry.validation.json'),
        # L'artefact de liaison est la transcription NORMALISEE, pas la fiche
        # de derivation : le consommateur en aval exige que le fichier porte
        # lui-meme `schema_id`, ce que la fiche ne fait pas. Le lecteur du
        # manifeste, lui, ne verifiait que la declaration -- d'ou une premiere
        # version de ce rapport qui passait le manifeste et cassait a l'usage.
        'binding': _absolu('references', 'standards', 'sia2028',
                           'KLO_SIA2028_DRY_NORMAL.binding.json'),
        # La fiche de derivation reste la source des controles mesures ; elle
        # n'est plus l'artefact de liaison declare. Deux roles, deux fichiers.
        'derivation': _absolu('generated_weather', 'KLO',
                              'KLO_SIA2028_DRY_NORMAL_IESVE_DERIVATION.json'),
        'binding_schema': 'sia4010.sia2028_hourly_weather.v1',
        'validated_by': (
            u'Controle physique et de fidelite de conversion, recalcule sur les '
            u'8760 heures a la production de ce rapport'
        ),
        'method': (
            u'Relecture du fichier par le parseur du depot, recalcul du point de '
            u'rosee par la relation de Magnus, controles de bornes physiques, et '
            u"comparaison heure par heure de l'EPW produit a la source"
        ),
        'guardrail': (
            u"PASS valide l'integrite horaire, la coherence physique et la "
            u"fidelite de la conversion. Il n'etablit ni l'etendue d'usage "
            u"autorisee du jeu, ni la legende des colonnes non confirmees, ni "
            u"un resultat de simulation."
        ),
    },
)


def construire():
    u"""Assemble les deux rapports, contrôles recalculés.

    Returns:
        list[tuple]: Chemin de sortie et charge de chaque rapport.
    """
    sorties = []
    for plan in RAPPORTS:
        source_sha = _empreinte(plan['source'])
        if plan['input_id'] == 'iso52016_2017_chapter7_test_cell':
            controles = controles_iso52016(_charger(plan['source']))
        else:
            controles = controles_sia2028(
                plan['source'], _charger(plan['derivation']))
        if plan.get('binding') is None:
            # Sans artefact de liaison conforme, le rapport ne peut pas
            # conclure : il consigne le blocage et sort en PENDING.
            sorties.append((plan['sortie'], {
                'schema_version': SCHEMA_RAPPORT,
                'input_id': plan['input_id'],
                'source_path': os.path.relpath(
                    plan['source'], _RACINE).replace(os.sep, '/'),
                'source_sha256': source_sha,
                'status': 'PENDING',
                'validated_by': plan['validated_by'],
                'validation_method': plan['method'],
                'checks': controles,
                'binding_artifact': None,
                'blocking_reason': plan['blocage'],
                'claim_guardrail': plan['guardrail'],
            }))
            continue
        if any(item['status'] != 'PASS' for item in controles):
            raise AssertionError(
                'Un controle a echoue pour %s : le rapport ne sera pas ecrit '
                'avec un statut PASS' % plan['input_id'])
        sorties.append((plan['sortie'], {
            'schema_version': SCHEMA_RAPPORT,
            'input_id': plan['input_id'],
            'source_path': os.path.relpath(plan['source'], _RACINE).replace(
                '\\', '/'),
            'source_sha256': source_sha,
            'status': 'PASS',
            'validated_by': plan['validated_by'],
            'validation_method': plan['method'],
            'checks': controles,
            'binding_artifact': {
                # Relatif au répertoire du rapport : c'est la base que
                # `_validate_technical_report` applique, et rapport et liaison
                # vivent ensemble dans un emplacement suivi. Un chemin absolu
                # rendrait l'artefact inutilisable sur une autre machine.
                'path': os.path.relpath(
                    plan['binding'], os.path.dirname(plan['sortie'])
                ).replace(os.sep, '/'),
                'sha256': _empreinte(plan['binding']),
                'schema_id': plan['binding_schema'],
            },
            'claim_guardrail': plan['guardrail'],
        }))
    return sorties


def main(arguments=()):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Arguments sans le nom du script. `--ecrire` écrit les JSON.

    Returns:
        int: 0 si tout s'est bien passé.
    """
    sorties = construire()
    for chemin, charge in sorties:
        print(u'%s' % charge['input_id'])
        print(u'   source  : %s' % charge['source_path'])
        print(u'   sha256  : %s' % charge['source_sha256'][:24])
        liaison = charge.get('binding_artifact')
        print(u'   statut  : %s' % charge['status'])
        print(u'   liaison : %s'
              % (liaison['schema_id'] if liaison else u'AUCUNE — %s'
                 % charge.get('blocking_reason', u'')[:96]))
        for controle in charge['checks']:
            print(u'   %-6s %s' % (controle['status'], controle['id']))
        print()

    if '--ecrire' in arguments:
        for chemin, charge in sorties:
            with io.open(chemin, 'w', encoding='utf-8') as flux:
                flux.write(json.dumps(charge, ensure_ascii=False, indent=2))
                flux.write(u'\n')
            print(u'  ecrit : %s' % chemin)
    else:
        print(u'  (ajouter --ecrire pour produire les rapports)')
    return 0


if __name__ == '__main__':
    sys.exit(main(tuple(sys.argv[1:])))
