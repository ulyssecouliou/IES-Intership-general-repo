# -*- coding: utf-8 -*-
"""Generates the traceability matrices for band-based SIA tests (2 to 6).

WHY THEY ARE GENERATED AND NOT HAND-WRITTEN. A traceability matrix is a
control document: it asserts that a given clause is covered by a given piece
of code and a given test. Written by hand, it becomes stale at the first
repository change — and a stale matrix is worse than none, since it asserts
coverage that no longer exists.

Everything that is verifiable is therefore READ: quantities and bands come from
the frozen reference datasets, the linkage status comes from the adapter, the
existence of test files is checked on disk. The normative judgement — what the
standard requires, what remains to be proven — is written here, explicitly,
and dated.

WHAT THIS SCRIPT DOES NOT DO. It does not sign anything. Project rule 5
requires an independent `qa-auditor` signature, and a script that signed
itself would be worthless.

Usage:
    python scripts/build_traceability_matrix.py [numero...] [--ecrire]
"""

from __future__ import print_function

import io
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import sia_bandes_engine as moteur_bandes  # noqa: E402
from engine import sia_distributions_engine as moteur_distrib  # noqa: E402
from ve_adapter import bandes_adapter as adaptateur  # noqa: E402

_SORTIE = os.path.join(_RACINE, "traceability")

TESTS = (2, 3, 4, 5, 6)

#: Normative anchor for each test, read from the official documents. The page
#: number refers to the cited PDF; the criterion statement is taken from the
#: « Testkriterien » section of the specification, where it exists.
ANCRAGE = {
    2: {
        "spec": "SIA_4010_geteilter_Link/Test2/Spezifikation_Test2.pdf",
        "criteres_dans_la_spec": True,
        "batiment": "Testraum « ASHRAE 140 » selon EN ISO 52016-1:2017, ch. 7",
        "climat": "SIA 2028 DRY normal, Zürich Kloten",
        "objet": "protection solaire — store toile (2A) et stores à lamelles "
        "avec régulations 1 à 3 de SIA 387/4:2017, tableau 9",
    },
    3: {
        "spec": "SIA_4010_geteilter_Link/Test3/Spezifikation_Test3.pdf",
        "criteres_dans_la_spec": True,
        "batiment": "Testraum « ASHRAE 140 » selon EN ISO 52016-1:2017, ch. 7",
        "climat": "SIA 2028 DRY normal, Zürich Kloten",
        "objet": "éclairage et régulation en fonction de la lumière du jour, "
        "12 cas (4 protections solaires × régulations)",
    },
    4: {
        "spec": "SIA_4010_geteilter_Link/Test4/Spezifikation_Test4.pdf",
        "criteres_dans_la_spec": False,
        "batiment": "Bâtiment exemple, local « Hörsaal », 165,8 m2, sans "
        "fenêtre, sur deux niveaux",
        "climat": "SIA 2028 DRY normal, Zürich Kloten",
        "objet": "climatisation monozone à débit variable, récupération à "
        "plaques sans échange d'humidité (taux 0,75), régulation "
        "CO2",
    },
    5: {
        "spec": "SIA_4010_geteilter_Link/Test5/Spezifikation_Test5.pdf",
        "criteres_dans_la_spec": True,
        "batiment": "Bâtiment exemple",
        "climat": "SIA 2028 DRY normal, Zürich Kloten",
        # « contact 5A-5C, vapeur 5D » was written here. PDF extraction
        # (build_reseau_ventilation_reference) shows that the table has FOUR
        # variant columns for TWO merged cells: the split point is not in the
        # text layer. The two types are therefore described without assigning
        # variants to them.
        "objet": "ventilation mécanique : batteries chaude et froide, "
        "récupération rotative, humidification par contact ou par "
        "vapeur selon la variante (répartition 5A-5D à confirmer)",
    },
    6: {
        "spec": "SIA_4010_geteilter_Link/Test6/Spezifikation_Test6.pdf",
        "criteres_dans_la_spec": False,
        "batiment": "Bâtiment exemple",
        "climat": "SIA 2028 DRY normal, Zürich Kloten",
        # « variantes de récupération de chaleur » was written here. The PDF
        # describes ONE configuration — glycol-water loop — and the frozen
        # reference dataset has only one case, « (ensemble) ». Announcing
        # variants would cause a search for cases that do not exist.
        "objet": "ventilation mécanique à trois étages, récupération par "
        "boucle à eau glycolée (« Kreislaufverbund »), configuration "
        "unique",
    },
}

