# -*- coding: utf-8 -*-
"""Integrite des donnees de reference du Test SIA 4010 n^1.

Ce fichier transcrit en assertions executables l'audit manuel consigne dans
`AUDIT.md` (qa-auditor, 2026-07-30). Objectif : ne plus jamais depenser une passe
d'audit humaine sur ce fichier. Toute regeneration de
`refs/reference-data/test-1.ref.json` est re-auditee ici en moins d'une seconde.

Deux familles de controles :

* **Sans le classeur source** (toujours executes, y compris en CI ou les binaires
  de `SIA_4010_geteilter_Link/` sont absents) : coherence interne, forme des
  noeuds, garde-fous contre les defauts n^2 et n^3 d'`AUDIT.md`, et la formule du
  `Streubereich` du cas 1E.
* **Avec le classeur source** (ignores si absent, avec un motif explicite) :
  fidelite valeur<->cellule et correspondance libelle<->colonne contre les vraies
  lignes d'en-tete. C'est ce second bloc qui garde contre le defaut n^1
  (decalage de colonnes en Table 30).

ANGLE MORT CONNU (mesure par mutation, cf. ADR-001 §7bis) : sans le classeur
source, deux corruptions sur quatre passent inapercues — le decalage de colonnes
(defaut n^1) et la conversion silencieuse d'une erreur Excel en 0. La CI ne peut
donc pas, en l'etat, attraper la classe de bug qui s'est reellement produite. Le
correctif prevu est une empreinte de cellules brutes versionnee dans
`refs/reference-data/`. Ne pas confondre "CI verte" et "donnees auditees".

`openpyxl` n'est utilise que par les controles optionnels et reste une dependance
de developpement / CI (il est de toute facon present dans VE, en 3.1.2). Aucun
`import iesve` : c'est ce qui garde le moteur testable en CI sans licence VE.

Le style sans f-string est un reliquat : la version de Python de VEScripts a
depuis ete mesuree a **3.12.3** (VE 2025, sonde du 2026-07-31, ADR-001 §2).
Aucune contrainte de compatibilite ne s'applique plus ; ce fichier n'a simplement
pas besoin d'etre reecrit pour autant.
"""

import json
import os
import re

import pytest

try:
    import openpyxl
except ImportError:  # environnement sans dependance de test
    openpyxl = None


# --------------------------------------------------------------------------
# Localisation des fichiers
# --------------------------------------------------------------------------

_ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))

# Surchargeable pour les tests de mutation : on verifie que ces controles
# ECHOUENT bien sur un fichier volontairement corrompu (cf. docs/ADR-001 §7).
REF_JSON = os.environ.get(
    'SIA_REF_JSON',
    os.path.join(RACINE, 'refs', 'reference-data', 'test-1.ref.json'))

# Source brute figee. Volontairement hors depot (130 Mo pour les 7 classeurs) :
# les controles qui en dependent sont ignores plutot qu'echoues quand elle manque.
CLASSEUR = os.environ.get(
    'SIA_TEST1_XLSX',
    os.path.join(RACINE, 'SIA_4010_geteilter_Link', 'Test1',
                 'Resultaterfassung_Test1.xlsx'))
FEUILLE = u'Zusammenfassung Testf\xe4lle'  # « Zusammenfassung Testfälle »

# Empreinte des cellules brutes, versionnee (38 Ko) : substitut du classeur
# quand la source figee est absente, typiquement en CI. Generee par
# `scripts/build_cell_fingerprint.py`. Sans elle, la mesure par mutation montre
# que deux corruptions sur quatre passent inapercues (ADR-001 §7bis).
EMPREINTE = os.environ.get(
    'SIA_TEST1_CELLS',
    os.path.join(RACINE, 'refs', 'reference-data', 'test-1.cells.json'))


# --------------------------------------------------------------------------
# Structure attendue du classeur SIA
#
# Lignes d'en-tete et plages de lignes de donnees reconstruites contre la source
# et confirmees par l'audit independant (`AUDIT.md`, section "Ce qui a ete
# VERIFIE ET CONFIRME", pt 1). Ce ne sont PAS des suppositions : elles sont
# re-verifiees par `test_correspondance_libelle_colonne` des que le classeur est
# present.
# --------------------------------------------------------------------------

