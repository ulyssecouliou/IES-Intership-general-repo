# -*- coding: utf-8 -*-
"""Tests unitaires de `ui/verdict_view.py`.

Exécutés réellement dans cet environnement (aucune dépendance `tkinter`,
`win32com` ou `reportlab` -- uniquement `engine/` et `ve_adapter/`, tous deux
Python purs). Suit la même doctrine que `engine/tests/test_test1_engine.py` :
piloté par les données réelles (`test-1.ref.json`, fixture de développement),
pas par des doublures synthétiques -- sauf pour les scénarios que ces
données réelles ne couvrent pas (formes anormales, verdict_test1 absent,
etc.), explicitement marqués comme tels.

Aucun `import iesve`/`tkinter`/`win32com`/`reportlab` ici : c'est précisément
ce qui rend ce fichier exécutable sans VE.
"""

import copy
import os
import sys

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import test1_engine as moteur  # noqa: E402
from ve_adapter import test1_adapter as adapter  # noqa: E402
from ui import verdict_view as vue  # noqa: E402

# --------------------------------------------------------------------------
# Fixtures de session : reference figee + fixture candidat de developpement.
# Chargees UNE fois (donnees reelles du depot, pas des doublures).
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def reference():
    return moteur.charger_reference()


@pytest.fixture(scope="module")
def candidat_fixture():
    return adapter.charger_fixture_test1()


@pytest.fixture(scope="module")
def resultat_fixture(reference, candidat_fixture):
    """Le vrai JSON produit par le moteur pour la fixture de developpement --
    exactement ce que consommera le dialogue Tkinter en mode sans VE."""
    return moteur.evaluer_test1(reference, candidat_fixture)


@pytest.fixture(scope="module")
def resultat_sans_candidat(reference):
    """Aucune donnee VE fournie du tout -- le cas que le dialogue Tkinter
    doit afficher tout en gris, jamais en vert, au premier lancement avant
    simulation."""
    return moteur.evaluer_test1(reference, None)


# --------------------------------------------------------------------------
# 1. `couleur_depuis_conforme` -- le contrat de couleur est LA regle non
#    negociable de CLAUDE.md : jamais de vert pour une donnee manquante.
# --------------------------------------------------------------------------


def test_couleur_conforme_true_est_verte():
    assert vue.couleur_depuis_conforme(True) == "vert"


def test_couleur_conforme_false_est_rouge():
    assert vue.couleur_depuis_conforme(False) == "rouge"


def test_couleur_conforme_none_est_grise():
    assert vue.couleur_depuis_conforme(None) == "gris"


def test_couleur_jamais_verte_sauf_true_explicite():
    """Garde-fou direct contre le risque de regression le plus dangereux :
    une valeur falsy non-None (0, 0.0, '') ne doit jamais etre confondue avec
    `False` conforme ni produire un vert."""
    for valeur_suspecte in (0, 0.0, "", [], {}):
        assert vue.couleur_depuis_conforme(valeur_suspecte) != "vert"


# --------------------------------------------------------------------------
# 2. `construire_ligne_periode` -- pas-fail (1E) et informatif, sur des
#    enregistrements REELS extraits du resultat du moteur (pas fabriques).
# --------------------------------------------------------------------------


def test_ligne_1e_conforme_est_verte_et_cite_streubereich(resultat_fixture):
    bloc = resultat_fixture["cas"]["sensible_heating_demand_kwh/1E"]
    verdict_annuel = bloc["periodes"]["annual"]
    assert verdict_annuel["conforme"] is True  # verifie l'hypothese du test
    ligne = vue.construire_ligne_periode(
        "sensible_heating_demand_kwh", "1E", "critere_pass_fail", "annual", verdict_annuel
    )
    assert ligne["couleur"] == "vert"
    assert ligne["texte_verdict"] == vue.TEXTE_CONFORME
    assert "Streubereich" in ligne["article"]
    assert ligne["valeur_candidate"] == verdict_annuel["valeur_candidate"]
    assert ligne["valeur_candidate_affichee"] != "—"


def test_ligne_informative_ne_porte_jamais_de_verdict(resultat_fixture):
    bloc = resultat_fixture["cas"]["sensible_heating_demand_kwh/600"]
    verdict_janvier = bloc["periodes"]["month_01"]
    assert verdict_janvier["conforme"] is None  # cas 600 : aucun critere (spec §6)
    ligne = vue.construire_ligne_periode(
        "sensible_heating_demand_kwh", "600", "informatif", "month_01", verdict_janvier
    )
    assert ligne["couleur"] == "gris"
    assert ligne["conforme"] is None
    assert ligne["texte_verdict"] == vue.TEXTE_NON_APPLICABLE_INFORMATIF
    assert "Abweichungskriterium" in ligne["article"] or "kein" in ligne["article"]
    # Le detail brut (comparaisons par programme) doit rester accessible
    # pour le drill-down, non aplati/perdu par la transformation.
    assert "comparaisons" in ligne["detail"]