#: Expected code and test files. Their existence is CHECKED: a matrix that
#: cited a missing file would be a false testimony.
CHAINE = {
    "moteur (somme annuelle)": "engine/sia_bandes_engine.py",
    "moteur (distribution)": "engine/sia_distributions_engine.py",
    "extraction des références": "scripts/build_sia_reference.py",
    "extraction des distributions": "scripts/build_sia_distribution_reference.py",
    "adaptateur VE": "ve_adapter/bandes_adapter.py",
    "tests du moteur (bandes)": "engine/tests/test_sia_bandes_engine.py",
    "tests du moteur (distributions)": "engine/tests/test_distributions_engine.py",
    "tests des références figées": "engine/tests/test_distributions_ref.py",
    "tests de l'adaptateur": "ve_adapter/tests/test_bandes_adapter.py",
}


def _existe(chemin_relatif):
    """True if a repository file exists.

    Args:
        chemin_relatif: Path relative to the root.

    Returns:
        bool: Presence on disk.
    """
    return os.path.exists(os.path.join(_RACINE, chemin_relatif))


def _etat_liaison(numero_test, libelle):
    """Status of a quantity in the extraction chain.

    Args:
        numero_test: SIA test number.
        libelle: German label of the quantity.

    Returns:
        str: Description, as one table row.
    """
    liaison = adaptateur.LIAISONS.get(numero_test, {}).get(libelle, {})
    if liaison.get("aps_varname"):
        return "**LIÉE** → `%s` (niveau `%s`)" % (
            liaison["aps_varname"],
            liaison["niveau"],
        )
    piste = adaptateur.candidats_a_confirmer(numero_test).get(libelle)
    if piste:
        nom = piste["aps_varname_candidat"]
        if nom is None:
            return "candidat impossible — %s" % piste["a_confirmer"][:90]
        return "candidat `%s` (%s), à confirmer" % (nom, piste["niveau_de_preuve"])
    if libelle in adaptateur.sans_candidat(numero_test):
        return "cherché, **aucune variable ne correspond**"
    return "**pas encore cherché**"


def _tableau_grandeurs(numero_test, reference):
    """Rows for the quantity → band → extraction table.

    Args:
        numero_test: SIA test number.
        reference: Annual-sum reference dataset.

    Returns:
        list[str]: Markdown rows.
    """
    lignes = [
        "| Grandeur (libellé du classeur) | Unité | Cas | Chaîne VE |",
        "|---|---|---|---|",
    ]
    for grandeur in reference["grandeurs"]:
        libelle = grandeur["libelle_de"]
        lignes.append(
            "| `%s` | %s | %d | %s |"
            % (
                libelle,
                grandeur.get("unite") or "—",
                len(grandeur["cas"]),
                _etat_liaison(numero_test, libelle),
            )
        )
    return lignes


def _tableau_distributions(distributions):
    """Rows for the distributions table.

    Args:
        distributions: Distribution reference dataset, or `None`.

    Returns:
        list[str]: Markdown rows.
    """
    if distributions is None:
        return []
    lignes = [
        "| Cas | Grandeur | Classes | Programmes de référence |",
        "|---|---|---|---|",
    ]
    for bloc in distributions["distributions"]:
        lignes.append(
            "| %s | `%s` | %d | %d |"
            % (
                bloc["cas"] or "*(non nommé)*",
                bloc["grandeur"],
                bloc["nb_classes"],
                len(bloc["contributeurs"]),
            )
        )
    return lignes


