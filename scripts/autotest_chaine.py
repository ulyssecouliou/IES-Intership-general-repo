# -*- coding: utf-8 -*-
"""End-to-end self-test: reference → engine → verdict → view.

WHAT THIS SCRIPT PROVES, AND WHAT IT DOES NOT PROVE.

It replays through the chain the values of a **reference program** as if
they had come from VE, and checks that the chain declares them conforming.
This proves that the **mechanics** are correct: the reference data loads,
the engine matches the quantities and cases, the band is computed, the verdict
is assembled, the view is put together.

This proves **nothing** about IESVE. A contributing program falls within its
own acceptance envelope by construction — the envelope equals `mean ± max|program −
mean|`, and the maximum discrepancy is by definition greater than or equal to
that of each contributor. Success is therefore arithmetically guaranteed: that
is precisely what makes this a test of the plumbing, and not a validation result.

    A "functional" class in the sense of this script = the chain runs.
    A "validated" class in the sense of SIA = IESVE has simulated the cases and
    its results fall within the bands. No class is validated to date.

The script fails loudly if a contributor comes out NON-conforming: this can only
come from a fault in the chain, never from the data.

Usage:
    python scripts/autotest_chaine.py [numero...]
"""

from __future__ import print_function

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import sia_bandes_engine as moteur_bandes  # noqa: E402
from engine import sia_distributions_engine as moteur_distrib  # noqa: E402
from engine import scatter_band  # noqa: E402
from engine import test1_engine as moteur_test1  # noqa: E402
from engine import test7_engine as moteur_test7  # noqa: E402

TESTS = (1, 2, 3, 4, 5, 6, 7)
TESTS_A_BANDES = (2, 3, 4, 5, 6)


class ChaineDefaillante(RuntimeError):
    """Signal an internally inconsistent replay of reference evidence.

    A reference contributor cannot fall outside its own acceptance envelope
    when the evaluation chain is internally consistent.
    """


def choisir_contributeur(reference):
    """Select the contributor column represented in the most cases.

    Args:
        reference: Annual-sum reference payload.

    Returns:
        str | None: Contributor column letter, or ``None`` when absent.
    """
    comptes = {}
    for grandeur in reference["grandeurs"]:
        for cas in grandeur["cas"]:
            for lettre in cas["contributeurs"]:
                comptes[lettre] = comptes.get(lettre, 0) + 1
    if not comptes:
        return None
    return sorted(comptes.items(), key=lambda p: (-p[1], p[0]))[0][0]


def candidat_depuis_contributeur(reference, lettre):
    """Build a candidate dataset from one reference program column.

    Args:
        reference: Annual-sum reference payload.
        lettre: Contributor column to replay.

    Returns:
        dict: Mapping of metric labels to case values.
    """
    candidat = {}
    for grandeur in reference["grandeurs"]:
        par_cas = {}
        for cas in grandeur["cas"]:
            if lettre not in cas["contributeurs"]:
                continue
            entree = cas["par_colonne"].get(lettre) or {}
            if entree.get("valeur") is not None:
                par_cas[cas["cas"]] = float(entree["valeur"])
        if par_cas:
            candidat[grandeur["libelle_de"]] = par_cas
    return candidat


def candidat_test1_depuis_moyennes(reference):
    """Replay only the 28 Test 1E values subject to a criterion.

    Other Test 1 cases are informative and must not be converted into an
    artificial PASS/FAIL decision.
    """
    candidat = {}
    for grandeur in ("sensible_heating_demand_kwh", "sensible_cooling_demand_kwh"):
        noeud = reference["reference_values"][grandeur]["1E"]
        candidat[grandeur] = {
            "1E": {
                "monthly": dict(
                    (
                        mois,
                        moteur_test1._valeur_reelle(
                            noeud["monthly"][mois]["mean_of_programs"]
                        ),
                    )
                    for mois in moteur_test1.MOIS
                ),
                "annual": moteur_test1._valeur_reelle(
                    noeud["annual"]["mean_of_programs"]
                ),
            }
        }

    pointe = reference["reference_values"]["annual_hourly_peak_load_kwh"]["1E"]["peak"]
    candidat["annual_hourly_peak_load_kwh"] = {
        "1E": {
            "peak": dict(
                (cle, moteur_test1._valeur_reelle(pointe[cle]["mean_of_programs"]))
                for cle in ("heating", "cooling")
            )
        }
    }
    return candidat