def test_ligne_1e_non_evaluee_faute_de_candidat_reste_grise(resultat_sans_candidat):
    """Sans aucune simulation VE, le cas 1E doit rester GRIS, jamais vert ni
    rouge -- garde-fou direct contre le "faux vert par donnee manquante"."""
    bloc = resultat_sans_candidat["cas"]["sensible_heating_demand_kwh/1E"]
    verdict_annuel = bloc["periodes"]["annual"]
    assert verdict_annuel["conforme"] is None
    ligne = vue.construire_ligne_periode(
        "sensible_heating_demand_kwh", "1E", "critere_pass_fail", "annual", verdict_annuel
    )
    assert ligne["couleur"] == "gris"
    assert ligne["conforme"] is None


def test_ligne_pointe_1e_cite_larticle_table_31_dedie(resultat_fixture):
    """Table 31 (charge de pointe) doit citer sa propre source (colonnes
    G/H/I, ligne d'en-tete L81), distincte du Streubereich mensuel usuel."""
    bloc = resultat_fixture["cas"]["annual_hourly_peak_load_kwh/1E"]
    verdict_pointe = bloc["periodes"]["heating"]
    ligne = vue.construire_ligne_periode(
        "annual_hourly_peak_load_kwh",
        "1E",
        "critere_pass_fail",
        "heating",
        verdict_pointe,
    )
    assert "Table 31" in ligne["article"]
    assert ligne["grandeur_libelle"].startswith("Charge de pointe")


def test_construire_ligne_periode_ne_mute_pas_le_json_du_moteur(resultat_fixture):
    """Garde-fou de non-regression : la vue ne doit jamais modifier le JSON
    source (deepcopy defensif), sinon un deuxieme rendu de la meme donnee
    pourrait afficher un etat corrompu."""
    bloc = resultat_fixture["cas"]["sensible_cooling_demand_kwh/900"]
    verdict_original = bloc["periodes"]["annual"]
    empreinte_avant = copy.deepcopy(verdict_original)
    vue.construire_ligne_periode(
        "sensible_cooling_demand_kwh", "900", "informatif", "annual", verdict_original
    )
    assert verdict_original == empreinte_avant


def test_type_controle_inconnu_est_signale_pas_invente():
    ligne = vue.construire_ligne_periode(
        "grandeur_test",
        "cas_test",
        "type_exotique_jamais_vu",
        "annual",
        {"conforme": None, "valeur_candidate": 1.0},
    )
    assert "⚠" in ligne["texte_verdict"]
    assert "⚠" in ligne["article"]
    assert ligne["couleur"] == "gris"


# --------------------------------------------------------------------------
# 3. `construire_lignes_test1` -- vue complete, contre la fixture reelle.
# --------------------------------------------------------------------------


def test_lignes_test1_couvre_exactement_les_cas_du_moteur(resultat_fixture):
    lignes = vue.construire_lignes_test1(resultat_fixture)
    nb_periodes_attendues = sum(
        len(bloc["periodes"]) for bloc in resultat_fixture["cas"].values()
    )
    assert len(lignes) == nb_periodes_attendues
    # Chaque ligne doit correspondre a une cle (grandeur, cas) reellement
    # presente dans le JSON du moteur -- aucune ligne fabriquee.
    cles_moteur = set(resultat_fixture["cas"].keys())
    for ligne in lignes:
        assert (ligne["grandeur"] + "/" + ligne["cas"]) in cles_moteur


def test_lignes_test1_sont_triees_de_facon_stable(resultat_fixture):
    lignes = vue.construire_lignes_test1(resultat_fixture)
    cles_tri = [
        (row["grandeur"], row["cas"], vue._rang_tri_periode(row["periode"]))
        for row in lignes
    ]
    assert cles_tri == sorted(cles_tri)


def test_lignes_test1_1e_sont_toutes_a_type_critere_pass_fail(resultat_fixture):
    lignes = vue.construire_lignes_test1(resultat_fixture)
    lignes_1e = [row for row in lignes if row["cas"] == "1E"]
    assert lignes_1e  # au moins une ligne 1E dans la fixture
    assert all(row["type_controle"] == "critere_pass_fail" for row in lignes_1e)


def test_lignes_test1_aucune_grandeur_hors_moteur_nest_ajoutee(resultat_fixture):
    lignes = vue.construire_lignes_test1(resultat_fixture)
    grandeurs_lignes = {row["grandeur"] for row in lignes}
    grandeurs_moteur = set(bloc["grandeur"] for bloc in resultat_fixture["cas"].values())
    assert grandeurs_lignes == grandeurs_moteur