def _tableau_chaine():
    """Rows for the software chain table, existence checked.

    Returns:
        list[str]: Markdown rows.
    """
    lignes = ["| Rôle | Fichier | Présent |", "|---|---|---|"]
    for role, chemin in sorted(CHAINE.items()):
        lignes.append(
            "| %s | `%s` | %s |" % (role, chemin, "oui" if _existe(chemin) else "**NON**")
        )
    return lignes


def construire(numero_test):
    """Builds the traceability matrix for a test.

    Args:
        numero_test: SIA test number.

    Returns:
        str: Markdown document.

    Raises:
        ValueError: If the test is not a band test.
    """
    if numero_test not in TESTS:
        raise ValueError(
            "test %r hors périmètre. Ce script traite les tests à bandes %s. "
            "Le Test 1 (ASHRAE 140) et le Test 7 (PV) ont leurs propres "
            "moteurs et leurs propres matrices." % (numero_test, list(TESTS))
        )

    reference = moteur_bandes.charger_reference(numero_test)
    try:
        distributions = moteur_distrib.charger_reference(numero_test)
    except (ValueError, moteur_distrib.ReferenceIntrouvable):
        distributions = None

    ancrage = ANCRAGE[numero_test]
    resolues = adaptateur.liaisons_resolues(numero_test)
    declarees = adaptateur.LIAISONS.get(numero_test, {})
    nb_bandes = sum(len(g["cas"]) for g in reference["grandeurs"])

    lignes = []
    lignes.append("# Matrice de traçabilité — Test SIA 4010 n° %d" % numero_test)
    lignes.append("")
    lignes.append("> ## Statut : **NON SIGNÉE**")
    lignes.append(">")
    lignes.append(
        "> Motif bloquant : **%d liaison(s) sur %d** entre une "
        "grandeur du classeur et une variable de résultat VE. "
        "Aucune valeur candidate ne peut donc être produite, et "
        "aucune ligne de cette matrice ne porte de résultat "
        "reproduit." % (len(resolues), len(declarees))
    )
    lignes.append(">")
    lignes.append(
        "> Ce document est **généré** par "
        "`scripts/build_traceability_matrix.py` : les grandeurs, "
        "les bandes et l'état des liaisons sont lus dans les "
        "référentiels figés et dans le code, jamais retapés. Une "
        "matrice rédigée à la main se périme au premier changement "
        "— et une matrice périmée affirme une couverture qui "
        "n'existe plus."
    )
    lignes.append(">")
    lignes.append(
        "> **Le script ne signe pas.** La règle 5 demande une "
        "signature `qa-auditor` indépendante."
    )
    lignes.append("")
    lignes.append("---")
    lignes.append("")

    lignes.append("## 1. Ancrage normatif")
    lignes.append("")
    lignes.append("| Élément | Valeur | Source |")
    lignes.append("|---|---|---|")
    lignes.append(
        "| Classes de validation concernées | %s | SIA 4010:2023, "
        "tableau 63 (p. 48) |" % ", ".join(reference.get("classes_concernees", []))
    )
    lignes.append(
        "| Bâtiment / local | %s | %s |"
        % (ancrage["batiment"], os.path.basename(ancrage["spec"]))
    )
    lignes.append("| Climat | %s | idem |" % ancrage["climat"])
    lignes.append("| Objet du test | %s | idem |" % ancrage["objet"])
    lignes.append(
        "| Classeur d'évaluation | `%s` | SIA 4010:2023, §4.4 |"
        % reference["source"]["fichier"]
    )
    lignes.append("")

    lignes.append("## 2. Critères")
    lignes.append("")
    if ancrage["criteres_dans_la_spec"]:
        lignes.append(
            "La spécification énonce **deux** critères, dans sa "
            "section *Testkriterien*."
        )
    else:
        # THIS TEXT SAID THE OPPOSITE, AND IT WAS WRONG. It claimed that the
        # workbook carried "neither frequency classes nor a distribution
        # sheet", therefore that the annual sum was the only criterion,
        # "an observation, not a gap". Verified on 2026-08-10 by opening the
        # workbooks: tests 4 and 6 carry a `Haeufigkeitskassen` sheet —
        # without the « l » of `Haeufigkeitsklassen`, a typo in the official
        # files taken for an absence — and a « Stündliche
        # Häufigkeitsverteilung » section in their `Zusammenfassung`. The
        # authority clarification of the same day says the same.
        lignes.append(
            "La spécification ne comporte **aucune** section "
            "*Testkriterien* : SIA 4010:2023 §4.4 délègue au "
            "classeur d'évaluation."
        )
        lignes.append("")
        lignes.append(
            "> **Corrigé le 2026-08-10.** Cette matrice affirmait "
            "que le classeur ne porte ni classes de fréquence ni "
            "feuille de distribution. C'est faux : il porte une "
            "feuille `Haeufigkeitskassen` (23 lignes) et une "
            "section « Stündliche Häufigkeitsverteilung » dans "
            "`Zusammenfassung`. L'erreur tenait à une lettre — "
            "les tests 2, 3 et 5 écrivent "
            "`Haeufigkeitsklassen`. La distribution est donc un "
            "critère de ce test aussi ; elle n'est PAS ENCORE "
            "extraite, et la matrice ne peut rien en dire tant "
            "qu'elle ne l'est pas. Source : "
            "`traceability/sia4010-authority-clarification-"
            "2026-08-10.json`, décision "
            "`SIA4010-TEST4-6-DISTRIBUTION-PRESENCE`."
        )
    lignes.append("")
    lignes.append("### 2.1 Somme annuelle")
    lignes.append("")
    lignes.append("- Formule appliquée : `%s`" % reference["critere"].get("formule", "—"))
    statut_annuel, justification_annuelle = moteur_bandes.critere_du_test(numero_test)
    lignes.append(
        "- Statut du critère : **%s** — %s" % (statut_annuel, justification_annuelle)
    )
    lignes.append("- Bandes figées : **%d**" % nb_bandes)
    lignes.append("")
    lignes.append("### 2.2 Distribution de fréquence")
    lignes.append("")
    if distributions is None:
        lignes.append(
            "**Sans objet pour ce test.** Le classeur ne porte ni "
            "feuille `Haeufigkeitsklassen` ni feuille "
            "`Verteilung`."
        )
    else:
        lignes.append("- Énoncé : %s" % distributions["critere"])
        lignes.append("- Statut du critère : **%s**" % moteur_distrib.STATUT_CRITERE)
        lignes.append("- Motif : %s" % distributions["pourquoi_non_calcule"])
        lignes.append(
            "- Distributions figées : **%d**, sur **%d** classes"
            % (
                distributions["nb_distributions"],
                distributions["distributions"][0]["nb_classes"],
            )
        )
        lignes.append(
            "- Les deux lectures du `Streubereich` sont calculées "
            "(`%s`, `%s`) et **aucune n'est retenue** : le moteur "
            "ne rend jamais de verdict conforme." % moteur_distrib.LECTURES
        )
    lignes.append("")

    lignes.append("## 3. Grandeurs, bandes et chaîne d'extraction")
    lignes.append("")
    lignes.extend(_tableau_grandeurs(numero_test, reference))
    lignes.append("")

    if distributions is not None:
        lignes.append("## 4. Distributions de référence")
        lignes.append("")
        lignes.extend(_tableau_distributions(distributions))
        lignes.append("")
        for reserve in distributions.get("reserves", []):
            lignes.append("> %s" % reserve)
            lignes.append(">")
        lignes.append("")

    lignes.append("## %d. Chaîne logicielle" % (5 if distributions else 4))
    lignes.append("")
    lignes.extend(_tableau_chaine())
    lignes.append("")

    lignes.append("## %d. Ce qui n'est PAS établi" % (6 if distributions else 5))
    lignes.append("")
    lignes.extend(_ce_qui_manque(numero_test, distributions, resolues, declarees))
    lignes.append("")
    lignes.append("---")
    lignes.append("")
    lignes.append("## Signature")
    lignes.append("")
    lignes.append("| Rôle | Nom | Date | Verdict |")
    lignes.append("|---|---|---|---|")
    lignes.append(
        "| Producteur | `build_traceability_matrix.py` (généré) | " "— | non applicable |"
    )
    lignes.append("| Vérificateur indépendant | `qa-auditor` | — | " "**non signé** |")
    lignes.append("")
    return "\n".join(lignes) + "\n"