GRANDEURS = {
    'sensible_heating_demand_kwh': {
        'table': 28, 'ligne_entete': 15, 'lignes_donnees': (16, 28)},
    'sensible_cooling_demand_kwh': {
        'table': 29, 'ligne_entete': 36, 'lignes_donnees': (37, 49)},
    'operative_temperature_monthly_celsius': {
        'table': 30, 'ligne_entete': 57, 'lignes_donnees': (58, 70)},
    'operative_temperature_annual_extremes_celsius': {
        'table': 32, 'ligne_entete': 104, 'lignes_donnees': (105, 107)},
    # Table 31 : troisieme critere pass/fail du cas 1E (charges de pointe
    # horaires annuelles). Ajoutee en passe 4 apres l'audit du loader existant.
    'annual_hourly_peak_load_kwh': {
        'table': 31, 'ligne_entete': 81, 'lignes_donnees': (82, 83)},
}

# Libelle exact porte par l'en-tete de la colonne declaree, par champ.
# Releve sur la source (lignes 15 / 36 / 57 / 104) le 2026-07-30.
CHAMP_VERS_ENTETE = {
    'testprogramm': 'Testprogramm',
    'iso_52016_1_2017': 'Daten Norm EN ISO 52016-1',
    'ida_ice_5_0_beta_23': 'IDA ICE',
    'excel_sia_380_2': 'EXCEL SIA 380/2',
    'energyplus_openstudio_9_1_0': 'Energy+/OpenStudio',
    'tas_edsl_9_5_2': 'EDSL-Tas',
    'mean_of_programs': 'Mittelwert',
    'range_max': 'obere Grenze',
    'range_min': 'untere Grenze',
}

# Les noeuds de donnees nomment deux champs autrement que les metadonnees.
CHAMP_DONNEE_VERS_COLONNE = {
    'testprogramm_candidate': 'testprogramm',
    'iso_52016_1_2017_reference': 'iso_52016_1_2017',
}

# Les quatre programmes de reference qui fondent la plage de dispersion du cas 1E.
# Le cas 1E n'a pas de colonne ISO 52016-1 (en-tete C15 = 'IDA ICE'), cf. AUDIT.md pt 3.
PROGRAMMES_1E = (
    'ida_ice_5_0_beta_23',
    'excel_sia_380_2',
    'energyplus_openstudio_9_1_0',
    'tas_edsl_9_5_2',
)

# Nombre de couples {value, cell} mesure sur la passe 4 (2026-07-31 : 1336 en
# passe 3, + 16 pour la Table 31 = 2 lignes x 8 colonnes). Garde-fou contre une
# regeneration qui perdrait silencieusement des donnees.
CELLULES_MINIMUM = 1352

TOLERANCE = 1e-6

_MOTIF_CELLULE = re.compile(r'^([A-Z]{1,3})([0-9]{1,5})$')


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------

def _charger_reference():
    with open(REF_JSON, encoding='utf-8') as flux:
        return json.load(flux)


@pytest.fixture(scope='module')
def reference():
    if not os.path.exists(REF_JSON):
        pytest.fail('Donnees de reference absentes : ' + REF_JSON)
    return _charger_reference()


class _SourceClasseur(object):
    """Acces direct au classeur officiel : la verite de premiere main."""

    origine = 'classeur officiel'

    def __init__(self, feuille):
        self._feuille = feuille

    def valeur(self, coordonnee):
        return self._feuille[coordonnee].value

    def entete(self, ligne, colonne):
        return self._feuille[colonne + str(ligne)].value


class _SourceEmpreinte(object):
    """Acces aux cellules brutes figees : substitut quand le classeur manque.

    Ne connait que les cellules citees par le JSON de reference et les lignes
    d'en-tete. Une adresse inconnue leve, plutot que de rendre `None` — sinon un
    controle passerait pour cause d'ignorance.
    """

    origine = 'empreinte figee'

    def __init__(self, donnees):
        self._cellules = donnees['cells']
        self._entetes = donnees['header_rows']

    def valeur(self, coordonnee):
        if coordonnee not in self._cellules:
            raise KeyError(
                'Cellule ' + coordonnee + " absente de l'empreinte. Relancer "
                'scripts/build_cell_fingerprint.py apres regeneration du JSON.')
        return self._cellules[coordonnee]

    def entete(self, ligne, colonne):
        return self._entetes.get(str(ligne), {}).get(colonne)


