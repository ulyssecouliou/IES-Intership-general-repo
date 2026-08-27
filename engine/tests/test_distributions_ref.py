# -*- coding: utf-8 -*-
"""Tests of the reference frequency distributions — SIA tests 2, 3 and 5.

The second criterion of specifications 2, 3 and 5 — "Die Häufigkeitsverteilung
muss im Streubereich der Referenzprogramme liegen" — had never been
extracted. These tests hold the reference that carries it.

They target mostly what a plausible but wrong extraction would produce:
counting a column of zeros as a measurement, missing the totals row, or
inventing a band that the workbook computes nowhere.
"""

import io
import json
import os

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
_DOSSIER = os.path.join(_RACINE, "refs", "reference-data")

#: Tests whose distribution counts are frozen. Tests 4, 6 and 7
#: joined the list on 2026-08-12, when the layout of their workbook was
#: recorded. All integrity checks in this file apply to them.
TESTS = (2, 3, 4, 5, 6, 7)

#: Tests whose specification contains NO "Testkriterien" section.
#: Verified on 2026-08-12 on the three PDFs, after ensuring that their text
#: extracts correctly: zero occurrences of `Testkriterien`, `Streubereich`,
#: `Abweichung` or `Häufigkeitsverteilung`.
#:
#: THIS IS NOT "NO DISTRIBUTION". Their workbooks carry distributions, and
#: confusing the two is what caused the contrary to be asserted to the SIA on
#: 2026-08-07. These three tests have frozen counts; whether the distribution
#: criterion is opposable to them is an open question with the sub-commission.
TESTS_SANS_TESTKRITERIEN = (4, 6, 7)


def _charger(numero):
    chemin = os.path.join(_DOSSIER, "test-%d.distributions.ref.json" % numero)
    if not os.path.exists(chemin):
        pytest.skip("référentiel absent : " "scripts/build_sia_distribution_reference.py")
    with io.open(chemin, encoding="utf-8") as flux:
        return json.load(flux)


@pytest.fixture(scope="module", params=TESTS)
def reference(request):
    return _charger(request.param)


# --------------------------------------------------------------------------
# The criterion is not invented
# --------------------------------------------------------------------------


def test_le_critere_est_confirme_par_lautorite(reference):
    """The workbook does not compute the band, but the SIA confirmed min/max."""
    assert reference["statut_critere"] == "CONFIRME_AUTORITE_2026-08-10"
    assert "GRAPHIQUES" in reference["pourquoi_non_calcule"]
    assert "min/max" in reference["pourquoi_non_calcule"]


def test_le_critere_cite_sa_source(reference):
    """Traceability rule: each check cites its article."""
    assert "Streubereich" in reference["critere"]
    assert "Spezifikation_Test" in reference["critere"]


def test_aucune_bande_nest_publiee(reference):
    """If a band key appeared, someone would have computed it without
    foundation. The reference must carry only counts."""
    texte = json.dumps(reference, ensure_ascii=False).lower()
    for interdit in (
        '"borne_inf',
        '"borne_sup_bande',
        '"moyenne"',
        '"ecart_max"',
        '"bande"',
    ):
        assert interdit not in texte, interdit


# --------------------------------------------------------------------------
# The counts are reconciled with the workbook
# --------------------------------------------------------------------------


def test_chaque_contributeur_totalise_ce_que_le_classeur_annonce(reference):
    """The main safeguard. It validates TWO things at once: reading
    the counts, and detecting the totals row — which is not
    labelled in Test 3."""
    for bloc in reference["distributions"]:
        for contributeur in bloc["contributeurs"]:
            lettre = contributeur["colonne"]
            somme = sum(e["par_colonne"][lettre] or 0 for e in bloc["effectifs"])
            assert somme == contributeur["total_heures"], (
                reference["test"],
                bloc["colonne_bloc"],
                lettre,
            )


def test_aucune_colonne_de_zeros_nest_retenue(reference):
    """A column full of zeros signals a programme that did NOT submit this
    case, not a programme that counted zero hours. Counting it as a measurement
    would corrupt the entire dispersion."""
    for bloc in reference["distributions"]:
        for contributeur in bloc["contributeurs"]:
            assert contributeur["total_heures"] > 0


def test_les_effectifs_ne_sont_jamais_negatifs(reference):
    for bloc in reference["distributions"]:
        for effectif in bloc["effectifs"]:
            for valeur in effectif["par_colonne"].values():
                assert valeur is None or valeur >= 0


def test_tous_les_blocs_ont_le_meme_nombre_de_classes(reference):
    """Classes come from a shared sheet: a block with a different count
    would signal a misaligned read."""
    nombres = set(bloc["nb_classes"] for bloc in reference["distributions"])
    assert len(nombres) == 1, nombres


#: "No upper limit" bound, written as ±9999 by the workbook: `9999` for a
#: positive quantity, `-9999` for a negative quantity such as an evacuated power.
#:
#: THIS IS NOT AN EMPTY CLASS. A test assumed this on 2026-08-12 and the
#: data disproved it: the first ±9999 class of a block captures the hours
#: that exceed the last real bound — 3, 6 or 7 hours depending on the blocks
#: of tests 4, 5 and 7. The ±9999 that follow it are, however, zero. The
#: guarantee on the counts remains the reconciliation with the workbook totals
#: row, not an assumption about this bound.
BORNE_SANS_LIMITE_HAUTE = 9999


