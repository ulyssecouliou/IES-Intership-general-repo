# -*- coding: utf-8 -*-
u"""Freeze the public climate data of EN ISO 52016-1:2017 (DRYCOLD case).

THE AUTHORITATIVE SOURCE, free and public -- the only one the Test 1
specification names:

    Spezifikation_Test1.pdf : « Klima | DRYCOLD.TMY (BESTEST) Denver, CO /
                                http://standards.iso.org/iso/52016/-1/ed-1 »

The portal holds exactly ONE file:
`ISO_52016_1_BESTEST_ClimData_2016.08.24.xls`. It is NOT a weather file
brut mais un tableau horaire converti, et il porte deux avertissements en clair
that change how Test 1 must be run -- see `avertissements_du_fichier`.

WHY THIS SCRIPT EXISTS. The Codex repository carried a file
`DRYCOLD_TMY_ISO_SOURCE_VERIFICATION.json` declaring
`{"status": "PASS", "source_identity_supported": true}` avec une empreinte
sha256 that is the digest of a 30-BYTE TEST STUB, not of the real file
de 8760 heures. L'attestation ne certifiait rien. On repart donc de la source
public source, with its digest recomputed here.

That is the failure this whole repository is built against: a document that
LOOKS like verification, carrying a real algorithm and a real-looking digest,
attesting to something that was never checked. Nothing about it reads as
suspicious until someone recomputes the hash.

Usage :
    python scripts/freeze_iso_drycold_climate.py
"""

from __future__ import print_function

import hashlib
import io
import json
import os

import xlrd

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_XLS = os.path.join(_RACINE, 'refs', 'ISO_52016_1_BESTEST_ClimData_2016.08.24.xls')
_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data',
                       'iso-52016-1-climat-drycold.json')

URL = ('https://standards.iso.org/iso/52016/-1/ed-1/'
       'ISO_52016_1_BESTEST_ClimData_2016.08.24.xls')

# Les huit surfaces sur lesquelles le fichier donne l'irradiance, dans l'ordre
# of columns 6 to 13. Labels read from row 4 of the sheet.
SURFACES = ('NV', 'EV', 'SV', 'WV', 'N45', 'S45', 'VOID', 'H')

# Row of the first data point, and the length of the warm-up month.
PREMIERE_LIGNE_DONNEES = 5
HEURES_INITIALISATION = 744  # December duplicated at the front

CONSEQUENCE = (
    u"Le fichier ISO fournit l'irradiance DÉJÀ CALCULÉE sur huit surfaces "
    u"nommées, sans décomposition global / direct / diffus. Les quatre "
    u"programmes de référence ont donc été alimentés en irradiance DE SURFACE. "
    u"Un .epw fournit global / direct / diffus et laisse le modèle de ciel du "
    u"programme dériver les surfaces : l'entrée n'est pas la même. L'écart de "
    u"modèle de ciel doit être quantifié AVANT d'interpréter tout écart "
    u"thermique, sans quoi on attribuerait au moteur thermique de VE une "
    u"divergence d'origine radiative."
)

INITIALISATION = (
    u"Les 744 premières heures sont un mois d'initialisation (décembre "
    u"recopié). Une simulation VE de 8760 heures partant du 1er janvier ne "
    u"reproduit donc PAS l'état initial des programmes de référence. L'effet "
    u"est maximal sur les cas à forte masse (900, 940, 900FF). Le "
    u"préconditionnement de VE doit être réglé pour refléter ce mois."
)


def _lignes(feuille):
    """Data rows: the ones whose `month` column holds a number."""
    lues = []
    for r in range(PREMIERE_LIGNE_DONNEES, feuille.nrows):
        valeur = feuille.cell_value(r, 1)
        if isinstance(valeur, float):
            lues.append([feuille.cell_value(r, c) for c in range(16)])
    return lues