@pytest.fixture(scope='module')
def source():
    """Source des cellules brutes : le classeur s'il est la, sinon l'empreinte.

    Quand les deux sont presents, l'empreinte est verifiee CONTRE le classeur :
    elle ne peut donc pas deriver en silence et devenir un faux temoin.
    """
    empreinte = None
    if os.path.exists(EMPREINTE):
        with open(EMPREINTE, encoding='utf-8') as flux:
            empreinte = json.load(flux)

    if openpyxl is not None and os.path.exists(CLASSEUR):
        classeur = openpyxl.load_workbook(CLASSEUR, data_only=True)
        feuille = classeur[FEUILLE]
        reelle = _SourceClasseur(feuille)
        if empreinte is not None:
            derives = []
            for coordonnee, figee in empreinte['cells'].items():
                vraie = feuille[coordonnee].value
                if isinstance(figee, (int, float)) and isinstance(vraie, (int, float)):
                    if abs(float(vraie) - float(figee)) > 1e-9:
                        derives.append(coordonnee + ' : empreinte ' + repr(figee)
                                       + ', classeur ' + repr(vraie))
                elif figee != vraie:
                    derives.append(coordonnee + ' : empreinte ' + repr(figee)
                                   + ', classeur ' + repr(vraie))
            assert not derives, (
                "L'empreinte a derive du classeur ({0} cellule(s)) — relancer "
                'scripts/build_cell_fingerprint.py :\n{1}'.format(
                    len(derives), '\n'.join(derives[:10])))
        return reelle

    if empreinte is not None:
        return _SourceEmpreinte(empreinte)

    pytest.skip(
        'Ni le classeur officiel (' + CLASSEUR + ") ni l'empreinte (" + EMPREINTE
        + ') ne sont disponibles : la fidelite valeur<->cellule et la '
        'correspondance libelle<->colonne ne sont PAS verifiees.')


def _est_feuille_valeur(noeud):
    return isinstance(noeud, dict) and 'value' in noeud and 'cell' in noeud


def _decouper_cellule(ref):
    trouve = _MOTIF_CELLULE.match(ref)
    assert trouve is not None, 'Reference de cellule invalide : ' + repr(ref)
    return trouve.group(1), int(trouve.group(2))


def _iterer_enregistrements(noeud, chemin=''):
    """Rend les (chemin, enregistrement).

    Un *enregistrement* est un dict dont toutes les valeurs utiles sont des
    feuilles {value, cell} : une ligne du tableau SIA (un mois, une annee, un
    extreme). `_metadata` est ignore.
    """
    if not isinstance(noeud, dict):
        return
    utiles = dict((cle, val) for cle, val in noeud.items() if cle != '_metadata')
    if utiles and all(_est_feuille_valeur(val) for val in utiles.values()):
        yield chemin, utiles
        return
    for cle, val in utiles.items():
        for item in _iterer_enregistrements(val, chemin + '/' + cle):
            yield item


def _iterer_feuilles(reference):
    for grandeur, cas_tous in reference['reference_values'].items():
        for cas, noeud in cas_tous.items():
            for chemin, enreg in _iterer_enregistrements(noeud):
                for champ, feuille_valeur in enreg.items():
                    yield grandeur, cas, chemin, champ, feuille_valeur


def _proche(gauche, droite, tolerance=TOLERANCE):
    return abs(gauche - droite) <= tolerance


def _colonnes_declarees(noeud_cas):
    return noeud_cas.get('_metadata', {}).get('columns', {})


# --------------------------------------------------------------------------
# 1. Controles structurels — sans le classeur source
# --------------------------------------------------------------------------

def test_grandeurs_attendues_presentes(reference):
    """Les quatre tables auditees sont la. Une disparition doit casser le build."""
    presentes = set(reference['reference_values'].keys())
    attendues = set(GRANDEURS.keys())
    manquantes = attendues - presentes
    assert not manquantes, 'Grandeurs absentes du JSON : ' + repr(sorted(manquantes))