def test_les_bornes_sont_monotones(reference):
    """Disordered bounds would signal a misidentified column.

    MONOTONE, NOT INCREASING. This test required increasing bounds, which
    is only true of a positive quantity. Test 6 carries
    'Leistung Wärmeabfuhr WRG', an EVACUATED power therefore negative, whose
    classes decrease: 100, -1000, -2000 ... -10000. Requiring
    increase rejected a correct read of a correct workbook.

    The ±9999 bounds are excluded from the check: they mean "no upper
    limit" and would break monotonicity without signalling anything. They
    carry real counts — see `BORNE_SANS_LIMITE_HAUTE`.
    """
    for bloc in reference["distributions"]:
        bornes = [
            e["borne_superieure"]
            for e in bloc["effectifs"]
            if e["borne_superieure"] is not None
            and abs(e["borne_superieure"]) != BORNE_SANS_LIMITE_HAUTE
        ]
        assert bornes == sorted(bornes) or bornes == sorted(
            bornes, reverse=True
        ), "bloc %s : bornes ni croissantes ni décroissantes : %s" % (
            bloc["colonne_bloc"],
            bornes,
        )


# --------------------------------------------------------------------------
# What the record says about itself
# --------------------------------------------------------------------------


def test_les_heures_hors_classes_sont_explicites(reference):
    """A short displayed total means out-of-class hours, not an incomplete series."""
    totaux = set(
        c["total_heures"]
        for bloc in reference["distributions"]
        for c in bloc["contributeurs"]
    )
    if any(t < 8760 for t in totaux):
        texte = " ".join(reference["reserves"])
        assert "8760" in texte
        assert "heures manquantes" in texte
        for bloc in reference["distributions"]:
            for contributeur in bloc["contributeurs"]:
                assert contributeur["heures_dans_classes"] == contributeur["total_heures"]
                assert (
                    contributeur["heures_dans_classes"]
                    + contributeur["heures_hors_classes"]
                    == contributeur["heures_source_attendues"]
                )


def test_un_bloc_sans_cas_est_signale(reference):
    """Test 5 carries a block that the workbook does not attach to any case. The
    field remains null, and the reserve says so."""
    sans_cas = [b for b in reference["distributions"] if not b["cas"]]
    if sans_cas:
        assert any("identifiant de cas" in r for r in reference["reserves"])


def test_les_reserves_rappellent_la_bande_confirmee(reference):
    assert any("min/max" in r for r in reference["reserves"])


def test_chaque_bloc_nomme_sa_grandeur(reference):
    for bloc in reference["distributions"]:
        assert bloc["grandeur"], bloc["colonne_bloc"]


def test_la_source_est_tracable(reference):
    source = reference["source"]
    assert source["fichier"].endswith(".xlsx")
    assert source["feuille"]
    lignes = source["lignes_de_structure"]
    assert {"cas", "grandeur", "programmes", "classes"} <= set(lignes)
    # `unite` is only present for layouts where the workbook puts the
    # unit on its own line (tests 4, 6, 7). Its absence means
    # "the unit follows the comma", not "unknown".
    assert set(lignes) <= {"cas", "grandeur", "programmes", "classes", "unite"}
    assert all(isinstance(v, int) and v > 0 for v in lignes.values())


# --------------------------------------------------------------------------
# Scope
# --------------------------------------------------------------------------


@pytest.mark.parametrize("numero", TESTS_SANS_TESTKRITERIEN)
def test_les_tests_sans_testkriterien_ont_bien_des_effectifs(numero):
    """The inverse of what this file asserted before 2026-08-12.

    These three tests state no criterion in their specification, and
    their workbooks nonetheless tabulate hourly distributions. Freezing the
    counts says nothing about their opposability; not freezing them said,
    wrongly, that they did not exist.
    """
    chemin = os.path.join(_DOSSIER, "test-%d.distributions.ref.json" % numero)
    assert os.path.exists(chemin), (
        "produire avec scripts/build_sia_distribution_reference.py %d "
        "--ecrire" % numero
    )


def test_lextracteur_refuse_un_test_sans_disposition_relevee():
    """The refusal covers the unread layout, never a supposed
    absence of distribution."""
    from scripts import build_sia_distribution_reference as extracteur

    with pytest.raises(extracteur.ExtractionRefusee, match="aucune disposition relev"):
        extracteur.extraire(1)


def test_le_moteur_ne_gate_pas_ce_qui_est_seulement_extractible():
    """A frozen fact does not authorise a verdict.

    The extractor can read six tests; the engine only evaluates three, those
    whose specification states the criterion. Aligning one with the other without
    an answer from the sub-commission would turn data into a criterion.
    """
    from engine import sia_distributions_engine as moteur
    from scripts import build_sia_distribution_reference as extracteur

    assert set(moteur.TESTS_SUPPORTES) == {2, 3, 5}
    assert set(TESTS_SANS_TESTKRITERIEN).isdisjoint(moteur.TESTS_SUPPORTES)
    assert set(moteur.TESTS_SUPPORTES).issubset(extracteur.TESTS_AVEC_DISTRIBUTION)


@pytest.mark.parametrize(
    "numero,attendu", [(2, 22), (3, 16), (4, 11), (5, 16), (6, 10), (7, 17)]
)
def test_le_nombre_de_distributions_est_fige(numero, attendu):
    """54 distributions in total. If the count changed, it would be either a
    different workbook, or a misaligned read — both warrant a failure."""
    assert _charger(numero)["nb_distributions"] == attendu
