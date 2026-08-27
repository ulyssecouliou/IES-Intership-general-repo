# -*- coding: utf-8 -*-
"""Tests of the matrix generator (`scripts/build_traceability_matrix.py`).

A traceability matrix is a CONTROL document: it asserts that a clause is
covered. Two ways to make it harmful, both experienced in this repository:

* **writing a number instead of counting it.** The first version announced
  "only one case carries the pass/fail criterion" — the engine returns three. The
  document was asserting, with the authority of a record, something false;
* **overwriting a draft.** The Test 7 matrix is an independent audit of
  three hundred lines, returned unsigned. A generator cannot produce that
  judgement; overwriting it destroys it without a trace.

These two dangers are what these tests guard against.
"""

import io
import os

import pytest

from scripts import build_traceability_matrix as generateur

# --------------------------------------------------------------------------
# Never overwrite a draft
# --------------------------------------------------------------------------


@pytest.fixture
def sortie(tmp_path, monkeypatch):
    monkeypatch.setattr(generateur, "_SORTIE", str(tmp_path))
    return str(tmp_path)


def _poser(dossier, nom, contenu):
    chemin = os.path.join(dossier, nom)
    with io.open(chemin, "w", encoding="utf-8") as flux:
        flux.write(contenu)
    return chemin


def test_sans_fichier_existant_on_ecrit_a_la_place_attendue(sortie):
    chemin, redigee = generateur.chemin_de_sortie(1)
    assert chemin.endswith("test-1.matrix.md")
    assert redigee is False


def test_une_matrice_redigee_a_la_main_nest_pas_ecrasee(sortie):
    _poser(sortie, "test-7.matrix.md", "# Audit indépendant\n\nRENVOYÉE\n")
    chemin, redigee = generateur.chemin_de_sortie(7)
    assert redigee is True
    assert chemin.endswith("test-7.matrix.releve.md")


def test_le_releve_va_a_cote_sans_toucher_a_la_redaction(sortie):
    original = "# Audit indépendant\n\nRENVOYÉE\n"
    ecrit = _poser(sortie, "test-7.matrix.md", original)
    generateur.chemin_de_sortie(7)
    with io.open(ecrit, encoding="utf-8") as flux:
        assert flux.read() == original


@pytest.mark.parametrize("numero", [1, 2, 3, 4, 5, 6, 7])
def test_une_sortie_du_script_est_bien_reconnue_comme_sienne(sortie, numero):
    """THE REGRESSION EXPERIENCED. The marker had been taken from the header
    banner — worded differently by `construire` and `construire_dedie`.
    Tests 2 to 6 therefore appeared as hand-written drafts, and their
    matrix was placed in a neighbouring file on every run."""
    document = (
        generateur.construire_dedie(numero)
        if numero in generateur.TESTS_DEDIES
        else generateur.construire(numero)
    )
    _poser(sortie, "test-%d.matrix.md" % numero, document)
    chemin, redigee = generateur.chemin_de_sortie(numero)
    assert redigee is False, numero
    assert chemin.endswith("test-%d.matrix.md" % numero)


def test_le_marqueur_est_present_dans_les_deux_generateurs():
    """Direct check of the invariant on which the previous test depends."""
    assert generateur.MARQUE_GENEREE in generateur.construire(2)
    assert generateur.MARQUE_GENEREE in generateur.construire_dedie(1)
    assert generateur.MARQUE_GENEREE in generateur.construire_dedie(7)


# --------------------------------------------------------------------------
# Tests 1 and 7: dedicated engines
# --------------------------------------------------------------------------


def test_les_tests_a_bandes_ne_passent_pas_par_le_generateur_dedie():
    """Their results do not have the same shape: forcing it would produce a
    matrix that talks about non-existent fields."""
    for numero in generateur.TESTS:
        with pytest.raises(ValueError):
            generateur.construire_dedie(numero)


def test_seuls_1_et_7_ont_un_moteur_dedie():
    assert generateur.TESTS_DEDIES == (1, 7)
    assert not set(generateur.TESTS) & set(generateur.TESTS_DEDIES)


def test_les_sept_tests_sont_couverts():
    couverts = set(generateur.TESTS) | set(generateur.TESTS_DEDIES)
    assert couverts == set(range(1, 8))


# --------------------------------------------------------------------------
# The carrying count is COMPUTED
# --------------------------------------------------------------------------