def test_forme_des_feuilles_de_valeur(reference):
    """Chaque feuille porte une valeur, une unite et une reference de cellule valide."""
    fautifs = []
    for grandeur, cas, chemin, champ, feuille_valeur in _iterer_feuilles(reference):
        localisation = '/'.join([grandeur, cas, chemin.strip('/'), champ])
        if 'unit' not in feuille_valeur:
            fautifs.append(localisation + ' : unite absente')
        valeur = feuille_valeur['value']
        if valeur is not None and not isinstance(valeur, (int, float)):
            fautifs.append(localisation + ' : valeur non numerique ' + repr(valeur))
        _decouper_cellule(feuille_valeur['cell'])
    assert not fautifs, 'Feuilles mal formees :\n' + '\n'.join(fautifs)


def test_volume_de_donnees_non_regresse(reference):
    """Une regeneration ne doit pas perdre de cellules en silence."""
    total = sum(1 for _ in _iterer_feuilles(reference))
    assert total >= CELLULES_MINIMUM, (
        'Regression de volume : {0} cellules extraites contre {1} auditees le '
        '2026-07-30. Si la reduction est deliberee, mettre a jour '
        'CELLULES_MINIMUM en le justifiant.'.format(total, CELLULES_MINIMUM))


def test_valeurs_nulles_documentees(reference):
    """Une valeur nulle vient d'une cellule d'erreur Excel : elle doit porter une note.

    AUDIT.md pt 7 : aucune erreur Excel ne doit etre silencieusement convertie en 0.
    Une note obligatoire rend la conversion silencieuse impossible a cacher.
    """
    sans_note = []
    for grandeur, cas, chemin, champ, feuille_valeur in _iterer_feuilles(reference):
        if feuille_valeur['value'] is None and not feuille_valeur.get('note'):
            sans_note.append('/'.join([grandeur, cas, chemin.strip('/'), champ])
                             + ' (' + feuille_valeur['cell'] + ')')
    assert not sans_note, (
        'Valeurs nulles sans note explicative :\n' + '\n'.join(sans_note))


def test_enregistrement_sur_une_seule_ligne(reference):
    """Toutes les cellules d'un enregistrement partagent la meme ligne Excel.

    Garde-fou contre un decalage de lignes : un mois ne peut pas melanger des
    valeurs prises sur deux lignes differentes.
    """
    fautifs = []
    for grandeur, cas_tous in reference['reference_values'].items():
        for cas, noeud in cas_tous.items():
            for chemin, enreg in _iterer_enregistrements(noeud):
                lignes = set(_decouper_cellule(f['cell'])[1] for f in enreg.values())
                if len(lignes) != 1:
                    fautifs.append('{0}/{1}{2} : lignes {3}'.format(
                        grandeur, cas, chemin, sorted(lignes)))
    assert not fautifs, 'Enregistrements a cheval sur plusieurs lignes :\n' + \
        '\n'.join(fautifs)


def test_lignes_dans_la_plage_de_leur_table(reference):
    """Les cellules citees tombent dans la plage de donnees de la table concernee."""
    fautifs = []
    for grandeur, cas_tous in reference['reference_values'].items():
        if grandeur not in GRANDEURS:
            continue
        debut, fin = GRANDEURS[grandeur]['lignes_donnees']
        for cas, noeud in cas_tous.items():
            for chemin, enreg in _iterer_enregistrements(noeud):
                for champ, feuille_valeur in enreg.items():
                    _, ligne = _decouper_cellule(feuille_valeur['cell'])
                    if not (debut <= ligne <= fin):
                        fautifs.append('{0}/{1}{2}/{3} : {4} hors plage {5}-{6}'.format(
                            grandeur, cas, chemin, champ,
                            feuille_valeur['cell'], debut, fin))
    assert not fautifs, 'Cellules hors de la plage de leur table :\n' + \
        '\n'.join(fautifs)