def _ce_qui_manque(numero_test, distributions, resolues, declarees):
    """Lists what prevents signing.

    Args:
        numero_test: SIA test number.
        distributions: Distribution reference dataset, or `None`.
        resolues: Resolved linkages.
        declarees: Declared linkages.

    Returns:
        list[str]: Markdown rows.
    """
    lignes = []
    lignes.append(
        "1. **Aucune valeur candidate.** %d liaison(s) sur %d sont "
        "établies. Tant qu'elles ne le sont pas, aucun cas ne peut "
        "être évalué et le moteur les traite en `NOT_CHECKABLE` — "
        "ce qui est la vérité, mais ne vaut pas conformité."
        % (len(resolues), len(declarees))
    )
    lignes.append(
        "2. **Aucune simulation.** Le test n'a jamais été construit "
        "ni simulé dans IESVE. Les bandes de référence sont "
        "vérifiées ; le comportement de VE face à elles ne l'est "
        "pas."
    )
    if distributions is not None:
        lignes.append(
            "3. **La bande des distributions n'est pas définie.** "
            "Le classeur officiel ne la calcule nulle part. Deux "
            "lectures restent défendables et le choix appartient à "
            "la sous-commission SIA, pas à cet outil."
        )
    muettes = adaptateur.sans_candidat(numero_test)
    if muettes:
        lignes.append(
            "%d. **%d grandeur(s) sans variable VE correspondante** "
            "sur le modèle sondé : %s. Un modèle doté d'un réseau "
            "ApacheHVAC pourrait en exposer davantage — à vérifier "
            "avant de conclure."
            % (
                4 if distributions else 3,
                len(muettes),
                ", ".join("`%s`" % m for m in sorted(muettes)),
            )
        )
    return lignes