def test_le_nombre_dentrees_porteuses_vient_du_moteur():
    """The hand-written figure was wrong: three entries carry the
    criterion, on the single case 1E."""
    from engine import test1_engine as moteur

    resultat = moteur.evaluer_test1(moteur.charger_reference())
    porteuses = [
        e
        for e in resultat["cas"].values()
        if e.get("type_controle") == "critere_pass_fail"
    ]
    document = generateur.construire_dedie(1)
    assert (
        "**%d entrée(s) sur %d portent le critère pass/fail**"
        % (len(porteuses), len(resultat["cas"]))
        in document
    )


def test_aucun_nombre_de_cas_nest_ecrit_en_toutes_lettres():
    """'un seul cas', 'les dix-huit autres': these wordings are
    exactly the ones that became stale."""
    chemin = os.path.abspath(generateur.__file__).replace(".pyc", ".py")
    with io.open(chemin, encoding="utf-8") as flux:
        source = flux.read()
    for interdit in ("dix-huit autres", "Un seul cas porte", "seul cas porteur du"):
        assert interdit not in source, interdit


def test_le_cas_porteur_est_lu_et_non_affirme():
    from engine import test1_engine as moteur

    resultat = moteur.evaluer_test1(moteur.charger_reference())
    porteurs = sorted(
        set(
            e.get("cas")
            for e in resultat["cas"].values()
            if e.get("type_controle") == "critere_pass_fail"
        )
    )
    document = generateur.construire_dedie(1)
    assert "repose entièrement sur le(s) cas **%s**" % ", ".join(porteurs) in document


# --------------------------------------------------------------------------
# What the matrix must never say
# --------------------------------------------------------------------------


@pytest.mark.parametrize("numero", [1, 7])
def test_aucune_matrice_ne_se_signe_elle_meme(numero):
    """Rule 5: the signature is independent. A script that signs itself
    would be worthless."""
    document = generateur.construire_dedie(numero)
    assert "**non signé**" in document
    assert "NON SIGNÉE" in document


@pytest.mark.parametrize("numero", [1, 7])
def test_aucune_matrice_nannonce_une_validation(numero):
    document = generateur.construire_dedie(numero)
    for interdit in ("validé", "conforme", "PASS"):
        assert interdit not in document, (numero, interdit)


def test_la_matrice_du_test_1_dit_combien_de_controles_restent_non_evalues():
    from engine import test1_engine as moteur

    verdict = moteur.evaluer_test1(moteur.charger_reference()).get("verdict_test1") or {}
    document = generateur.construire_dedie(1)
    assert (
        "%d contrôle(s) sur %d ne sont pas évalués"
        % (
            verdict.get("nb_periodes_non_evaluees", 0),
            verdict.get("nb_periodes_totales", 0),
        )
        in document
    )


def test_la_matrice_du_test_7_nomme_sa_source_dirradiance():
    """Without Kloten irradiance, no Test 7 quantity is computable.
    Hiding this would produce a matrix that appears complete."""
    document = generateur.construire_dedie(7)
    assert "Source d'irradiance" in document


def test_les_classes_concernees_viennent_du_moteur():
    """SIA 4010:2023, tableau 63. Retyping them would make them stale."""
    from engine import test7_engine as moteur

    classes = (
        moteur.evaluer_test7(moteur.charger_reference()).get("classes_concernees") or []
    )
    document = generateur.construire_dedie(7)
    assert ", ".join(classes) in document


# --------------------------------------------------------------------------
# Software chain: existence is checked
# --------------------------------------------------------------------------


@pytest.mark.parametrize("numero", [1, 7])
def test_un_fichier_absent_est_signale_et_non_tu(numero):
    lignes = generateur._tableau_chaine_dediee(numero)
    assert any("| Rôle |" in ligne for ligne in lignes)
    for ligne in lignes[2:]:
        assert ligne.endswith("oui |") or ligne.endswith("**NON** |"), ligne


def test_la_chaine_du_test_1_cite_le_gbxml_et_limport():
    """These are the two links added this week; a matrix that ignored them
    would under-declare the coverage."""
    lignes = "\n".join(generateur._tableau_chaine_dediee(1))
    assert "ve_adapter/gbxml_test1.py" in lignes
    assert "scripts/importer_geometrie_test1.py" in lignes