def test_colonnes_des_donnees_conformes_aux_metadonnees(reference):
    """La colonne de chaque cellule correspond a la colonne declaree pour son champ.

    Premiere moitie du garde-fou contre le DEFAUT n^1 d'`AUDIT.md` : le JSON ne
    doit pas se contredire lui-meme. La seconde moitie (le libelle reel de la
    colonne) exige le classeur, cf. `test_correspondance_libelle_colonne`.
    """
    fautifs = []
    for grandeur, cas_tous in reference['reference_values'].items():
        for cas, noeud in cas_tous.items():
            declarees = _colonnes_declarees(noeud)
            if not declarees:
                fautifs.append(grandeur + '/' + cas + ' : aucune colonne declaree')
                continue
            for chemin, enreg in _iterer_enregistrements(noeud):
                for champ, feuille_valeur in enreg.items():
                    cle = CHAMP_DONNEE_VERS_COLONNE.get(champ, champ)
                    if cle not in declarees:
                        fautifs.append('{0}/{1}{2} : champ {3} non declare dans '
                                       '_metadata.columns'.format(
                                           grandeur, cas, chemin, champ))
                        continue
                    colonne, _ = _decouper_cellule(feuille_valeur['cell'])
                    if colonne != declarees[cle]:
                        fautifs.append(
                            '{0}/{1}{2}/{3} : cellule en colonne {4} mais '
                            '_metadata declare {5}'.format(
                                grandeur, cas, chemin, champ,
                                colonne, declarees[cle]))
    assert not fautifs, ('Incoherences colonne donnee <-> metadonnees :\n' +
                         '\n'.join(fautifs))


def test_table_32_ne_contient_que_les_cas_flottement_libre(reference):
    """Garde-fou contre le DEFAUT n^2 d'`AUDIT.md`.

    La Table 32 (extremes annuels de temperature operative, zone compacte
    lignes 105-107) ne contient que deux blocs : 600FF (B-G) et 900FF (J-O).
    Les entrees '600' et '640' etaient des doublons mal etiquetes. Preuve
    physique : un maximum de 63.5 degres et un minimum de -16.9 n'appartiennent
    qu'a un cas en flottement libre.
    """
    cas = set(reference['reference_values'][
        'operative_temperature_annual_extremes_celsius'].keys())
    assert cas == {'600FF', '900FF'}, (
        "Table 32 doit contenir exactement {'600FF', '900FF'} ; trouve " +
        repr(sorted(cas)) + ". Les cas chauffes/refroidis ne figurent pas dans "
        "cette table (cf. AUDIT.md defaut n^2).")


def test_donnees_manquantes_ne_contredisent_pas_le_contenu(reference):
    """Garde-fou contre le DEFAUT n^3 d'`AUDIT.md`.

    `data_missing` ne doit pas declarer manquante une table pourtant extraite.
    """
    extraites = set(reference['extraction_completeness']['tables_extracted'])
    contradictions = []
    for cle, texte in reference.get('data_missing', {}).items():
        numeros = set(int(n) for n in re.findall(r'\d{2}', cle + ' ' + str(texte)))
        recouvrement = numeros & extraites
        if recouvrement:
            contradictions.append('data_missing[' + cle + '] mentionne la/les '
                                  'table(s) ' + repr(sorted(recouvrement)) +
                                  ' pourtant listee(s) comme extraite(s)')
    assert not contradictions, '\n'.join(contradictions)


def test_cas_declares_correspondent_au_contenu(reference):
    """`extraction_completeness.cases_covered` doit refleter les cas reellement la."""
    declares = set(reference['extraction_completeness']['cases_covered'])
    reels = set()
    for cas_tous in reference['reference_values'].values():
        reels |= set(cas_tous.keys())
    fantomes = declares - reels
    non_declares = reels - declares
    assert not fantomes, 'Cas declares mais absents : ' + repr(sorted(fantomes))
    assert not non_declares, 'Cas presents mais non declares : ' + \
        repr(sorted(non_declares))


# --------------------------------------------------------------------------
# 2. Critere pass/fail du cas 1E — la seule regle de verdict du Test 1
#
# `Spezifikation_Test1.pdf`, section Testkriterien : seul le cas 1E porte un
# critere d'acceptation (plage de dispersion). Les cas 600/640/900/940/600FF/900FF
# n'en ont aucun (cf. traceability/test-1.spec.md §6).
# --------------------------------------------------------------------------

def _enregistrements_1e(reference, grandeur):
    noeud = reference['reference_values'][grandeur]['1E']
    return list(_iterer_enregistrements(noeud))


