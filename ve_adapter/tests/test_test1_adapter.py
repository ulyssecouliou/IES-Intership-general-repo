# -*- coding: utf-8 -*-
"""Tests de `ve_adapter/test1_adapter.py` -- la couche qui PRODUIT les nombres.

POURQUOI CE FICHIER EXISTE
--------------------------
La revue independante du 2026-08-01 (`docs/ETAT-DES-LIEUX.md`, bloquant B3) a
mesure : 1137 lignes, seul point de contact du depot avec l'API `iesve`, sur le
chemin critique, **zero test et trois mutations sur trois non detectees**, dont
un decalage de curseur dans l'agregation mensuelle.

Tout le reste de la chaine est solide -- moteur prouve contre 48 bandes
officielles, references auditees 1352/1352, empreinte CI resistante aux
mutations. Mais cette chaine protege des donnees que CE module est seul a
fabriquer. C'est le maillon faible d'un ensemble par ailleurs sain.

DEUX FAMILLES DE CONTROLES
--------------------------
1. **Confrontation aux valeurs normatives figees.** Les constantes codees en dur
   du module (geometrie, consignes, apports, materiaux) sont confrontees a
   `traceability/iso-52016-1-ch7-valeurs.spec.md`, lui-meme etabli par lecture
   directe de BS EN ISO 52016-1:2017 §7.2 (p. 122-134). C'est la classe de test
   qui aurait attrape l'ecart ASHRAE-2023 / ISO-2017 sur le vitrage.
2. **Resistance a la mutation sur l'agregation.** Le decoupage mensuel et le
   ramenage au pas horaire sont de l'arithmetique d'indices : un decalage de
   curseur ou un mois de mauvaise longueur produit des nombres plausibles et
   faux. Ces tests sont ecrits pour tomber sur ce genre de faute.

Aucun `iesve` n'est requis : le module expose un accesseur paresseux `_iesve()`,
et tout ce qui est teste ici est du calcul pur ou du dialogue avec un double.
"""

import calendar
import importlib.util
import os
import sys

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)