# ---------------------------------------------------------------------------
# Tests 1 and 7 — dedicated engines and reference shapes
# ---------------------------------------------------------------------------
#
# They do not go through `sia_bandes_engine` and their results do not have the
# same shape: Test 1 returns `cas` indexed by « quantity/case » and carries
# neither `grandeurs` nor `critere`; Test 7 adds `source_irradiance` and
# `grandeurs_verrouillees`. Forcing them into the Test 2–6 template would
# produce matrices that reference non-existent fields.

TESTS_DEDIES = (1, 7)

ANCRAGE_DEDIE = {
    1: {
        "spec": "SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf",
        "batiment": "Testraum « ASHRAE 140 » selon EN ISO 52016-1:2017, ch. 7",
        "climat": "ISO 52016-1 DRYCOLD pour les six cas principaux ; "
        "SIA 2028 DRY Zürich Kloten pour les cas diagnostiques",
        "objet": "besoins de chaleur et de froid, températures opératives et "
        "charge de pointe horaire, sur la cellule d'essai",
    },
    7: {
        "spec": "SIA_4010_geteilter_Link/Test7/Spezifikation_Test7.pdf",
        "batiment": "Bâtiment exemple",
        "climat": "SIA 2028 DRY normal, Zürich Kloten",
        "objet": "besoins de chaleur et de froid pour profils existants, "
        "production photovoltaïque comprise",
    },
}