def verifier_test1():
    """Exercise the explicit Test 1 criterion and view without VE."""
    from ui import verdict_view as vue

    reference = moteur_test1.charger_reference()
    resultat = moteur_test1.evaluer_test1(
        reference, candidat_test1_depuis_moyennes(reference)
    )
    verdict = resultat["verdict_test1"]
    if verdict.get("conforme") is not True:
        raise ChaineDefaillante(
            "test 1 : le centre des bandes 1E ne ressort pas conforme."
        )
    assemblee = vue.construire_vue_test1(resultat)
    return {
        "bandes": {
            "test": 1,
            "programme_rejoue": "mean_of_programs",
            "classes_concernees": resultat["classes_concernees"],
            "nb_bandes": verdict["nb_periodes_totales"],
            "nb_cas_rejoues": (
                verdict["nb_periodes_totales"] - verdict["nb_periodes_non_evaluees"]
            ),
            "nb_non_evaluables": verdict["nb_periodes_non_evaluees"],
            "critere": "ENONCE_DANS_LA_SPEC",
            "verdict": "PASS",
        },
        "distributions": None,
        "vue": {
            "test_id": assemblee.get("test_id"),
            "nb_lignes": len(assemblee.get("lignes", [])),
            "couleur": assemblee["verdict_global"]["couleur"],
        },
    }


def candidat_test7_depuis_moyennes(reference):
    """Build the positive Test 7 witness at official band centers."""
    return dict(
        (grandeur["libelle_de"], grandeur["moyenne"])
        for grandeur in reference["grandeurs"]
    )


def verifier_test7():
    """Exercise all Test 7 bands and the PV provenance guardrail."""
    from ui import verdict_view as vue

    reference = moteur_test7.charger_reference()
    source = (
        "replay du programme de reference : valeur PV issue du classeur "
        "officiel, aucune irradiance VE ni simulation revendiquee"
    )
    resultat = moteur_test7.evaluer_test7(
        reference, candidat_test7_depuis_moyennes(reference), source_irradiance=source
    )
    if resultat["verdict"] != scatter_band.VERDICT_PASS:
        raise ChaineDefaillante("test 7 : le centre des bandes ne ressort pas PASS.")
    assemblee = vue.construire_vue_test7(resultat)
    return {
        "bandes": {
            "test": 7,
            "programme_rejoue": "mean_of_programs",
            "classes_concernees": resultat["classes_concernees"],
            "nb_bandes": resultat["grandeurs_soumises_au_critere"],
            "nb_cas_rejoues": (
                resultat["grandeurs_soumises_au_critere"] - resultat["nb_non_evaluables"]
            ),
            "nb_non_evaluables": resultat["nb_non_evaluables"],
            "critere": resultat["critere"]["statut"],
            "verdict": resultat["verdict"],
        },
        "distributions": None,
        "vue": {
            "test_id": assemblee.get("test_id"),
            "nb_lignes": len(assemblee.get("lignes", [])),
            "couleur": assemblee["verdict_global"]["couleur"],
        },
    }


def verifier_bandes(numero_test):
    """Replay one reference program through the annual-sum engine.

    Args:
        numero_test: SIA test number.

    Returns:
        dict: Structured replay report.

    Raises:
        ChaineDefaillante: If a replayed case falls outside its own band.
    """
    reference = moteur_bandes.charger_reference(numero_test)
    lettre = choisir_contributeur(reference)
    if lettre is None:
        raise ChaineDefaillante(
            "test %d : aucun contributeur dans le référentiel." % numero_test
        )

    candidat = candidat_depuis_contributeur(reference, lettre)
    resultat = moteur_bandes.evaluer(reference, candidat)

    echecs = []
    evalues = 0
    for grandeur in resultat["grandeurs"]:
        for ligne in grandeur["cas"]:
            if ligne["candidat"] is None:
                continue
            evalues += 1
            if not scatter_band.is_passing(ligne["statut"]):
                # `libelle`, not `libelle_de`: the engine RESULT renames
                # the reference data key. The failure path had never been
                # exercised, and its own test unmasked it.
                echecs.append((grandeur["libelle"], ligne["cas"], ligne["statut"]))
    if echecs:
        raise ChaineDefaillante(
            "test %d : %d cas rejoués sortent de leur propre bande, ce qui "
            "est arithmétiquement impossible. Le défaut est dans la chaîne. "
            "Premiers : %s" % (numero_test, len(echecs), echecs[:3])
        )

    return {
        "test": numero_test,
        "programme_rejoue": lettre,
        "classes_concernees": resultat["classes_concernees"],
        "nb_bandes": resultat["nb_bandes"],
        "nb_cas_rejoues": evalues,
        "nb_non_evaluables": resultat["nb_non_evaluables"],
        "critere": resultat["critere"]["statut"],
        "verdict": resultat["verdict"],
    }


