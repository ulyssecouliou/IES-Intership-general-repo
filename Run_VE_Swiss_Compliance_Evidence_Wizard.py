# -*- coding: utf-8 -*-
"""Assistant de collecte des preuves SIA 380/2 — bouton Run depuis VE.

CE QU IL FAIT. Il lit le projet VE actif, affiche ce qui est techniquement
demontre, et demande au reviseur les preuves que le logiciel ne peut pas
produire : localisation, altitude, base climatique, strategie de ventilation,
perimetre de l eclairage, sources documentaires.

CE QU IL NE FAIT PAS.
    - Il NE MODIFIE AUCUNE donnee VE. Aucune ecriture dans le modele, aucune
      creation d echange d air, aucun gain, aucune simulation lancee.
    - Il NE PRONONCE PAS de conformite SIA 380/2. Il collecte les preuves qui
      permettront a un ingenieur de le faire.
    - Il NE VAUT PAS validation SIA 4010. Celle-ci porte sur le LOGICIEL et
      ses methodes, pas sur un batiment client. Les deux ne se melangent pas.

FAIL-CLOSED. Le statut `accepted` est RECALCULE a l enregistrement, jamais
repris de la saisie. Toute incertitude ramene a `pending`.

Ecrit deux fichiers, tous deux SOUS LE PROJET VE — donc sans droits
administrateur :
    sia4010_evidence/SIA3802_project_metadata_<projet>.csv
    sia_compliance_artifacts/evidence/SIA3802_evidence_audit_<projet>_<date>.json
"""

from __future__ import print_function

import os
import sys

_RACINE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Amorcage — DOIT preceder tout import du projet
# ---------------------------------------------------------------------------
#
# VEScripts garde le MEME interpreteur d un clic sur Run au suivant :
# `sys.modules` persiste. Un paquet importe depuis un autre depot y reste en
# cache et masque celui-ci, quoi qu on fasse ensuite a `sys.path`.
_PAQUETS = ('scripts', 've_adapter', 'engine', 'ui', 'swiss_sia')
_PREFIXES = _PAQUETS + tuple(_nom + '.' for _nom in _PAQUETS)
for _nom_module in tuple(sys.modules):
    if _nom_module in _PAQUETS or _nom_module.startswith(_PREFIXES):
        del sys.modules[_nom_module]

while _RACINE in sys.path:
    sys.path.remove(_RACINE)
sys.path.insert(0, _RACINE)

from scripts import bootstrap_check  # noqa: E402
from swiss_sia import evidence_wizard as noyau  # noqa: E402
from swiss_sia import evidence_wizard_ui as interface  # noqa: E402


def _dans_ve():
    """Vrai si le module `iesve` est importable.

    Returns:
        bool: Presence d une session VEScripts.
    """
    try:
        import iesve  # noqa: F401
    except ImportError:
        return False
    return True


def relever_les_faits():
    """Lit dans VE ce qui est techniquement demontre. N ECRIT RIEN.

    Chaque lecture est isolee : une lecture qui echoue laisse son fait a
    `None`, ce qui se traduira par NOT_CHECKABLE dans l assistant. Jamais par
    zero, et jamais par une valeur par defaut.

    Returns:
        dict: Faits releves, les inconnus a `None`.
    """
    faits = {
        'project_id': None,
        'project_path': None,
        'aps_file': None,
        'detected_weather_file': None,
        'total_area_m2': None,
        'total_heating_kwh': None,
        'total_cooling_kwh': None,
        'missing_aps_outputs': (),
        'ventilation': {},
        'lighting': {},
    }
    if not _dans_ve():
        return faits

    import iesve
    try:
        projet = iesve.VEProject.get_current_project()
        chemin = getattr(projet, 'path', None)
        if isinstance(chemin, str) and chemin:
            faits['project_path'] = chemin
            faits['project_id'] = os.path.basename(chemin.rstrip(os.sep))
    except Exception:  # noqa: BLE001 -- l absence est un resultat
        pass
    return faits