def _charger_adaptateur():
    """Charge le module par chemin : `ve_adapter/` n'est pas un paquet."""
    chemin = os.path.join(RACINE, "ve_adapter", "test1_adapter.py")
    spec = importlib.util.spec_from_file_location("test1_adapter_sous_test", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adaptateur = _charger_adaptateur()

HEURES_PAR_AN = 365 * 24


# ==========================================================================
# 1. Confrontation aux valeurs normatives figees
#    Source : traceability/iso-52016-1-ch7-valeurs.spec.md
#             = BS EN ISO 52016-1:2017 §7.2, p. 122-134
# ==========================================================================


def test_geometrie_concorde_avec_iso_tableau_22():
    """8,0 x 6,0 x 2,7 m, volume 129,6 m3, deux fenetres de 3,0 x 2,0 m.

    ISO 52016-1:2017 §7.2.2.2, figure 2 et tableau 22.
    """
    g = adaptateur.GEOMETRIE_CELLULE
    assert g["largeur_facade_sud_m"] == 8.0
    assert g["profondeur_m"] == 6.0
    assert g["hauteur_m"] == 2.7
    assert g["nombre_fenetres_sud"] == 2
    assert g["largeur_fenetre_m"] == 3.0
    assert g["hauteur_fenetre_m"] == 2.0

    volume = g["largeur_facade_sud_m"] * g["profondeur_m"] * g["hauteur_m"]
    assert abs(volume - 129.6) < 1e-9, "Volume {0} m3, ISO tableau 22 donne 129,6".format(
        volume
    )

    aire_fenetres = (
        g["nombre_fenetres_sud"] * g["largeur_fenetre_m"] * g["hauteur_fenetre_m"]
    )
    assert (
        abs(aire_fenetres - 12.0) < 1e-9
    ), "Aire vitree {0} m2, ISO tableau 22 donne 12,0".format(aire_fenetres)

    sol = g["largeur_facade_sud_m"] * g["profondeur_m"]
    assert abs(sol - 48.0) < 1e-9, "Plancher/plafond : ISO donne 48,0 m2"


def test_la_facade_ferme_dimensionnellement():
    """2 x 0,5 + 2 x 3,0 + 1,0 = 8,0 m. Le garde-fou du module doit le voir."""
    assert adaptateur._verifier_fermeture_geometrie() is not False
    incoherente = dict(adaptateur.GEOMETRIE_CELLULE)
    incoherente["trumeau_central_m"] = 1.5  # la facade ne ferme plus
    with pytest.raises(ValueError):
        adaptateur._verifier_fermeture_geometrie(incoherente)


def test_consignes_concordent_avec_iso_7_2_2_15():
    """Continu 20/27 degres ; intermittent 10 degres de 23h00 a 07h00.

    ISO 52016-1:2017 §7.2.2.15. « (no night time set back for cooling) » :
    il n'existe donc PAS de consigne de refroidissement reduite.
    """
    assert adaptateur.CONSIGNE_CHAUFFAGE_C == 20.0
    assert adaptateur.CONSIGNE_REFROIDISSEMENT_C == 27.0
    assert adaptateur.CONSIGNE_CHAUFFAGE_REDUITE_C == 10.0
    assert adaptateur.HEURE_DEBUT_CONFORT == 7
    assert adaptateur.HEURE_FIN_CONFORT == 23
    assert not hasattr(
        adaptateur, "CONSIGNE_REFROIDISSEMENT_REDUITE_C"
    ), "ISO §7.2.2.15 exclut tout relachement nocturne en refroidissement"


def test_apport_interne_concorde_avec_iso_7_2_2_13():
    """200 W en continu, 24 h/24 toute l'annee (ISO §7.2.2.13).

    Seuls les 200 W sont assertes : c'est la donnee d'entree normative, et
    c'est elle que l'adaptateur injecte dans le modele.

    ⚠ POINT OUVERT, VOLONTAIREMENT NON ASSERTE. La meme clause annonce un flux
    surfacique specifique « q_int = 1,453 W/m2 ». Il ne se reconcilie avec
    aucune surface de la cellule : 200 / 48 (plancher) = 4,167 ;
    200 / 129,6 (volume) = 1,543 ; 200 / 171,6 (enveloppe) = 1,166. La surface
    qui donnerait 1,453 vaut 137,6 m2, sans correspondance connue.

    Trois explications possibles, aucune tranchee : une erreur de transcription
    lors de la lecture des pages ISO, une coquille de la norme, ou une surface
    de reference qui nous echappe. Tant que ce n'est pas relu sur le document,
    ce test n'encode PAS 1,453 -- asserter une valeur qu'on ne sait pas deriver
    reviendrait a graver l'erreur dans la suite de tests.
    Consigne dans traceability/iso-52016-1-ch7-valeurs.spec.md §6 et
    docs/ETAT-DES-LIEUX.md.
    """
    assert adaptateur.GAIN_EQUIPEMENT_W == 200.0

    surface_plancher = (
        adaptateur.GEOMETRIE_CELLULE["largeur_facade_sud_m"]
        * adaptateur.GEOMETRIE_CELLULE["profondeur_m"]
    )
    flux_specifique = adaptateur.GAIN_EQUIPEMENT_W / surface_plancher
    assert abs(flux_specifique - 4.1666666667) < 1e-6, (
        "Sur les 48 m2 de plancher, 200 W donnent 4,1667 W/m2. Si ce calcul "
        "change, c est que la geometrie ou le gain a bouge."
    )


def test_repartition_masse_par_cas_conforme_au_tableau_27():
    """ISO tableau 27 : 600/640/600FF legers, 900/940/900FF lourds."""
    attendu = {
        "600": "legere",
        "640": "legere",
        "600FF": "legere",
        "900": "lourde",
        "940": "lourde",
        "900FF": "lourde",
    }
    for cas, masse in attendu.items():
        assert (
            adaptateur.MASSE_PAR_CAS[cas] == masse
        ), "Cas {0} : ISO tableau 27 le classe {1}".format(cas, masse)


def test_familles_de_cas_coherentes_avec_le_tableau_27():
    """Les trois familles doivent partitionner les six cas ISO, plus 1E."""
    assert set(adaptateur.CAS_AVEC_CONSIGNE_REDUITE) == {"640", "940"}
    assert set(adaptateur.CAS_FLOTTEMENT_LIBRE) == {"600FF", "900FF"}
    conditionnes = set(adaptateur.CAS_AVEC_CONDITIONNEMENT)
    assert conditionnes.isdisjoint(
        adaptateur.CAS_FLOTTEMENT_LIBRE
    ), "Un cas en flottement libre ne peut pas etre conditionne"
    assert set(adaptateur.CAS_AVEC_CONSIGNE_REDUITE) <= conditionnes


def test_annee_de_simulation_non_bissextile():
    """L'agregation mensuelle suppose 8760 h : une bissextile la fausserait."""
    assert not calendar.isleap(adaptateur.ANNEE_SIMULATION)
    assert (
        sum(calendar.monthrange(adaptateur.ANNEE_SIMULATION, m)[1] for m in range(1, 13))
        * 24
        == HEURES_PAR_AN
    )


def test_les_coefficients_ashrae_ne_sont_plus_la_source_retenue():
    """Garde-fou documentaire, pas une exigence de valeur.

    `COEFFICIENTS_SURFACE_TABLE_7_7` porte les coefficients combines
    d'ASHRAE 140:2023 (Table 7-7). Or le projet a etabli que SIA 4010 vise
    ISO 52016-1:2017, laquelle cite ASHRAE 140 de **2014** et fournit ses
    propres coefficients au tableau 25 (h_ce = 20, h_lr;e = 4,14). Les deux
    conventions ne se melangent pas.

    Ce test ne force pas la valeur -- le choix de convention n'est pas encore
    tranche pour ApacheSim. Il exige que l'ecart reste VISIBLE : si quelqu'un
    remplace ces coefficients par ceux d'ISO sans le documenter, ou s'en sert
    comme s'ils faisaient autorite, ce test doit etre revu consciemment.
    """
    coeffs = adaptateur.COEFFICIENTS_SURFACE_TABLE_7_7
    assert coeffs["mur"]["combine"] == 21.6
    assert coeffs["fenetre"]["combine"] == 17.8
    assert coeffs["mur"]["combine"] != 20.0, (
        "20 W/(m2K) est le h_ce d'ISO tableau 25 : si cette valeur apparait "
        "ici, la source a change et la docstring du module doit suivre"
    )


# ==========================================================================
# 2. Agregation : resistance a la mutation
# ==========================================================================


def _serie_par_mois(valeur_du_mois):
    """Serie horaire ou chaque heure porte la valeur de SON mois."""
    serie = []
    for mois in range(1, 13):
        heures = calendar.monthrange(adaptateur.ANNEE_SIMULATION, mois)[1] * 24
        serie.extend([float(valeur_du_mois(mois))] * heures)
    return serie


def test_decoupage_mensuel_respecte_la_longueur_reelle_des_mois():
    """Chaque fenetre doit couvrir exactement son mois.

    Tue le decalage de curseur : si le curseur derape d'une heure, un mois
    empiete sur le suivant et la moyenne se contamine. Avec une serie dont
    chaque heure porte le numero de son mois, toute contamination est visible.
    """
    serie = _serie_par_mois(lambda m: m)
    assert len(serie) == HEURES_PAR_AN
    mensuel, _moy_mens, _moy_hor = adaptateur._agreger_mensuel_moyennes(serie)
    for indice, cle in enumerate(adaptateur.MOIS, start=1):
        assert abs(mensuel[cle] - indice) < 1e-12, (
            "{0} vaut {1!r} au lieu de {2} : le decoupage empiete sur un "
            "mois voisin".format(cle, mensuel[cle], indice)
        )


def test_les_sommes_mensuelles_partitionnent_exactement_la_serie():
    """La somme des douze mois doit egaler la somme de la serie, sans reste."""
    serie = _serie_par_mois(lambda m: m * 0.5)
    mensuel, total = adaptateur._agreger_mensuel_sommes(serie)
    assert abs(sum(mensuel.values()) - total) < 1e-6
    assert abs(total - sum(serie)) < 1e-6
    assert len(mensuel) == 12


def test_somme_mensuelle_ponderee_par_la_longueur_du_mois():
    """Une serie constante a 1,0 doit rendre 24 x nb_jours par mois."""
    serie = [1.0] * HEURES_PAR_AN
    mensuel, total = adaptateur._agreger_mensuel_sommes(serie)
    for indice, cle in enumerate(adaptateur.MOIS, start=1):
        attendu = calendar.monthrange(adaptateur.ANNEE_SIMULATION, indice)[1] * 24
        assert abs(mensuel[cle] - attendu) < 1e-9, "{0} : {1} h au lieu de {2}".format(
            cle, mensuel[cle], attendu
        )
    assert abs(total - HEURES_PAR_AN) < 1e-9


def test_les_deux_moyennes_annuelles_sont_distinctes_et_correctes():
    """Table 30 = moyenne des 12 mensuelles ; Table 32 = moyenne horaire.

    Les mois n'ont pas la meme longueur : confondre les deux introduit un biais
    systematique d'environ 0,04 K, invisible et plausible. Le classeur SIA les
    distingue (`B70 = AVERAGE(B58:B69)` pour la Table 30, agregat horaire pour
    la Table 32).
    """
    serie = _serie_par_mois(lambda m: m)
    _mensuel, moy_mensuelles, moy_horaire = adaptateur._agreger_mensuel_moyennes(serie)
    assert (
        abs(moy_mensuelles - 6.5) < 1e-12
    ), "La moyenne non ponderee des 12 mois vaut exactement 6,5"
    assert abs(moy_horaire - sum(serie) / len(serie)) < 1e-12
    assert abs(moy_horaire - moy_mensuelles) > 1e-3, (
        "Les deux agregations doivent differer sur une serie non constante ; "
        "si elles coincident, l une des deux est calculee comme l autre"
    )


def test_agregation_refuse_une_serie_incomplete():
    """Une annee tronquee doit lever, jamais etre completee en silence."""
    for longueur in (HEURES_PAR_AN - 1, HEURES_PAR_AN + 1, 0, 8784):
        with pytest.raises(ValueError):
            adaptateur._agreger_mensuel_moyennes([1.0] * longueur)
        with pytest.raises(ValueError):
            adaptateur._agreger_mensuel_sommes([1.0] * longueur)


# ==========================================================================
# 3. Lecture des series .aps -- avec un double du ResultsReader
# ==========================================================================


class FauxResultsReader(object):
    """Double minimal de `iesve.ResultsReader` (§6.1.14)."""

    def __init__(self, variables=None, serie=None):
        self._variables = variables if variables is not None else []
        self._serie = serie if serie is not None else []
        self.appels = []

    def get_variables(self):
        return self._variables

    def get_room_results(
        self, room_id, aps_varname, display_name, model_level, *args, **kwargs
    ):
        self.appels.append((room_id, aps_varname, display_name, model_level))
        return list(self._serie)


def _liaison_connue():
    cle = next(iter(adaptateur.LIAISONS_APS_CANDIDATES))
    return cle, adaptateur.LIAISONS_APS_CANDIDATES[cle]


def test_liaison_refusee_si_la_variable_est_absente_du_aps():
    """Ne jamais deviner une variable de remplacement."""
    cle, _liaison = _liaison_connue()
    lecteur = FauxResultsReader(
        variables=[{"aps_varname": "Une autre variable", "model_level": "z"}]
    )
    with pytest.raises(RuntimeError) as erreur:
        adaptateur._resoudre_liaison(lecteur, cle, adaptateur.LIAISONS_APS_CANDIDATES)
    assert "introuvable" in str(erreur.value).lower()


def test_liaison_exige_le_bon_niveau_de_modele():
    """Meme nom de variable mais mauvais niveau : refus.

    Le niveau discrimine une grandeur de zone d'une grandeur de surface ou de
    systeme. L'ignorer lierait une grandeur homonyme du mauvais objet.
    """
    cle, liaison = _liaison_connue()
    mauvais = "X" if liaison["model_level"] != "X" else "Y"
    lecteur = FauxResultsReader(
        variables=[{"aps_varname": liaison["aps_varname"], "model_level": mauvais}]
    )
    with pytest.raises(RuntimeError):
        adaptateur._resoudre_liaison(lecteur, cle, adaptateur.LIAISONS_APS_CANDIDATES)


def test_liaison_resolue_quand_la_variable_existe():
    cle, liaison = _liaison_connue()
    lecteur = FauxResultsReader(
        variables=[
            {"aps_varname": liaison["aps_varname"], "model_level": liaison["model_level"]}
        ]
    )
    assert (
        adaptateur._resoudre_liaison(lecteur, cle, adaptateur.LIAISONS_APS_CANDIDATES)
        is liaison
    )


def test_grandeur_sans_liaison_declaree_leve():
    lecteur = FauxResultsReader(variables=[])
    with pytest.raises(KeyError):
        adaptateur._resoudre_liaison(
            lecteur, "grandeur_inexistante", adaptateur.LIAISONS_APS_CANDIDATES
        )


def test_serie_horaire_passe_telle_quelle_a_pas_horaire():
    _cle, liaison = _liaison_connue()
    serie = [float(i % 7) for i in range(HEURES_PAR_AN)]
    lecteur = FauxResultsReader(serie=serie)
    horaire = adaptateur._lire_serie_horaire(lecteur, "R1", liaison, 24)
    assert len(horaire) == HEURES_PAR_AN
    assert horaire == serie


def test_serie_semi_horaire_est_moyennee_et_non_decimee():
    """Un pas de 30 min (48/jour) doit MOYENNER, pas prendre une valeur sur deux.

    C'est le defaut metrologique qui a ete rencontre en vrai : la simulation
    tournait a `results_per_hour = 2`. Deciner au lieu de moyenner donnerait une
    serie de bonne longueur et de mauvaise valeur.
    """
    _cle, liaison = _liaison_connue()
    serie = []
    for heure in range(HEURES_PAR_AN):
        serie.extend([float(heure), float(heure) + 2.0])  # moyenne = heure + 1
    lecteur = FauxResultsReader(serie=serie)
    horaire = adaptateur._lire_serie_horaire(lecteur, "R1", liaison, 48)
    assert len(horaire) == HEURES_PAR_AN
    assert abs(horaire[0] - 1.0) < 1e-12, "moyenne de 0 et 2"
    assert abs(horaire[10] - 11.0) < 1e-12, "moyenne de 10 et 12"
    assert abs(horaire[-1] - (HEURES_PAR_AN - 1 + 1.0)) < 1e-12


def test_pas_de_simulation_non_entier_est_refuse():
    """Un pas qui n'est pas un multiple entier de l'heure doit lever."""
    _cle, liaison = _liaison_connue()
    lecteur = FauxResultsReader(serie=[1.0] * (HEURES_PAR_AN * 3))
    for par_jour in (36, 10, 0):
        with pytest.raises(RuntimeError):
            adaptateur._lire_serie_horaire(lecteur, "R1", liaison, par_jour)


def test_serie_de_longueur_invalide_est_refusee():
    """Une annee incomplete ne doit jamais etre completee ni tronquee."""
    _cle, liaison = _liaison_connue()
    lecteur = FauxResultsReader(serie=[1.0] * (HEURES_PAR_AN - 24))
    with pytest.raises(RuntimeError):
        adaptateur._lire_serie_horaire(lecteur, "R1", liaison, 24)


def test_la_lecture_interroge_bien_le_local_demande():
    """Garde-fou contre une inversion d'arguments silencieuse."""
    _cle, liaison = _liaison_connue()
    lecteur = FauxResultsReader(serie=[0.0] * HEURES_PAR_AN)
    adaptateur._lire_serie_horaire(lecteur, "LOCAL-42", liaison, 24)
    room_id, aps_varname, _display, niveau = lecteur.appels[0]
    assert room_id == "LOCAL-42"
    assert aps_varname == liaison["aps_varname"]
    assert niveau == liaison["model_level"]