def construire():
    with open(_XLS, 'rb') as f:
        octets = f.read()
    empreinte = hashlib.sha256(octets).hexdigest()

    feuille = xlrd.open_workbook(_XLS).sheet_by_index(0)
    toutes = _lignes(feuille)
    annee = toutes[HEURES_INITIALISATION:]

    avertissements = []
    for r in (0, 1):
        for c in range(feuille.ncols):
            valeur = feuille.cell_value(r, c)
            if isinstance(valeur, unicode if str is bytes else str) and valeur.strip():
                avertissements.append(valeur.strip())

    temperatures = [l[5] for l in annee]
    irradiations = dict(
        (nom, round(sum(l[6 + i] for l in annee) / 1000.0, 1))
        for i, nom in enumerate(SURFACES))

    return {
        u'source': {
            u'norme': u'EN ISO 52016-1:2017',
            u'element': u'données climatiques publiques associées au chapitre 7',
            u'fichier': os.path.basename(_XLS),
            u'url': URL,
            u'octets': len(octets),
            u'sha256': empreinte,
            u'telecharge_le': u'2026-08-05',
            u'gratuit': True,
            u'auteur_metadonnee_xls': u'Thor Endre Lexow, ISO, 2016-08-24',
            u'designee_par': u'Spezifikation_Test1.pdf, ligne « Klima »',
        },
        u'avertissements_du_fichier': avertissements,
        u'structure': {
            u'lignes_de_donnees': len(toutes),
            u'heures_initialisation': HEURES_INITIALISATION,
            u'heures_annee': len(annee),
            u'mois_initialisation': 12,
            u'colonnes': {
                u'0': u'hours/calc', u'1': u'month', u'2': u'week',
                u'3': u'day/week', u'4': u'hours/week',
                u'5': u'theta_e;air [°C]',
                u'6-13': u'I_sol [W/m2] sur ' + u', '.join(SURFACES),
                u'14': u'v_w [m/s]', u'15': u'H [g/kg]',
            },
        },
        u'agregats_annuels': {
            u'theta_e_air_c': {
                u'min': min(temperatures),
                u'max': max(temperatures),
                u'moyenne': round(sum(temperatures) / len(temperatures), 4),
            },
            u'v_w_m_s_moyenne': round(
                sum(l[14] for l in annee) / len(annee), 4),
            u'irradiation_kwh_m2_an': irradiations,
        },
        u'consequence_pour_la_validation': CONSEQUENCE,
        u'consequence_initialisation': INITIALISATION,
        u'attestation_codex_invalidee': {
            u'fichier': u'.codex_tmp/test_checksum_bound_weather_verification_is_preserved/'
                        u'DRYCOLD_TMY_ISO_SOURCE_VERIFICATION.json',
            u'declarait': u'{"status": "PASS", "source_identity_supported": true}',
            u'sha256_declare': u'95490E30E3CC864D209923DEF3E089F5EF52015742285C79A637340C3F178FDC',
            u'ce_que_cette_empreinte_designe':
                u'un stub de test de 30 octets sur une seule ligne, PAS le '
                u'fichier réel de 8760 heures (sha256 c33778b4…)',
            u'statut': u'ATTESTATION SANS VALEUR — remplacée par le présent fichier',
        },
    }


def main():
    donnees = construire()
    with io.open(_SORTIE, 'w', encoding='utf-8') as f:
        f.write(json.dumps(donnees, ensure_ascii=False, indent=2))
        f.write(u'\n')

    source = donnees[u'source']
    print(u'frozen: %s' % os.path.relpath(_XLS, _RACINE))
    print(u'  %d octets, sha256 %s' % (source[u'octets'], source[u'sha256']))
    print(u'frozen: %s' % os.path.relpath(_SORTIE, _RACINE))
    print()
    print(u'reference annual irradiation, kWh/m2:')
    for nom, valeur in donnees[u'agregats_annuels'][u'irradiation_kwh_m2_an'].items():
        print(u'   %-5s %8.1f' % (nom, valeur))


if __name__ == '__main__':
    main()