def verifier_distributions(numero_test):
    """Replay one reference program through the distribution engine.

    Args:
        numero_test: SIA test number.

    Returns:
        dict | None: Report, or ``None`` when no criterion applies.

    Raises:
        ChaineDefaillante: If a replayed class falls outside its envelope.
    """
    if numero_test not in moteur_distrib.TESTS_SUPPORTES:
        return None
    try:
        reference = moteur_distrib.charger_reference(numero_test)
    except moteur_distrib.ReferenceIntrouvable:
        return None

    candidat, hors = {}, 0
    for bloc in reference["distributions"]:
        if not bloc["contributeurs"]:
            continue
        lettre = bloc["contributeurs"][0]["colonne"]
        candidat[(bloc["cas"], bloc["grandeur"])] = [
            entree["par_colonne"][lettre] for entree in bloc["effectifs"]
        ]

    resultat = moteur_distrib.evaluer(reference, candidat)
    for bloc in resultat["distributions"]:
        hors += bloc["nb_hors_lecture"].get(moteur_distrib.LECTURE_ENVELOPPE, 0)
    if hors:
        raise ChaineDefaillante(
            "test %d : %d classes rejouées sortent de l'enveloppe min/max "
            "de leur propre jeu — impossible si la chaîne est correcte."
            % (numero_test, hors)
        )

    return {
        "test": numero_test,
        "nb_distributions": resultat["nb_distributions"],
        "nb_evaluees": resultat["nb_evaluees"],
        "critere": resultat["critere"]["statut"],
        "verdict": resultat["verdict"],
    }


def verifier_vue(numero_test):
    """Assemble the navigator view as an end-to-end rendering check.

    Args:
        numero_test: SIA test number.

    Returns:
        dict: Structured view summary.
    """
    from ui import verdict_view as vue

    reference = moteur_bandes.charger_reference(numero_test)
    lettre = choisir_contributeur(reference)
    resultat = moteur_bandes.evaluer(
        reference, candidat_depuis_contributeur(reference, lettre)
    )
    assemblee = vue.construire_vue_bandes(resultat)
    return {
        "test_id": assemblee.get("test_id"),
        "nb_lignes": len(assemblee.get("lignes", [])),
        "couleur": assemblee["verdict_global"]["couleur"],
    }


def executer(tests=TESTS):
    """Run the complete offline evaluation-chain self-test.

    Args:
        tests: Test numbers to check.

    Returns:
        list[dict]: One structured report per test.
    """
    comptes_rendus = []
    for numero in tests:
        if numero == 1:
            rendu = verifier_test1()
        elif numero == 7:
            rendu = verifier_test7()
        elif numero in TESTS_A_BANDES:
            rendu = {
                "bandes": verifier_bandes(numero),
                "distributions": verifier_distributions(numero),
                "vue": verifier_vue(numero),
            }
        else:
            raise ChaineDefaillante(
                "test %s : aucun moteur de reference raccorde." % numero
            )
        comptes_rendus.append(rendu)
    return comptes_rendus


def main(arguments=()):
    """Run the evaluation-chain self-test from command-line arguments.

    Args:
        arguments: Optional test numbers.

    Returns:
        int: Zero when the chain is consistent, otherwise one.
    """
    demandes = [int(a) for a in arguments if a.isdigit()]
    print("AUTO-TEST DE LA CHAINE — reference -> moteur -> verdict -> vue")
    print("Ne prouve PAS que IESVE passe les tests : aucune simulation n est")
    print("en jeu. Prouve que la mecanique tourne de bout en bout.")
    print()
    try:
        rendus = executer(demandes or TESTS)
    except ChaineDefaillante as erreur:
        print("CHAINE DEFAILLANTE : %s" % erreur)
        return 1

    classes = set()
    for rendu in rendus:
        bandes = rendu["bandes"]
        classes.update(bandes["classes_concernees"])
        distributions = rendu["distributions"]
        print(
            "Test %d  programme rejoue %-3s  %2d/%2d cas  classes %s"
            % (
                bandes["test"],
                bandes["programme_rejoue"],
                bandes["nb_cas_rejoues"],
                bandes["nb_bandes"],
                ", ".join(bandes["classes_concernees"]),
            )
        )
        print("         critere somme annuelle : %s" % bandes["critere"])
        if distributions:
            print(
                "         distributions : %d/%d evaluees, critere %s"
                % (
                    distributions["nb_evaluees"],
                    distributions["nb_distributions"],
                    distributions["critere"],
                )
            )
        else:
            print("         distributions : sans objet pour ce test")
        print("         vue : %d lignes" % rendu["vue"]["nb_lignes"])
    print()
    print(
        "Chaine verte sur %d tests, couvrant les classes %s."
        % (len(rendus), ", ".join(sorted(classes)))
    )
    print("AUCUNE de ces classes n est VALIDEE : il y faut une simulation")
    print("IESVE qualifiee et des resultats APS lies aux grandeurs officielles.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