def test_1e_moyenne_est_la_moyenne_arithmetique(reference):
    """`Mittelwert` = moyenne arithmetique des 4 programmes de reference."""
    verifies = 0
    for grandeur in ('sensible_heating_demand_kwh', 'sensible_cooling_demand_kwh'):
        for chemin, enreg in _enregistrements_1e(reference, grandeur):
            valeurs = [enreg[p]['value'] for p in PROGRAMMES_1E]
            if any(v is None for v in valeurs):
                continue
            attendue = sum(valeurs) / float(len(valeurs))
            obtenue = enreg['mean_of_programs']['value']
            assert _proche(obtenue, attendue), (
                '{0}/1E{1} : Mittelwert {2} != moyenne des programmes {3}'.format(
                    grandeur, chemin, obtenue, attendue))
            verifies += 1
    assert verifies >= 26, ('Seulement {0} periodes verifiees ; 26 attendues '
                            '(12 mois + annuel, chaud + froid).'.format(verifies))


def test_1e_plage_de_dispersion(reference):
    """`obere/untere Grenze` = bande symetrique autour de la moyenne, plancher a 0.

    CORRECTION D'UNE IDEE RECUE, etablie par l'audit (AUDIT.md pt 4) : le
    `Streubereich` n'est PAS le min/max des programmes. La formule reelle du
    classeur est

        ecart_max = max |programme - moyenne|
        range_max = moyenne + ecart_max
        range_min = max(0, moyenne - ecart_max)

    Verifiee 26/26. Ce test existe pour que le moteur n'implemente jamais la
    version fausse : c'est lui qui definit le critere pass/fail du cas 1E.
    """
    verifies = 0
    for grandeur in ('sensible_heating_demand_kwh', 'sensible_cooling_demand_kwh'):
        for chemin, enreg in _enregistrements_1e(reference, grandeur):
            valeurs = [enreg[p]['value'] for p in PROGRAMMES_1E]
            if any(v is None for v in valeurs):
                continue
            moyenne = sum(valeurs) / float(len(valeurs))
            ecart_max = max(abs(v - moyenne) for v in valeurs)
            attendu_max = moyenne + ecart_max
            attendu_min = max(0.0, moyenne - ecart_max)
            obtenu_max = enreg['range_max']['value']
            obtenu_min = enreg['range_min']['value']
            assert _proche(obtenu_max, attendu_max), (
                '{0}/1E{1} : obere Grenze {2} != {3}'.format(
                    grandeur, chemin, obtenu_max, attendu_max))
            assert _proche(obtenu_min, attendu_min), (
                '{0}/1E{1} : untere Grenze {2} != {3}'.format(
                    grandeur, chemin, obtenu_min, attendu_min))
            verifies += 1
    assert verifies >= 26, ('Seulement {0} periodes verifiees ; 26 attendues.'
                            .format(verifies))


def test_1e_moyenne_dans_sa_propre_plage(reference):
    """Coherence physique : la moyenne tombe toujours dans la plage de dispersion."""
    for grandeur in ('sensible_heating_demand_kwh', 'sensible_cooling_demand_kwh'):
        for chemin, enreg in _enregistrements_1e(reference, grandeur):
            moyenne = enreg['mean_of_programs']['value']
            borne_min = enreg['range_min']['value']
            borne_max = enreg['range_max']['value']
            if None in (moyenne, borne_min, borne_max):
                continue
            assert borne_min - TOLERANCE <= moyenne <= borne_max + TOLERANCE, (
                '{0}/1E{1} : moyenne {2} hors de [{3}, {4}]'.format(
                    grandeur, chemin, moyenne, borne_min, borne_max))


# --------------------------------------------------------------------------
# 3. Controles contre la source figee — ignores si le classeur est absent
# --------------------------------------------------------------------------

