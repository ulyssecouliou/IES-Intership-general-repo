# -*- coding: utf-8 -*-
"""Builds a ventilation system in VE, based on the Test 4 specification.

PURPOSE: READING VARIABLE NAMES, NOT VALIDATING. This model is used to
discover which quantities VE exposes for an air-handling unit — heating and
cooling coils, heat-recovery unit, fans. It is the only way to resolve the
18 missing bindings for SIA tests 4 to 6.

It **cannot** be a SIA validation case, and three mandatory inputs are
missing from the repository for that purpose (see `MANQUANTS`). No result
from this model must be presented as a SIA candidate.

WHAT THE RECOGNITION ESTABLISHED on 2026-08-07. The signatures are
known: all setters of `VEApacheSystem` take a **dictionary**, whose keys are
recorded in `CLES_DES_SETTERS`.

And those keys answer a broader question than their own. `SFP`, `SEER`,
`SCoP`, `gen_seasonal_eff`, `CHP_ranking`, `meter_cef`: **ApacheSystems is
a seasonal-efficiency model**, oriented towards NCM compliance. It is not a
component model.

Five Test 4 requirements therefore have no expression in it — coil capacities,
heat-recovery bypass, frost protection, regulated supply-air setpoint, CO2-
controlled variable flow (see `INEXPRIMABLE_EN_APACHESYSTEMS`). `construire()`
refuses for this reason, which is a result, not a deferral.

CONSEQUENCE FOR THE PROJECT. Tests 4, 5 and 6 require an **ApacheHVAC**
network. Yet `HVACNetwork` only exposes `components`, `systems`,
`controllers`, `get_component_by_id`, `load_network` and `path` — no creation
method. The network must be built **by hand** in VE, once, then its `.asp`
file versioned and reloaded via `load_network`.

AN API TRAP, noted in passing. `set_heating()` called **without argument**
does not raise: it returns `None`. A faulty call therefore goes unnoticed.
Any configuration written here must be **read back** after writing, as
`test1_adapter` already does for materials.
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from scripts.run_test1_dans_ve import (  # noqa: E402
    _dans_ve,
    _membres,
    _serialisable,
    dire,
)

CHEMIN_RAPPORT = os.path.join(_RACINE, "outputs", "reconnaissance_test4.json")

_SPEC = "Spezifikation_Test4.pdf"

#: Central-unit parameters, ALL read from the Test 4 specification. Each
#: entry carries its source; none is rounded, completed or converted.
PARAMETRES = {
    "debit_nominal_m3_h": {"valeur": 1700.0, "source": _SPEC + ", Volumenstrom"},
    "debit_variable_pourcent": {
        "valeur": (20.0, 100.0),
        "source": _SPEC + ", Variabel von bis",
    },
    "perte_de_charge_soufflage_pa": {
        "valeur": 500.0,
        "source": _SPEC + ", Nenn-Druckverlust",
    },
    "perte_de_charge_reprise_pa": {
        "valeur": 400.0,
        "source": _SPEC + ", Nenn-Druckverlust",
    },
    "puissance_ventilateur_soufflage_w": {
        "valeur": 407.0,
        "source": _SPEC + ", Ventilatoren / Nennleistung",
    },
    "puissance_ventilateur_reprise_w": {
        "valeur": 331.0,
        "source": _SPEC + ", Ventilatoren / Nennleistung",
    },
    "recuperateur_taux": {
        "valeur": 0.75,
        "source": _SPEC + ", Wärmerückgewinnungsgerät / Nominale "
        "Temperaturänderungszahl",
    },
    "recuperateur_type": {
        "valeur": "échangeur à plaques SANS échange d'humidité",
        "source": _SPEC + ", Wärmerückgewinnungsgerät / Beschreibung",
    },
    "batterie_froide_kw": {"valeur": 12.8, "source": _SPEC + ", Luftkühler / Auslegung"},
    "batterie_chaude_kw": {
        "valeur": 11.4,
        "source": _SPEC + ", Lufterhitzer / Auslegung",
    },
    "temperature_soufflage_refroidissement_c": {
        "valeur": (16.0, 22.5),
        "source": _SPEC + ", Zulufttemperatur",
    },
    "temperature_soufflage_chauffage_c": {
        "valeur": (22.5, 29.0),
        "source": _SPEC + ", Zulufttemperatur",
    },
    "horaire_fonctionnement": {
        "valeur": "jours ouvrés 05:00-20:00 ; arrêt en juillet",
        "source": _SPEC + ", Regelung / Betriebszeit",
    },
    "surface_nette_m2": {"valeur": 165.8, "source": _SPEC + ", Nettofläche"},
    "infiltration_m3_h_m2": {"valeur": 0.15, "source": _SPEC + ", Infiltration"},
    "occupants": {"valeur": 55, "source": _SPEC + ", Personen / Anzahl"},
    "apport_equipements_w_m2": {"valeur": 10.0, "source": _SPEC + ", Geräte"},
    "apport_eclairage_w_m2": {"valeur": 6.4, "source": _SPEC + ", Beleuchtung"},
    "co2_ppm": {"valeur": (600.0, 1000.0), "source": _SPEC + ", Sollwerte / CO2"},
    "co2_exterieur_ppm": {"valeur": 400.0, "source": _SPEC + ", Sollwerte / CO2"},
}

#: Mandatory inputs for a VALIDATION CASE, absent from the repository. They
#: do not prevent reading variable names; they prohibit presenting a result
#: as a SIA candidate.
MANQUANTS = {
    "climat": "SIA 2028 DRY normal, Zürich Kloten — fichier non disponible. "
    "Le relevé de variables fonctionne avec un autre climat ; le "
    "résultat chiffré, non.",
    "constructions": "FprSIA 380/2:2022, tableau 3 « Grenzwert » — valeurs "
    "non extraites du PDF.",
    "usage": "Standardnutzung « Hörsaal » selon SIA 2024:2021, Zielwerte — "
    "fiches d'utilisation non disponibles (téléchargement libre, "
    "action utilisateur).",
}

#: `VEApacheSystem` methods whose signature must be read before the
#: parameters can be applied.
SETTERS_A_RELEVER = (
    "set_air_supply",
    "set_auxiliary_energy",
    "set_control",
    "set_cooling",
    "set_heating",
    "set_name",
    "set_ventilation_ncm",
)

#: Properties to read as they come out of a new system: they show the
#: structures the setters expect in return.
PROPRIETES_A_RELEVER = (
    "air_supply",
    "auxiliary_energy",
    "control",
    "cooling",
    "heating",
    "hot_water",
    "id",
    "name",
    "ventilation_ncm",
)


class ConstructionRefusee(RuntimeError):
    """Raised when the construction cannot proceed without guessing."""


def reconnaitre():
    """Creates an ApacheSystems system and reads what its API expects.

    Configures NOTHING: the created system remains at VE default values.
    This is a reading, not a construction.

    Returns:
        dict: Report, also written to disk.
    """
    rapport = {
        "dans_ve": _dans_ve(),
        "but": "Relever la signature des setters de VEApacheSystem avant de "
        "leur appliquer les valeurs de la spécification du Test 4.",
        "avertissement": "Aucune valeur de ce rapport n'est un résultat de validation. Le "
        "système créé ici est un objet de RECONNAISSANCE : il porte les "
        "valeurs par défaut de VE, pas celles de la norme.",
        "parametres_de_la_spec": dict(
            (cle, {"valeur": _serialisable(entree["valeur"]), "source": entree["source"]})
            for cle, entree in PARAMETRES.items()
        ),
        "manquants_pour_une_validation": MANQUANTS,
        "etapes": [],
    }

    def etape(nom, fonction):
        """Executes a step recording its outcome.

        Args:
            nom: Step label.
            fonction: Callable taking no argument.

        Returns:
            Any: Result, or `None` on failure.
        """
        try:
            valeur = fonction()
        except Exception as erreur:  # noqa: BLE001 -- on consigne, on ne masque pas
            rapport["etapes"].append(
                {
                    "nom": nom,
                    "statut": "ECHEC",
                    "type_erreur": type(erreur).__name__,
                    "erreur": "%s" % erreur,
                }
            )
            dire("  [ECHEC] %-40s %s" % (nom, type(erreur).__name__))
            return None
        rapport["etapes"].append(
            {
                "nom": nom,
                "statut": "OK",
                "type": type(valeur).__name__,
                "valeur": _serialisable(valeur),
            }
        )
        dire("  [OK]    %-40s %s" % (nom, repr(valeur)[:44]))
        return valeur

    dire("=== RECONNAISSANCE : systeme de ventilation, Test 4 ===")
    dire("  but : relever ce que l API attend, pas construire un cas SIA.")
    if not rapport["dans_ve"]:
        dire("  hors VEScripts : rien a apprendre ici.")
        return rapport

    import iesve

    projet = etape("projet courant", lambda: iesve.VEProject.get_current_project())
    etape("systemes existants", lambda: projet.apache_systems)

    systeme = etape("create_apache_system", lambda: projet.create_apache_system())
    if systeme is None:
        _ecrire(rapport)
        return rapport

    etape("attributs du systeme", lambda: _membres(systeme))

    # CORRECTED on 2026-08-07. `heating`, `cooling`, `air_supply`... are
    # METHODS, not attributes: the first reading only captured
    # `<bound method ...>` values and therefore never obtained the default
    # dictionaries. Those are what show the types the setters expect.
    for nom in PROPRIETES_A_RELEVER:
        etape(
            "%s() (valeur par defaut)" % nom,
            lambda n=nom: _appeler_si_possible(getattr(systeme, n)),
        )

    for nom in SETTERS_A_RELEVER:
        etape("%s (signature)" % nom, lambda n=nom: _signature(getattr(systeme, n)))

    _ecrire(rapport)
    return rapport


def _appeler_si_possible(valeur):
    """Returns the value, or the result of calling it if it is a method.

    `VEApacheSystem` exposes `heating`, `cooling`, `air_supply`... as methods,
    not attributes. Reading them without calling them only yields a
    `<bound method ...>` — that was the first reading's error.

    Args:
        valeur: Attribute read from the object.

    Returns:
        Any: The result of the call, or the value as-is.
    """
    if not callable(valeur):
        return valeur
    return valeur()


def _signature(methode):
    """Describes a method: docstring and signature if it exposes one.

    Args:
        methode: Bound method.

    Returns:
        dict: What could be discovered.
    """
    import inspect

    releve = {"doc": (getattr(methode, "__doc__", None) or "")[:400]}
    try:
        releve["signature"] = "%s" % (inspect.signature(methode),)
    except (TypeError, ValueError) as erreur:
        # Native methods often do not expose a signature: that is the normal
        # case, not an anomaly.
        releve["signature"] = "non exposee (%s)" % type(erreur).__name__
    return releve


#: Keys each setter accepts, READ from their docstring on 2026-08-07. They
#: show what ApacheSystems is: a SEASONAL-EFFICIENCY model, oriented towards
#: NCM compliance.
CLES_DES_SETTERS = {
    "set_heating": (
        "fuel",
        "gen_seasonal_eff",
        "SCoP",
        "gen_size",
        "HR_effectiveness",
        "HR_return_temp",
        "used_with_CHP",
        "CHP_ranking",
        "CHP_heat_output",
        "is_heat_pump",
        "meter_cef",
        "meter_pef",
    ),
    "set_cooling": (
        "cool_vent_mechanism",
        "has_absorption_chiller",
        "fuel",
        "SEER",
        "del_eff",
        "SSEER",
        "gen_size",
        "pump_and_fan_power_perc",
        "nominal_eer",
        "free_cooling",
    ),
    "set_air_supply": (
        "condition",
        "profile",
        "OA_max_flow",
        "temperature_difference",
        "cooling_max_flow",
    ),
    "set_auxiliary_energy": (
        "method",
        "SFP",
        "AEV",
        "off_schedule_AEV",
        "fan_fraction",
        "air_supply_mechanism",
    ),
    "set_ventilation_ncm": (
        "air_supply_mechanism",
        "heat_recovery_type",
        "heat_recovery_efficiency_known",
        "heat_recovery_efficiency",
        "variable_heat_recovery",
    ),
}

#: Test 4 specification requirements that NO key above can express. This is
#: why ApacheSystems is not suitable.
INEXPRIMABLE_EN_APACHESYSTEMS = {
    "puissance des batteries": "Luftkühler 12,8 kW et Lufterhitzer 11,4 kW. `gen_size` dimensionne "
    "le GÉNÉRATEUR, pas la batterie de traitement d'air.",
    "bypass du récupérateur": "« Mit Bypass auf Zulufttemperatur-Sollwert, Kühlfall 100 % Bypass ». "
    "`heat_recovery_efficiency` est un rendement constant : il n'a pas "
    "de régulation.",
    "protection antigel": "« Regelung mit Bypass auf Fortlufttemperatur ≥ 0 °C ». Aucune clé.",
    "consigne de température de soufflage": "16–22,5 °C en refroidissement, 22,5–29 °C en chauffage, régulateur "
    "PI. `temperature_difference` est un écart fixe, pas une consigne "
    "régulée.",
    "régulation CO2 du débit variable": "20–100 % du débit nominal, pilotés par la concentration en CO2. "
    "Aucune clé.",
}


def construire(projet=None):
    """Applies the specification parameters to a system.

    Args:
        projet: `VEProject`, or `None` for the current project.

    Raises:
        ConstructionRefusee: Always. The reason CHANGED on 2026-08-07, and
            it is a result, not a deferral.

            The signatures are now known: all setters take a dictionary,
            whose keys are recorded in `CLES_DES_SETTERS`. Those keys show
            that ApacheSystems is a **seasonal-efficiency** model oriented
            towards NCM compliance — SFP, SEER, SCoP, generation efficiency
            — and not a component model.

            Five specification requirements for Test 4 have no expression in
            it (see `INEXPRIMABLE_EN_APACHESYSTEMS`). Constructing anyway
            would produce a system that simulates, that gives numbers, and
            that does not represent the test — the worst of the three cases.
    """
    raise ConstructionRefusee(
        "construction refusée : ApacheSystems ne peut pas représenter le "
        "Test 4. Les %d setters sont désormais connus (ils prennent des "
        "dictionnaires, clés relevées dans CLES_DES_SETTERS), mais aucune de "
        "leurs clés n'exprime : %s. ApacheSystems modélise des RENDEMENTS "
        "saisonniers (SFP, SEER, SCoP), pas des composants. Le Test 4 exige "
        "un réseau ApacheHVAC, qui doit être construit à la main dans VE puis "
        "chargé par `HVACNetwork.load_network` depuis un `.asp`."
        % (len(CLES_DES_SETTERS), ", ".join(sorted(INEXPRIMABLE_EN_APACHESYSTEMS)))
    )


def _ecrire(rapport):
    """Writes the report and says where to find it.

    Args:
        rapport: Recognition report.
    """
    dossier = os.path.dirname(CHEMIN_RAPPORT)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(CHEMIN_RAPPORT, "w", encoding="utf-8") as flux:
        flux.write(json.dumps(rapport, ensure_ascii=False, indent=2))
    dire()
    dire("rapport : %s" % CHEMIN_RAPPORT)
    dire(
        "-> me renvoyer ce fichier : il contient les signatures qui "
        "manquent pour appliquer les valeurs de la specification."
    )


def main(arguments=()):
    """Entry point.

    Args:
        arguments: `--construire` to attempt the construction.

    Returns:
        int: 0 if the report could be written, 1 otherwise.
    """
    if "--construire" in arguments:
        try:
            construire()
        except ConstructionRefusee as erreur:
            dire("REFUS : %s" % erreur)
            return 1
    rapport = reconnaitre()
    return 0 if rapport.get("etapes") else 1