def _tableau_cas_test1(resultat):
    """Rows for the Test 1 case table.

    The column that matters is `type_controle`: only a minority of entries
    carry the pass/fail criterion, the others are informative. A matrix that
    presented them equally would suggest that all of them decide the verdict.
    Their count is COMPUTED, never written: the first draft announced "a single
    case" where the engine returns three.

    Args:
        resultat: What `evaluer_test1` returns.

    Returns:
        list[str]: Markdown rows.
    """
    lignes = [
        "| Grandeur | Cas | Nature du contrôle | Périodes | Évaluées |",
        "|---|---|---|---|---|",
    ]
    for cle in sorted(resultat["cas"]):
        entree = resultat["cas"][cle]
        periodes = entree.get("periodes") or {}
        evaluees = sum(
            1 for p in periodes.values() if p.get("valeur_candidate") is not None
        )
        nature = entree.get("type_controle") or "—"
        marque = (
            "**critère pass/fail**" if nature == "critere_pass_fail" else "informatif"
        )
        lignes.append(
            "| `%s` | %s | %s (`%s`) | %d | %d |"
            % (
                entree.get("grandeur"),
                entree.get("cas"),
                marque,
                nature,
                len(periodes),
                evaluees,
            )
        )
    return lignes


def _tableau_grandeurs_test7(resultat):
    """Rows for the Test 7 quantities table.

    Args:
        resultat: What `evaluer_test7` returns.

    Returns:
        list[str]: Markdown rows.
    """
    lignes = ["| Grandeur | Unité | Statut | Candidat |", "|---|---|---|---|"]
    for grandeur in resultat.get("grandeurs") or []:
        lignes.append(
            "| `%s` | %s | %s | %s |"
            % (
                grandeur.get("libelle") or grandeur.get("libelle_de"),
                grandeur.get("unite") or "—",
                grandeur.get("statut") or "—",
                "—" if grandeur.get("candidat") is None else grandeur.get("candidat"),
            )
        )
    return lignes