def test_fidelite_valeur_cellule(reference, source):
    """Chaque valeur stockee est exactement celle de la cellule Excel citee.

    C'est le controle central de l'audit : 1336/1336 concordances le 2026-07-30.
    Une valeur nulle doit correspondre a une cellule non numerique (erreur Excel
    du type #DIV/0! ou #REF!), jamais a un zero invente.
    """
    divergences = []
    total = 0
    for grandeur, cas, chemin, champ, feuille_valeur in _iterer_feuilles(reference):
        total += 1
        attendue = feuille_valeur['value']
        localisation = '/'.join([grandeur, cas, chemin.strip('/'), champ]) + \
            ' (' + feuille_valeur['cell'] + ')'
        try:
            obtenue = source.valeur(feuille_valeur['cell'])
        except KeyError:
            # Cellule inconnue de l'empreinte : soit le JSON cite une cellule
            # qu'il ne citait pas (decalage de colonnes), soit l'empreinte n'a
            # pas ete regeneree. Les deux doivent echouer, pas passer.
            divergences.append(localisation + " : cellule absente de la source "
                               "(" + source.origine + ")")
            continue
        if attendue is None:
            if isinstance(obtenue, (int, float)):
                divergences.append(localisation + ' : JSON null mais la cellule '
                                   'porte le nombre ' + repr(obtenue))
        elif not isinstance(obtenue, (int, float)):
            divergences.append(localisation + ' : JSON ' + repr(attendue) +
                               ' mais la cellule porte ' + repr(obtenue))
        elif not _proche(float(obtenue), float(attendue)):
            divergences.append(localisation + ' : JSON ' + repr(attendue) +
                               ' != Excel ' + repr(obtenue))
    assert not divergences, ('{0} divergence(s) sur {1} cellules :\n{2}'.format(
        len(divergences), total, '\n'.join(divergences[:40])))


def test_correspondance_libelle_colonne(reference, source):
    """Chaque colonne declaree porte bien, dans l'en-tete reel, le libelle revendique.

    Seconde moitie du garde-fou contre le DEFAUT n^1 d'`AUDIT.md` : c'est
    exactement ce controle qui avait revele 286 incoherences en Table 30 pour les
    cas 600/640/900/940 (donnees decalees d'une colonne, EDSL-Tas perdu).
    """
    divergences = []
    for grandeur, cas_tous in reference['reference_values'].items():
        if grandeur not in GRANDEURS:
            continue
        ligne_entete = GRANDEURS[grandeur]['ligne_entete']
        for cas, noeud in cas_tous.items():
            for champ, colonne in _colonnes_declarees(noeud).items():
                if champ not in CHAMP_VERS_ENTETE:
                    divergences.append('{0}/{1} : champ inconnu {2}'.format(
                        grandeur, cas, champ))
                    continue
                attendu = CHAMP_VERS_ENTETE[champ]
                cellule = colonne + str(ligne_entete)
                obtenu = source.entete(ligne_entete, colonne)
                if obtenu is None or str(obtenu).strip() != attendu:
                    divergences.append(
                        '{0}/{1}/{2} : colonne {3}, en-tete {4} = {5!r} '
                        'au lieu de {6!r}'.format(grandeur, cas, champ, colonne,
                                                  cellule, obtenu, attendu))
    assert not divergences, ('{0} incoherence(s) libelle <-> colonne :\n{1}'.format(
        len(divergences), '\n'.join(divergences[:40])))


def test_source_declaree_est_la_source_utilisee(reference, source):
    """La feuille citee dans le JSON est celle qui a reellement ete lue."""
    declaree = reference['excel_source']['sheet']
    assert declaree == FEUILLE, (
        'Le JSON declare la feuille ' + repr(declaree) + ' mais les controles '
        'portent sur ' + repr(FEUILLE))


def test_empreinte_couvre_toutes_les_cellules_citees(reference):
    """L'empreinte doit suivre le JSON, sinon la CI redevient aveugle.

    Une regeneration du JSON qui cite de nouvelles cellules sans regenerer
    l'empreinte laisserait ces cellules non verifiees en CI. On l'interdit
    explicitement plutot que de le decouvrir plus tard.
    """
    if not os.path.exists(EMPREINTE):
        pytest.skip('Empreinte absente : ' + EMPREINTE)
    with open(EMPREINTE, encoding='utf-8') as flux:
        empreinte = json.load(flux)
    citees = set(f['cell'] for _g, _c, _p, _ch, f in _iterer_feuilles(reference))
    manquantes = citees - set(empreinte['cells'])
    assert not manquantes, (
        '{0} cellule(s) citees par le JSON mais absentes de l empreinte. '
        'Relancer scripts/build_cell_fingerprint.py. Exemples : {1}'.format(
            len(manquantes), sorted(manquantes)[:10]))