def _completer_depuis_la_sonde(faits, rapport):
    """Reprend les faits deja etablis par la sonde de remediation.

    Ne recopie QUE des grandeurs mesurees. Les champs du reviseur ne sont
    jamais pre-remplis depuis un rapport machine.

    Args:
        faits: Faits en cours de constitution.
        rapport: Rapport JSON de la sonde, ou `None`.

    Returns:
        dict: Faits completes.
    """
    if not rapport:
        return faits
    dynamique = rapport.get('normalized_dynamic_results') or {}
    for cle_rapport, cle_fait in (
            ('selected_aps_file', 'aps_file'),
            ('project_weather_file', 'detected_weather_file'),
            ('total_area_m2', 'total_area_m2'),
            ('total_heating_kwh', 'total_heating_kwh'),
            ('total_cooling_kwh', 'total_cooling_kwh')):
        valeur = dynamique.get(cle_rapport)
        if valeur is not None and faits.get(cle_fait) is None:
            faits[cle_fait] = valeur

    inventaire = rapport.get('aps_runtime_inventory') or {}
    absentes = inventaire.get('unresolved_bindings')
    if absentes:
        faits['missing_aps_outputs'] = tuple(absentes)

    if not faits.get('project_id'):
        faits['project_id'] = rapport.get('project_label')
    return faits


def charger_dernier_rapport(dossier):
    """Charge le rapport de sonde le plus recent, s il existe.

    Args:
        dossier: `sia_compliance_artifacts/diagnostics/`.

    Returns:
        dict | None: Rapport, ou `None`.
    """
    import io
    import json
    if not os.path.isdir(dossier):
        return None
    candidats = sorted(
        nom for nom in os.listdir(dossier)
        if nom.startswith('swiss_sia_remediation_probe_')
        and nom.endswith('.json'))
    if not candidats:
        return None
    chemin = os.path.join(dossier, candidats[-1])
    try:
        with io.open(chemin, encoding='utf-8') as flux:
            return json.load(flux)
    except (OSError, ValueError):
        return None


def main(arguments=()):
    """Point d entree.

    Args:
        arguments: Arguments de ligne de commande, ignores.

    Returns:
        int: 0 si l assistant s est ouvert, 1 sinon.
    """
    if not bootstrap_check.check(_RACINE):
        return 2

    faits = relever_les_faits()
    if not faits.get('project_path'):
        print('Aucun projet VE actif detecte.')
        print('Cet assistant doit etre lance depuis VE, sur une COPIE du')
        print('modele client. Il ne modifie rien, mais il lit le projet actif.')
        return 1

    faits = _completer_depuis_la_sonde(
        faits,
        charger_dernier_rapport(os.path.join(
            faits['project_path'], 'sia_compliance_artifacts',
            'diagnostics')))

    chemins = interface.chemins_du_projet(faits['project_path'],
                                          faits.get('project_id') or '')
    print('Projet VE actif : %s' % faits.get('project_id'))
    print('CSV de preuves  : %s' % chemins['csv'])
    print('Audit JSON      : %s' % chemins['audit'])
    print('Aucune donnee VE ne sera modifiee.')

    assistant = interface.AssistantDePreuves(
        detecte=faits, chemin_csv=chemins['csv'],
        dossier_audit=chemins['audit'])
    resultat = assistant.lancer()

    if resultat is None:
        print('Ferme sans enregistrer. Aucun fichier ecrit.')
        return 0
    print('Statut ecrit : %s' % resultat['statut'])
    if resultat.get('sauvegarde'):
        print('Sauvegarde de l ancien CSV : %s' % resultat['sauvegarde'])
    print('Rappel : %s' % noyau.EXPLICATION_DES_CATEGORIES[
        noyau.PASS_TECHNIQUE])
    return 0


if __name__ == '__main__':
    # Pas de `sys.exit` : il leve SystemExit, que VEScripts remonte comme une
    # erreur dans sa fenetre de script alors que tout s est bien passe.
    _code = main(tuple(getattr(sys, 'argv', ())[1:]))
    print()
    print('--- termine (code %d) ---' % _code)