def construire_dedie(numero_test):
    """Builds the traceability matrix for a test with a dedicated engine (1 or 7).

    Args:
        numero_test: 1 or 7.

    Returns:
        str: Markdown document.

    Raises:
        ValueError: If the test has no dedicated engine.
    """
    if numero_test not in TESTS_DEDIES:
        raise ValueError(
            "test %r sans moteur dédié. Concernés : %s. Les tests 2 à 6 "
            "passent par `construire`." % (numero_test, list(TESTS_DEDIES))
        )

    ancrage = ANCRAGE_DEDIE[numero_test]
    if numero_test == 1:
        from engine import test1_engine as moteur

        resultat = moteur.evaluer_test1(moteur.charger_reference())
        classes = resultat.get("classes_concernees") or []
        verdict = resultat.get("verdict_test1") or {}
        total = verdict.get("nb_periodes_totales", 0)
        non_evaluees = verdict.get("nb_periodes_non_evaluees", 0)
        statut_critere = "ÉNONCÉ DANS LA SPEC"
        justification = (
            "Le Test 1 est le seul dont la spécification énonce ses propres "
            "critères ; ils ne sont pas inférés du classeur."
        )
    else:
        from engine import test7_engine as moteur

        resultat = moteur.evaluer_test7(moteur.charger_reference())
        classes = resultat.get("classes_concernees") or []
        total = len(resultat.get("grandeurs") or [])
        non_evaluees = resultat.get("nb_non_evaluables", 0)
        critere = resultat.get("critere") or {}
        statut_critere = critere.get("statut") or "—"
        justification = critere.get("justification") or ""

    lignes = [
        "# Matrice de traçabilité — Test SIA 4010 n° %d" % numero_test,
        "",
        "> ## Statut : **NON SIGNÉE**",
        ">",
        "> **%d contrôle(s) sur %d ne sont pas évalués** : aucune simulation "
        "IESVE n'a produit de valeur candidate. Aucune ligne de cette "
        "matrice ne porte donc de résultat reproduit." % (non_evaluees, total),
        ">",
        "> Document **généré** par `scripts/build_traceability_matrix.py` : "
        "les grandeurs, les cas et leur état sont lus dans le moteur et dans "
        "les référentiels figés, jamais retapés. Le script **ne signe pas** — "
        "la règle 5 demande une vérification indépendante.",
        "",
        "---",
        "",
        "## 1. Ancrage normatif",
        "",
        "| Élément | Valeur | Source |",
        "|---|---|---|",
        "| Classes de validation concernées | %s | SIA 4010:2023, tableau 63 "
        "(p. 48) |" % ", ".join(classes),
        "| Bâtiment / local | %s | %s |"
        % (ancrage["batiment"], os.path.basename(ancrage["spec"])),
        "| Climat | %s | idem |" % ancrage["climat"],
        "| Objet du test | %s | idem |" % ancrage["objet"],
        "",
        "## 2. Critère",
        "",
        "- Statut : **%s**" % statut_critere,
        "- %s" % justification,
        "",
    ]

    if numero_test == 1:
        lignes.append("## 3. Cas et nature du contrôle")
        lignes.append("")
        # This count was WRITTEN by hand — and wrong: the engine returns three
        # carrying entries, not one. We compute it, like everything else.
        porteuses = [
            entree
            for entree in resultat["cas"].values()
            if entree.get("type_controle") == "critere_pass_fail"
        ]
        cas_porteurs = sorted(set(e.get("cas") for e in porteuses))
        lignes.append(
            "**%d entrée(s) sur %d portent le critère pass/fail**, sur le(s) "
            "cas %s. Les autres sont informatives : les présenter à égalité "
            "laisserait croire qu'elles décident du verdict."
            % (len(porteuses), len(resultat["cas"]), ", ".join(cas_porteurs) or "—")
        )
        lignes.append("")
        lignes.extend(_tableau_cas_test1(resultat))
    else:
        lignes.append("## 3. Grandeurs")
        lignes.append("")
        lignes.extend(_tableau_grandeurs_test7(resultat))
        verrouillees = resultat.get("grandeurs_verrouillees") or []
        if verrouillees:
            lignes.append("")
            lignes.append(
                "**Grandeurs verrouillées** : %s. Leur calcul exige "
                "une entrée absente du dépôt."
                % ", ".join("`%s`" % g for g in verrouillees)
            )
        lignes.append("")
        lignes.append(
            "- Source d'irradiance : `%s`"
            % (resultat.get("source_irradiance") or "AUCUNE")
        )

    lignes.extend(
        [
            "",
            "## 4. Chaîne logicielle",
            "",
        ]
    )
    lignes.extend(_tableau_chaine_dediee(numero_test))
    lignes.extend(
        [
            "",
            "## 5. Ce qui n'est PAS établi",
            "",
            "1. **Aucune valeur candidate.** %d contrôle(s) sur %d restent non "
            "évalués faute de simulation." % (non_evaluees, total),
            "2. **Aucune simulation.** Le test n'a jamais été construit ni "
            "simulé dans IESVE.",
        ]
    )
    if numero_test == 1:
        # Which case carries the criterion is READ from the engine: writing it
        # would make the matrix an assertion, not a record.
        lignes.append(
            "3. **Les cas diagnostiques 1A à 1E sont hors de portée** : ils "
            "exigent le climat de Zürich-Kloten, absent du dépôt. Or le "
            "critère pass/fail repose entièrement sur le(s) cas **%s** — "
            "sans eux, aucun verdict formel du Test 1 n'est possible."
            % (", ".join(cas_porteurs) or "aucun")
        )
    else:
        lignes.append(
            "3. **La divergence de mise en forme conditionnelle est résolue.** "
            "Le classeur corrigé reçu le 2026-08-10 utilise `$N8` / `$M8`, "
            "soit `[borne basse ; borne haute]`. Son SHA-256 est "
            "`24937d8f421daa74a7f957025bfeb17a42fe2dc807b1a301a6752f4c0e808958` ; "
            "le contrôle XML et l'ancienne identité sont consignés dans "
            "`traceability/sia4010-authority-clarification-2026-08-10.json`."
        )
    lignes.extend(
        [
            "",
            "---",
            "",
            "## Signature",
            "",
            "| Rôle | Nom | Date | Verdict |",
            "|---|---|---|---|",
            "| Producteur | `build_traceability_matrix.py` (généré) | — | non "
            "applicable |",
            "| Vérificateur indépendant | `qa-auditor` | — | **non signé** |",
            "",
        ]
    )
    return "\n".join(lignes) + "\n"