def test_grandeur_non_repertoriee_est_signalee_pas_masquee():
    """Si le moteur produit un jour une grandeur que ce module ne connait pas
    encore (LIBELLES_GRANDEUR incomplet), le libelle doit le dire -- ne
    jamais afficher un intitule vide ou trompeur."""
    assert vue.libelle_grandeur("grandeur_future_inconnue").startswith("⚠")


# --------------------------------------------------------------------------
# 4. Verdict global -- lu tel quel depuis `verdict_test1`, jamais recalcule.
# --------------------------------------------------------------------------


def test_verdict_global_fixture_reflete_exactement_le_moteur(resultat_fixture):
    verdict = vue.construire_verdict_global(resultat_fixture)
    assert verdict["conforme"] == resultat_fixture["verdict_test1"]["conforme"]
    assert verdict["couleur"] == vue.couleur_depuis_conforme(
        resultat_fixture["verdict_test1"]["conforme"]
    )
    assert verdict["detail"] == resultat_fixture["verdict_test1"]


def test_verdict_global_absent_devient_gris_et_explicite():
    resultat_sans_verdict = {"test_id": "X", "cas": {}}
    verdict = vue.construire_verdict_global(resultat_sans_verdict)
    assert verdict["conforme"] is None
    assert verdict["couleur"] == "gris"
    assert "absent" in verdict["texte"].lower()


def test_verdict_global_sans_candidat_est_gris_jamais_vert(resultat_sans_candidat):
    """Reproduit litteralement la garantie centrale de CLAUDE.md : sans VE,
    le verdict global ne doit jamais s'afficher vert."""
    verdict = vue.construire_verdict_global(resultat_sans_candidat)
    assert verdict["conforme"] is None
    assert verdict["couleur"] == "gris"


# --------------------------------------------------------------------------
# 5. Classes de validation -- limitees a `classes_concernees` du moteur.
# --------------------------------------------------------------------------


def test_lignes_classes_reprend_exactement_classes_concernees(resultat_fixture):
    lignes = vue.construire_lignes_classes(resultat_fixture)
    classes_attendues = set(resultat_fixture["classes_concernees"])
    assert {row["classe"] for row in lignes} == classes_attendues
    assert len(lignes) == len(classes_attendues)


def test_lignes_classes_portent_toutes_le_meme_verdict_global(resultat_fixture):
    lignes = vue.construire_lignes_classes(resultat_fixture)
    verdict_global = vue.construire_verdict_global(resultat_fixture)
    for ligne in lignes:
        assert ligne["conforme"] == verdict_global["conforme"]
        assert ligne["couleur"] == verdict_global["couleur"]


def test_lignes_classes_citent_la_table_63(resultat_fixture):
    lignes = vue.construire_lignes_classes(resultat_fixture)
    assert all("tab. 63" in row["article"] for row in lignes)


def test_classe_5_absente_car_non_concernee_par_test1(resultat_fixture):
    """Reflet exact de traceability/test-1.spec.md §2 (Test 1 non requis en
    classe 5) : la classe 5 ne doit apparaitre nulle part ici, plutot que
    d'etre affichee a tort (vraie absence, pas un oubli)."""
    lignes = vue.construire_lignes_classes(resultat_fixture)
    assert "5" not in [row["classe"] for row in lignes]


# --------------------------------------------------------------------------
# 6. Assemblage complet -- ce que consomment Tkinter/PDF/Excel.
# --------------------------------------------------------------------------


def test_construire_vue_test1_assemble_les_trois_blocs(resultat_fixture):
    v = vue.construire_vue_test1(resultat_fixture)
    assert v["test_id"] == resultat_fixture["test_id"]
    assert (
        v["verdict_global"]["conforme"] == resultat_fixture["verdict_test1"]["conforme"]
    )
    assert len(v["classes"]) == len(resultat_fixture["classes_concernees"])
    assert len(v["lignes"]) == sum(
        len(bloc["periodes"]) for bloc in resultat_fixture["cas"].values()
    )


def test_construire_vue_test1_sur_resultat_reel_ne_leve_aucune_exception(
    reference, candidat_fixture
):
    """Bout en bout reel : reference figee -> moteur -> vue, sans mock."""
    resultat = moteur.evaluer_test1(reference, candidat_fixture)
    v = vue.construire_vue_test1(resultat)
    assert v["lignes"]
    assert v["classes"]


def test_construire_vue_test1_sans_aucun_candidat_reste_entierement_gris(reference):
    """Etat "avant premiere simulation VE" : aucune ligne ne doit etre verte
    ni rouge, uniquement grise -- sinon on afficherait un faux verdict."""
    resultat = moteur.evaluer_test1(reference, None)
    v = vue.construire_vue_test1(resultat)
    couleurs = {row["couleur"] for row in v["lignes"]}
    assert couleurs <= {"gris"}
    assert v["verdict_global"]["couleur"] == "gris"