def _tableau_chaine_dediee(numero_test):
    """Software chain for a test with a dedicated engine, existence checked.

    Args:
        numero_test: 1 or 7.

    Returns:
        list[str]: Markdown rows.
    """
    fichiers = {
        "moteur": "engine/test%d_engine.py" % numero_test,
        "référence figée": "refs/reference-data/test-%d.ref.json" % numero_test,
        "vue du navigateur": "ui/verdict_view.py",
    }
    if numero_test == 1:
        fichiers["adaptateur VE"] = "ve_adapter/test1_adapter.py"
        fichiers["géométrie"] = "ve_adapter/geometrie_test1.py"
        fichiers["gbXML"] = "ve_adapter/gbxml_test1.py"
        fichiers["import + confrontation"] = "scripts/importer_geometrie_test1.py"

    lignes = ["| Rôle | Fichier | Présent |", "|---|---|---|"]
    for role, chemin in sorted(fichiers.items()):
        lignes.append(
            "| %s | `%s` | %s |" % (role, chemin, "oui" if _existe(chemin) else "**NON**")
        )
    return lignes


#: Marker that identifies our own outputs — and therefore what may be
#: overwritten. It is the SIGNATURE LINE, the only string written identically
#: by both `construire` and `construire_dedie`: the header banner is worded
#: differently in each, and a marker taken from there was classifying tests 2
#: to 6 as hand-written documents.
MARQUE_GENEREE = "| Producteur | `build_traceability_matrix.py` (généré) |"


def chemin_de_sortie(numero_test):
    """Where to write the matrix for a test, without ever overwriting a draft.

    Test 7 carries a HAND-WRITTEN matrix: three hundred lines of independent
    audit, returned unsigned. A generator cannot produce that judgement, and
    overwriting it would destroy it without trace. The rule is therefore
    general: **if the expected file was not written by this script**, the
    generated content goes into a neighbouring file and the draft remains
    intact.

    Args:
        numero_test: SIA test number.

    Returns:
        tuple: `(chemin, une_redaction_existe)`.
    """
    attendu = os.path.join(_SORTIE, "test-%d.matrix.md" % numero_test)
    if not os.path.exists(attendu):
        return attendu, False
    with io.open(attendu, encoding="utf-8") as flux:
        deja_generee = MARQUE_GENEREE in flux.read()
    if deja_generee:
        return attendu, False
    voisin = os.path.join(_SORTIE, "test-%d.matrix.releve.md" % numero_test)
    return voisin, True


def main(arguments):
    """Command-line entry point.

    Args:
        arguments: Test numbers, and `--ecrire`.

    Returns:
        int: 0 if everything went well.
    """
    demandes = [int(a) for a in arguments if a.isdigit()]
    for numero in demandes or (list(TESTS) + list(TESTS_DEDIES)):
        # Tests 1 and 7 have their own engines and reference shapes: forcing
        # them into the band-test template would produce matrices that reference
        # non-existent fields.
        document = (
            construire_dedie(numero) if numero in TESTS_DEDIES else construire(numero)
        )
        chemin, redigee = chemin_de_sortie(numero)
        print("Test %d : %d lignes" % (numero, document.count("\n")))
        if redigee:
            print(
                "    matrice RÉDIGÉE présente : elle est conservée. "
                "Le relevé va à côté."
            )
        if "--ecrire" in arguments:
            with io.open(chemin, "w", encoding="utf-8") as flux:
                flux.write(document)
            print("    écrit : %s" % os.path.relpath(chemin, _RACINE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
