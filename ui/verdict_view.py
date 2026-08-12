# -*- coding: utf-8 -*-
"""Transformation JSON -> structure d'affichage, Test SIA 4010 n° 1.

Python PUR : aucun `import iesve`, `tkinter`, `win32com` ou `reportlab`. C'est
la SEULE partie de `ui/` testable par `pytest` classique dans cet
environnement (docs/ADR-001-architecture-MSP.md §2 -- Tkinter/Pywin32/
ReportLab tournent uniquement dans VE ; voir `ui/dialog_tkinter.py`,
`ui/excel_export.py`, `ui/export_pdf_reportlab.py`, marqués
`# ⚠ À VÉRIFIER -- non exécuté` partout où ils dépendent de VE).

Style volontairement conservateur (pas de f-string, pas de `dataclasses`),
comme `engine/test1_engine.py` et `ve_adapter/test1_adapter.py` : ADR-001 §2
n'a PAS tranché la version de Python embarquée dans VEScripts au moment où ce
fichier est écrit. Rester compatible avec une éventuelle contrainte 3.4 ne
coûte rien ici.

--------------------------------------------------------------------------
RÈGLE DE FOND (CLAUDE.md, PROJECT_PLAN.md, docs/ADR-001 §D2, prompt
ui-engineer) : ce module NE RECALCULE RIEN. Il consomme UNIQUEMENT ce que
`engine/test1_engine.py::evaluer_test1(reference, candidat)` a déjà produit
et certifié :
  - aucune tolérance n'est réévaluée ici (le booléen `conforme` est lu tel
    quel dans le JSON du moteur, jamais recalculé à partir de bornes) ;
  - aucun article de norme n'est inventé : les citations ci-dessous
    reprennent mot pour mot celles déjà présentes dans les docstrings de
    `engine/test1_engine.py`, `ve_adapter/SCHEMA.md` et
    `traceability/test-1.spec.md` (voir `CITATIONS` plus bas, avec renvoi
    explicite à la source de chaque chaîne) ;
  - aucune valeur numérique n'est inventée : ce module ne fait que lire,
    trier et mettre en forme les clés déjà présentes dans
    `resultat_test1['cas'][...]['periodes'][...]`.

La seule chose que ce module « invente » est PUREMENT PRÉSENTATIONNELLE :
  - des libellés français lisibles pour les clés machine (`LIBELLES_GRANDEUR`)
    -- une traduction d'identifiant, pas une donnée métier ;
  - un ordre d'affichage des périodes (mois puis annuel, etc.) -- l'ordre des
    clés JSON n'étant pas garanti par `dict` ;
  - un mappage verdict -> couleur (vert/rouge/gris), imposé littéralement par
    CLAUDE.md ("Lisibilité du verdict") et repris ici sans varier :
      conforme is True  -> 'vert'
      conforme is False -> 'rouge'
      conforme is None  -> 'gris'   (jamais un faux vert par donnée manquante)
"""

import copy


# --------------------------------------------------------------------------
# Couleurs de verdict -- imposées par CLAUDE.md / .claude/agents/ui-engineer.md
# ("Lisibilité du verdict : vert / rouge / gris -- jamais de faux vert par
# donnée manquante"). Ne JAMAIS faire dépendre `gris` d'une valeur numérique :
# uniquement de `conforme is None`.
# --------------------------------------------------------------------------

COULEUR_CONFORME = 'vert'
COULEUR_NON_CONFORME = 'rouge'
COULEUR_NON_APPLICABLE = 'gris'

TEXTE_CONFORME = 'Conforme'
TEXTE_NON_CONFORME = 'Non conforme'
TEXTE_NON_APPLICABLE_INFORMATIF = 'Comparatif seulement -- aucun critère de déviation'
TEXTE_NON_APPLICABLE_MANQUANT = 'Non évalué -- candidat non fourni ou non simulé'


def couleur_depuis_conforme(conforme):
    """Mappe `conforme` (True/False/None) sur une couleur de verdict.

    Unique fonction de ce module qui décide d'une couleur : centralisée pour
    qu'aucun appelant (Tkinter, PDF, Excel) ne puisse dériver un « faux vert »
    par un autre chemin.
    """
    if conforme is True:
        return COULEUR_CONFORME
    if conforme is False:
        return COULEUR_NON_CONFORME
    return COULEUR_NON_APPLICABLE


# --------------------------------------------------------------------------
# Citations -- reprises MOT POUR MOT des sources déjà vérifiées par
# `norm-analyst`/`validation-engine-engineer`. Chaque constante indique sa
# source exacte en commentaire ; ce module ne relit ni ne revérifie la norme,
# il cite ce qui a déjà été cité ailleurs dans le dépôt.
# --------------------------------------------------------------------------

# Source : traceability/test-1.spec.md §2 ; SIA 4010:2023 §4.5, tab. 63 --
# repris à l'identique dans engine/test1_engine.py (constante
# CLASSES_REQUERANT_TEST1, commentaire de définition).
CITATION_CLASSES_CONCERNEES = (
    u'SIA 4010:2023, §4.5, tab. 63 (traceability/test-1.spec.md §2) -- '
    u'Test 1 requis dans toutes les classes de validation sauf la classe 5.'
)

# Source : Spezifikation_Test1.pdf, rubrique « Testkriterien », cité mot pour
# mot dans traceability/test-1.spec.md §6 et dans la docstring de
# engine/test1_engine.py::evaluer_periode_1e.
CITATION_CRITERE_1E = (
    u'Spezifikation_Test1.pdf, rubrique « Testkriterien » '
    u'(traceability/test-1.spec.md §6) : « Resultate für den Test 1E müssen '
    u'im Streubereich der enthaltenen Referenzprogramme liegen » -- seul '
    u'critère pass/fail du Test 1. Formule de la plage de dispersion '
    u'(Streubereich) établie par audit indépendant, PAS un simple min/max '
    u'(AUDIT.md, point 4 ; engine/test1_engine.py::calculer_plage_dispersion).'
)

# Source : Spezifikation_Test1.pdf, rubrique « Testkriterien », cité mot pour
# mot dans traceability/test-1.spec.md §6 et dans la docstring de
# engine/test1_engine.py::comparer_periode_informative.
CITATION_INFORMATIF = (
    u'Spezifikation_Test1.pdf, rubrique « Testkriterien » '
    u'(traceability/test-1.spec.md §6) : « Es gibt dafür kein '
    u'Abweichungskriterium » -- aucun critère de déviation pour ce cas. '
    u'Comparaison affichée à titre indicatif uniquement, jamais de verdict.'
)

# Source : SCHEMA.md §7 pt 5 ; AUDIT-swiss-sia-existant.md, élément n° 3 ;
# engine/test1_engine.py::_perioder_pointe (Table 31, « Test results Annual
# hourly integrated peak heating and cooling load », triplet Mittelwert/
# obere Grenze/untere Grenze en G/H/I, ligne d'en-tête L81).
CITATION_CRITERE_POINTE_1E = (
    u'Resultaterfassung_Test1.xlsx, Table 31 (« Annual hourly integrated peak '
    u'heating and cooling load »), ligne d’en-tête L81, colonnes G/H/I '
    u'(Mittelwert/obere Grenze/untere Grenze) -- troisième critère pass/fail '
    u'du cas 1E, cf. engine/test1_engine.py::_perioder_pointe.'
)

# Source de la valeur de référence elle-même (toutes grandeurs) : identique
# pour toutes les périodes du Test 1, cf. refs/reference-data/test-1.ref.json
# (clé racine `excel_source`) et AUDIT.md (verdict « GARDER -- SIGNÉ »,
# passe 3, 1336/1336 cellules concordantes).
SOURCE_VALEUR_REFERENCE = (
    u'refs/reference-data/test-1.ref.json, extrait de '
    u'SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx '
    u'(feuille « Zusammenfassung Testfälle »). Audit indépendant : '
    u'AUDIT.md, verdict « GARDER -- SIGNÉ » (passe 3, 2026-07-30, '
    u'1336/1336 cellules concordantes).'
)

CITATIONS_PAR_TYPE_CONTROLE = {
    'critere_pass_fail': CITATION_CRITERE_1E,
    'informatif': CITATION_INFORMATIF,
}


# --------------------------------------------------------------------------
# Libellés -- traduction d'identifiants machine en texte lisible. AUCUNE
# valeur numérique ou normative n'est introduite ici ; l'unité affichée est
# lue directement dans le suffixe du nom de la grandeur (`_kwh` / `_celsius`),
# pas revérifiée indépendamment (cf. réserve explicite ci-dessous pour
# `annual_hourly_peak_load_kwh`, dont l'intitulé Excel -- Table 31, « Annual
# hourly integrated peak ... load » -- pourrait désigner une PUISSANCE [kW]
# plutôt qu'une énergie [kWh] malgré le suffixe de la clé JSON : point
# ⚠ À VÉRIFIER avec `reference-data-engineer`/`norm-analyst`, non tranché ici,
# ce module se limite à refléter fidèlement le nom de clé fourni par le
# moteur, sans corriger ni deviner).
# --------------------------------------------------------------------------

LIBELLES_GRANDEUR = {
    'sensible_heating_demand_kwh': u'Besoins de chauffage sensible [kWh]',
    'sensible_cooling_demand_kwh': u'Besoins de refroidissement sensible [kWh]',
    'operative_temperature_monthly_celsius':
        u'Température opérative moyenne [°C]',
    'operative_temperature_annual_extremes_celsius':
        u'Température opérative -- extrêmes annuels [°C]',
    'annual_hourly_peak_load_kwh':
        u'Charge de pointe horaire annuelle chauffage/refroidissement '
        u'[kWh -- ⚠ à vérifier, Table 31 : peut-être une puissance kW]',
}


def libelle_grandeur(grandeur):
    """Retourne le libellé français d'une grandeur, ou -- à défaut d'entrée
    connue -- la clé brute précédée d'un avertissement visible plutôt que de
    masquer une grandeur non répertoriée ici (ex. future Table 3x)."""
    return LIBELLES_GRANDEUR.get(
        grandeur, u'⚠ Grandeur non répertoriée dans verdict_view.py : ' + grandeur)


# Ordre d'affichage des périodes. Ce ne sont pas des valeurs normatives : ce
# sont des clés structurelles déjà fixées par `engine/test1_engine.py`
# (MOIS, `_perioder_extremes`, `_perioder_pointe`) et `ve_adapter/SCHEMA.md`.
# Un ordre explicite est nécessaire car l'ordre d'itération d'un dict JSON
# n'est pas une garantie de present affichage stable.
_ORDRE_PERIODES = (
    'month_01', 'month_02', 'month_03', 'month_04', 'month_05', 'month_06',
    'month_07', 'month_08', 'month_09', 'month_10', 'month_11', 'month_12',
    'annual', 'max', 'min', 'average', 'heating', 'cooling',
)
_RANG_PERIODE = dict((cle, indice) for indice, cle in enumerate(_ORDRE_PERIODES))


def _rang_tri_periode(label):
    """Rang de tri d'une période connue ; les inconnues sont poussées en fin
    de liste (triées entre elles par ordre alphabétique), jamais masquées."""
    return (_RANG_PERIODE.get(label, len(_ORDRE_PERIODES)), label)


LIBELLES_PERIODE = {
    'month_01': u'Janvier', 'month_02': u'Février', 'month_03': u'Mars',
    'month_04': u'Avril', 'month_05': u'Mai', 'month_06': u'Juin',
    'month_07': u'Juillet', 'month_08': u'Août', 'month_09': u'Septembre',
    'month_10': u'Octobre', 'month_11': u'Novembre', 'month_12': u'Décembre',
    'annual': u'Annuel', 'max': u'Maximum annuel', 'min': u'Minimum annuel',
    'average': u'Moyenne annuelle', 'heating': u'Chauffage (pointe)',
    'cooling': u'Refroidissement (pointe)',
}


def libelle_periode(label):
    return LIBELLES_PERIODE.get(label, label)


# --------------------------------------------------------------------------
# Formattage numérique -- purement présentationnel (arrondi d'affichage),
# n'affecte jamais le verdict (déjà tranché par le moteur avant tolérance).
# --------------------------------------------------------------------------

def formater_nombre(valeur, decimales=2):
    """Formate un nombre pour affichage, ou '—' si absent (`None`).

    Ne JAMAIS afficher `0` ou une chaîne vide à la place d'une valeur
    manquante : `None` reste visuellement distinct (CLAUDE.md, "jamais de
    faux vert/valeur par donnée manquante").
    """
    if valeur is None:
        return u'—'
    gabarit = u'{0:.' + str(decimales) + u'f}'
    return gabarit.format(valeur)


# --------------------------------------------------------------------------
# Construction d'une ligne d'affichage par période.
# --------------------------------------------------------------------------

def construire_ligne_periode(grandeur, cas, type_controle, label_periode, verdict):
    """Transforme UNE période déjà évaluée par le moteur
    (`resultat_test1['cas'][cle]['periodes'][label]`) en une ligne
    d'affichage plate.

    `verdict` est lu tel quel (copie profonde défensive pour que l'appelant
    ne puisse pas muter accidentellement le JSON du moteur via la vue) ; ce
    module n'y ajoute que des clés de présentation (`*_affiche`, `couleur`,
    `article`, ...), il ne modifie ni ne recalcule aucune des clés d'origine.
    """
    verdict = copy.deepcopy(verdict)
    conforme = verdict.get('conforme')
    couleur = couleur_depuis_conforme(conforme)

    if type_controle == 'critere_pass_fail':
        if conforme is None:
            texte_verdict = verdict.get('motif') or TEXTE_NON_APPLICABLE_MANQUANT
        elif conforme is True:
            texte_verdict = TEXTE_CONFORME
        else:
            texte_verdict = TEXTE_NON_CONFORME
        # Citation spécifique : la Table 31 (pointe 1E) a son propre article,
        # distinct des Tables 28/29/30 (Streubereich mensuel/annuel usuel).
        if grandeur == 'annual_hourly_peak_load_kwh':
            article = CITATION_CRITERE_POINTE_1E
        else:
            article = CITATION_CRITERE_1E
    elif type_controle == 'informatif':
        texte_verdict = TEXTE_NON_APPLICABLE_INFORMATIF
        article = CITATION_INFORMATIF
    else:
        # Type de contrôle inconnu : ne jamais improviser un verdict --
        # afficher l'anomalie plutôt que la masquer.
        texte_verdict = u'⚠ type_controle inconnu : ' + str(type_controle)
        article = u'⚠ Aucune citation associée à ce type_controle.'

    ligne = {
        'grandeur': grandeur,
        'grandeur_libelle': libelle_grandeur(grandeur),
        'cas': cas,
        'type_controle': type_controle,
        'periode': label_periode,
        'periode_libelle': libelle_periode(label_periode),
        'conforme': conforme,
        'couleur': couleur,
        'texte_verdict': texte_verdict,
        'valeur_candidate': verdict.get('valeur_candidate'),
        'valeur_candidate_affichee': formater_nombre(verdict.get('valeur_candidate')),
        'article': article,
        'source_valeur_reference': SOURCE_VALEUR_REFERENCE,
        # Détail brut, non transformé, pour le drill-down (Tkinter) : contient
        # selon le type soit {moyenne_programmes, plage_min, plage_max,
        # marge_min, marge_max, coherence_reference}, soit {comparaisons}.
        'detail': verdict,
    }
    return ligne


def _cle_tri_ligne(ligne):
    """Ordre d'affichage stable : grandeur, puis cas, puis période."""
    return (ligne['grandeur'], ligne['cas'], _rang_tri_periode(ligne['periode']))


def construire_lignes_test1(resultat_test1):
    """Construit la liste plate de toutes les lignes d'affichage (grandeur ×
    cas × période) à partir du JSON complet de `evaluer_test1()`.

    Ne parcourt QUE les clés déjà produites par le moteur
    (`resultat_test1['cas']`) : une grandeur ou un cas absent du JSON du
    moteur est absent de la vue -- jamais complété par une valeur inventée.
    """
    lignes = []
    for bloc in resultat_test1.get('cas', {}).values():
        grandeur = bloc['grandeur']
        cas = bloc['cas']
        type_controle = bloc['type_controle']
        for label_periode, verdict in bloc.get('periodes', {}).items():
            lignes.append(construire_ligne_periode(
                grandeur, cas, type_controle, label_periode, verdict))
    lignes.sort(key=_cle_tri_ligne)
    return lignes


# --------------------------------------------------------------------------
# Verdict global du Test 1 (agrégat déjà calculé par le moteur -- lu tel
# quel, jamais recalculé).
# --------------------------------------------------------------------------

def construire_verdict_global(resultat_test1):
    """Transforme `resultat_test1['verdict_test1']` en ligne d'affichage.

    Ce dict est déjà l'agrégat produit par
    `engine/test1_engine.py::_verdict_global_1e` : ce module se contente de
    lui associer une couleur/un texte, comme pour une période individuelle.
    """
    verdict_test1 = resultat_test1.get('verdict_test1') or {
        'conforme': None, 'motif': u'verdict_test1 absent du JSON du moteur.'}
    conforme = verdict_test1.get('conforme')
    couleur = couleur_depuis_conforme(conforme)
    if conforme is True:
        texte = TEXTE_CONFORME + u' -- {0}/{0} périodes 1E dans la plage de dispersion'.format(
            verdict_test1.get('nb_periodes_totales'))
    elif conforme is False:
        nb_echecs = len(verdict_test1.get('echecs') or [])
        texte = TEXTE_NON_CONFORME + u' -- {0} période(s) 1E hors plage'.format(nb_echecs)
    else:
        texte = verdict_test1.get('motif') or (
            u'Non évalué -- {0} période(s) 1E non simulée(s) sur {1}'.format(
                verdict_test1.get('nb_periodes_non_evaluees'),
                verdict_test1.get('nb_periodes_totales')))
    return {
        'test_id': resultat_test1.get('test_id'),
        'conforme': conforme,
        'couleur': couleur,
        'texte': texte,
        'article': CITATION_CRITERE_1E,
        'detail': copy.deepcopy(verdict_test1),
    }


# --------------------------------------------------------------------------
# Vue « Classe de validation -> Test requis » (navigation de premier
# niveau). Limitée AUX classes déjà listées par le moteur
# (`resultat_test1['classes_concernees']`) : ce module ne connaît PAS la
# table 63 complète (tous tests × toutes classes) -- cette donnée n'existe
# pas encore comme JSON produit par un moteur (seul le Test 1 est implémenté
# à ce jour). Afficher la classe « 5 » comme "non applicable" nécessiterait
# de connaître, hors du JSON du moteur, la liste complète des classes SIA
# 4010 -- ce serait une valeur non tracée dans le contrat de ce module.
# ⚠ QUESTION OUVERTE (cf. rapport de fin de tâche) : le dialogue Tkinter
# devra, quand d'autres tests existeront, agréger plusieurs
# `resultat_testN['classes_concernees']` pour reconstituer la table 63 --
# non nécessaire tant qu'un seul test existe.
# --------------------------------------------------------------------------

def construire_lignes_classes(resultat_test1):
    """Une ligne par classe de validation concernée par le Test 1, chacune
    portant le verdict global du Test 1 (même valeur pour toutes les
    classes : le Test 1 n'a qu'un seul verdict, pas un verdict par classe)."""
    verdict_global = construire_verdict_global(resultat_test1)
    lignes = []
    for classe in resultat_test1.get('classes_concernees', []):
        lignes.append({
            'classe': classe,
            'test_id': resultat_test1.get('test_id'),
            'test_requis': True,
            'conforme': verdict_global['conforme'],
            'couleur': verdict_global['couleur'],
            'texte_verdict': verdict_global['texte'],
            'article': CITATION_CLASSES_CONCERNEES,
        })
    lignes.sort(key=lambda ligne: ligne['classe'])
    return lignes


# --------------------------------------------------------------------------
# Point d'entrée principal -- structure complète consommée par
# `ui/dialog_tkinter.py`, `ui/export_pdf_reportlab.py` et
# `ui/excel_export.py`.
# --------------------------------------------------------------------------

def construire_vue_test1(resultat_test1):
    """Assemble la structure d'affichage complète du Test 1.

    `resultat_test1` : JSON retourné par
    `engine/test1_engine.py::evaluer_test1(reference, candidat)`. Ce module
    ne l'exige pas conforme à un schéma figé au-delà des clés qu'il lit
    explicitement (`cas`, `verdict_test1`, `classes_concernees`, `test_id`) --
    une clé supplémentaire produite plus tard par le moteur (ex. futures
    Tables 3x) apparaît automatiquement dans `lignes` sans modification de ce
    module, tant qu'elle respecte la forme `{grandeur, cas, type_controle,
    periodes}` déjà utilisée par toutes les grandeurs actuelles.
    """
    return {
        'test_id': resultat_test1.get('test_id'),
        'numero_test': '1',
        'verdict_global': construire_verdict_global(resultat_test1),
        'classes': construire_lignes_classes(resultat_test1),
        'lignes': construire_lignes_test1(resultat_test1),
    }


# ==========================================================================
# TEST 7 -- classe de validation 5
# ==========================================================================
#
# Le Test 7 n'a ni cas ni périodes : c'est une liste plate de 11 grandeurs
# annuelles. Pour réutiliser l'arborescence du navigateur sans la réécrire, on
# le projette sur LE MÊME contrat de vue que le Test 1
# (`{test_id, verdict_global, classes, lignes}`), avec la correspondance :
#
#     grandeur  <- le GROUPE du classeur (Testgrössen / Diagnosegrössen)
#     cas       <- le libellé de la grandeur
#     periode   <- 'annual'
#
# ce qui donne dans l'arbre : Classe 5 -> Test 7 -> Testgrössen -> <grandeur>
# -> Annuel. Aucune donnée n'est ajoutée : `conforme` est lu tel quel dans le
# JSON du moteur, jamais recalculé à partir des bornes.
# --------------------------------------------------------------------------

# Source : SIA 4010:2023 §4.5, tab. 63 -- le Test 7 est exigé par 4A, 4B et 5.
CITATION_CLASSE_5 = (
    u'SIA 4010:2023, §4.5, tab. 63 -- la classe de validation 5 '
    u'(« calcul des besoins en énergie de refroidissement et de chauffage '
    u'pour les profils de besoins existants ») n\'exige que le Test 7.'
)
CITATION_CLASSE_4X = (
    u'SIA 4010:2023, §4.5, tab. 63 -- le Test 7 est l\'un des tests exigés '
    u'par cette classe (4A : tests 1, 2A, 3A à F, 4 à 7 ; 4B : tests 1 à 7). '
    u'Son succès est nécessaire mais NON suffisant : la classe reste non '
    u'validée tant que ses autres tests ne le sont pas.'
)


def _citation_classe_test7(classe):
    return CITATION_CLASSE_5 if classe == '5' else CITATION_CLASSE_4X

# Source : engine/test7_engine.py, constantes STATUT_CRITERE et
# JUSTIFICATION_CRITERE, elles-mêmes appuyées sur SIA 4010:2023 §4.4 et sur
# l'arbitrage traceability/critere-test4.spec.md.
CITATION_CRITERE_TEST7 = (
    u'La spécification du Test 7 n\'énonce aucun critère ; '
    u'SIA 4010:2023 §4.4 délègue la comparaison au classeur d\'évaluation, '
    u'qui porte des bandes sur les seules Testgrössen (lignes 8-20) et aucune '
    u'sur les Diagnosegrössen (21-26). Formule : moyenne ± MAX(ABS(programme '
    u'− moyenne)), bornes incluses. Le classeur corrigé reçu le 2026-08-10 '
    u'applique explicitement borne basse / borne haute ; contrôle XML et '
    u'checksum consignés dans la traçabilité.'
)

SOURCE_VALEUR_REFERENCE_TEST7 = (
    u'refs/reference-data/test-7.ref.json, extrait de '
    u'SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx '
    u'(feuille « Zusammenfassung », colonnes L/M/N). Les 11 bandes sont '
    u'recalculées par engine/scatter_band.py et confrontées au classeur '
    u'(scripts/build_test7_reference.py, tolérance 1e-6).'
)

TEXTE_INFORMATIF_TEST7 = u'Diagnosegrösse -- aucune bande au classeur'

_STATUTS_AVEC_RESERVE = ('PASS_WITH_RESERVATION',)


def _texte_verdict_test7(grandeur):
    """Texte de verdict d'une grandeur du Test 7, statut du moteur lu tel quel."""
    conforme = grandeur.get('conforme')
    statut = grandeur.get('statut')
    if conforme is True:
        if statut in _STATUTS_AVEC_RESERVE:
            return (TEXTE_CONFORME + u' -- sous réserve : hors enveloppe '
                    u'min/max des programmes, lecture concurrente non réfutée')
        return TEXTE_CONFORME
    if conforme is False:
        return TEXTE_NON_CONFORME + u' -- hors bande des programmes de référence'
    if grandeur.get('candidat') is None:
        return TEXTE_NON_APPLICABLE_MANQUANT
    return u'Non évalué -- ' + str(statut)


def _resumer_bande_test7(grandeur):
    """Résumé lisible de la bande : « moyenne (bas … haut) unité »."""
    unite = grandeur.get('unite') or u''
    return u'{0} ({1} … {2}) {3}'.format(
        formater_nombre(grandeur.get('moyenne'), 1),
        formater_nombre(grandeur.get('borne_basse'), 1),
        formater_nombre(grandeur.get('borne_haute'), 1),
        unite).strip()


def construire_lignes_test7(resultat_test7):
    """Une ligne d'affichage par grandeur du Test 7, dans l'ordre du classeur.

    L'ordre est celui de `resultat_test7['grandeurs']`, qui reprend l'ordre des
    lignes du classeur SIA -- pas un tri de notre invention.
    """
    lignes = []
    for grandeur in resultat_test7.get('grandeurs', []):
        conforme = grandeur.get('conforme')
        groupe = grandeur.get('groupe') or u'(groupe absent)'
        soumise = grandeur.get('borne_haute') is not None

        lignes.append({
            'grandeur': groupe,
            'grandeur_libelle': groupe,
            'cas': grandeur.get('libelle') or u'(sans libellé)',
            'type_controle': 'critere_pass_fail' if soumise else 'informatif',
            'periode': 'annual',
            'periode_libelle': libelle_periode('annual'),
            'conforme': conforme,
            'couleur': couleur_depuis_conforme(conforme),
            'texte_verdict': _texte_verdict_test7(grandeur),
            'valeur_candidate': grandeur.get('candidat'),
            'valeur_candidate_affichee': formater_nombre(grandeur.get('candidat'), 1),
            'reference_affichee': _resumer_bande_test7(grandeur),
            'article': CITATION_CRITERE_TEST7,
            'source_valeur_reference': SOURCE_VALEUR_REFERENCE_TEST7,
            'detail': copy.deepcopy(grandeur),
        })
    return lignes


def construire_verdict_global_test7(resultat_test7):
    """Verdict global du Test 7 -- agrégat déjà calculé par le moteur."""
    verdict = resultat_test7.get('verdict')
    nb_echecs = resultat_test7.get('nb_echecs', 0)
    nb_inconnues = resultat_test7.get('nb_non_evaluables', 0)
    nb_reserves = resultat_test7.get('nb_reserves', 0)
    soumises = resultat_test7.get('grandeurs_soumises_au_critere', 0)

    if verdict == 'FAIL':
        conforme = False
        texte = TEXTE_NON_CONFORME + u' -- {0} grandeur(s) hors bande'.format(nb_echecs)
    elif verdict in ('PASS', 'PASS_WITH_RESERVATION'):
        conforme = True
        texte = TEXTE_CONFORME + u' -- {0}/{0} grandeurs dans la bande'.format(soumises)
        if nb_reserves:
            texte += u' ({0} sous réserve)'.format(nb_reserves)
    else:
        conforme = None
        texte = (u'Non évalué -- {0} grandeur(s) non simulée(s) sur {1}'
                 .format(nb_inconnues, soumises))

    return {
        'test_id': u'Test 7',
        'conforme': conforme,
        'couleur': couleur_depuis_conforme(conforme),
        'texte': texte,
        'article': CITATION_CRITERE_TEST7,
        'detail': copy.deepcopy(resultat_test7.get('critere') or {}),
    }


def construire_lignes_classes_test7(resultat_test7):
    """Une ligne par classe concernée -- la classe 5 seule."""
    verdict_global = construire_verdict_global_test7(resultat_test7)
    lignes = []
    for classe in resultat_test7.get('classes_concernees', []):
        lignes.append({
            'classe': classe,
            'test_id': u'Test 7',
            'test_requis': True,
            'conforme': verdict_global['conforme'],
            'couleur': verdict_global['couleur'],
            'texte_verdict': verdict_global['texte'],
            'article': _citation_classe_test7(classe),
        })
    lignes.sort(key=lambda ligne: ligne['classe'])
    return lignes


def construire_vue_test7(resultat_test7):
    """Assemble la vue du Test 7, au même contrat que `construire_vue_test1`.

    `resultat_test7` : dict retourné par
    `engine/test7_engine.py::evaluer_test7(reference, candidat)`.
    """
    return {
        'test_id': u'Test 7',
        'numero_test': '7',
        'verdict_global': construire_verdict_global_test7(resultat_test7),
        'classes': construire_lignes_classes_test7(resultat_test7),
        'lignes': construire_lignes_test7(resultat_test7),
    }


# ==========================================================================
# TESTS 2 ET 3 -- références de forme « grandeur -> cas »
# ==========================================================================
#
# Même contrat de vue que les autres, avec la correspondance :
#
#     grandeur  <- le libellé de la grandeur du classeur
#     cas       <- le nom du cas (« Test 2 A », « Test 3 F »)
#     periode   <- 'annual'
#
# ce qui donne : Classe -> Test 2 -> <grandeur> -> <cas> -> Annuel.
# --------------------------------------------------------------------------

CITATION_CRITERE_BANDES = (
    u'Critère INFÉRÉ. La spécification de ce test n\'énonce aucun critère ; '
    u'SIA 4010:2023 §4.4 délègue la comparaison au classeur d\'évaluation, '
    u'qui porte les bandes. Formule : moyenne ± MAX(ABS(programme − moyenne)), '
    u'bornes incluses. À confirmer par la sous-commission (§4.6.2).'
)

TEXTE_VARIANTES = (
    u'Les colonnes du classeur sont des VARIANTES de programme, pas des '
    u'programmes : le SIA retient une variante par programme, et pas la même '
    u'd\'un programme à l\'autre. Le jeu contributeur est lu sur la formule.'
)


def _source_reference_bandes(numero_test):
    """Phrase de provenance d'une référence de test à bandes.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        str: Provenance, citée dans chaque ligne.
    """
    return (
        u'refs/reference-data/test-%s.ref.json, extrait de '
        u'Resultaterfassung_Test%s.xlsx (feuille « Zusammenfassung »). Chaque '
        u'bande est recalculée par engine/scatter_band.py et confrontée au '
        u'classeur (scripts/build_sia_reference.py, tolérance 1e-6).'
        % (numero_test, numero_test))


def _texte_verdict_bande(ligne):
    """Texte de verdict d'un cas, statut du moteur lu tel quel.

    Args:
        ligne: Ligne de résultat du moteur.

    Returns:
        str: Texte affichable.
    """
    conforme = ligne.get('conforme')
    if conforme is True:
        if ligne.get('statut') == 'PASS_WITH_RESERVATION':
            return (TEXTE_CONFORME + u' -- sous réserve : hors enveloppe '
                    u'min/max des programmes')
        return TEXTE_CONFORME
    if conforme is False:
        return TEXTE_NON_CONFORME + u' -- hors bande des programmes de référence'
    return TEXTE_NON_APPLICABLE_MANQUANT


def construire_vue_bandes(resultat):
    """Assemble la vue d'un test à bandes (2 ou 3).

    Args:
        resultat: Sortie d'`engine.sia_bandes_engine.evaluer`.

    Returns:
        dict: Vue au contrat commun `{test_id, numero_test, verdict_global,
        classes, lignes}`.
    """
    numero = u'%s' % resultat['test']
    source = _source_reference_bandes(numero)

    lignes = []
    for grandeur in resultat['grandeurs']:
        for cas in grandeur['cas']:
            conforme = cas.get('conforme')
            lignes.append({
                'grandeur': grandeur['libelle'],
                'grandeur_libelle': grandeur['libelle'],
                'cas': cas['cas'],
                'type_controle': 'critere_pass_fail',
                'periode': 'annual',
                'periode_libelle': libelle_periode('annual'),
                'conforme': conforme,
                'couleur': couleur_depuis_conforme(conforme),
                'texte_verdict': _texte_verdict_bande(cas),
                'valeur_candidate': cas['candidat'],
                'valeur_candidate_affichee': formater_nombre(cas['candidat'], 1),
                'reference_affichee': u'{0} ({1} … {2}) {3}'.format(
                    formater_nombre(cas['moyenne'], 1),
                    formater_nombre(cas['borne_basse'], 1),
                    formater_nombre(cas['borne_haute'], 1),
                    grandeur.get('unite') or u'').strip(),
                'article': CITATION_CRITERE_BANDES,
                'source_valeur_reference': source,
                'detail': copy.deepcopy(cas),
            })

    verdict = resultat['verdict']
    if verdict == 'FAIL':
        conforme_global = False
        texte = TEXTE_NON_CONFORME + u' -- {0} bande(s) dépassée(s)'.format(
            resultat['nb_echecs'])
    elif verdict in ('PASS', 'PASS_WITH_RESERVATION'):
        conforme_global = True
        texte = TEXTE_CONFORME + u' -- {0}/{0} bandes respectées'.format(
            resultat['nb_bandes'])
    else:
        conforme_global = None
        texte = u'Non évalué -- {0} bande(s) non simulée(s) sur {1}'.format(
            resultat['nb_non_evaluables'], resultat['nb_bandes'])

    verdict_global = {
        'test_id': u'Test ' + numero,
        'conforme': conforme_global,
        'couleur': couleur_depuis_conforme(conforme_global),
        'texte': texte,
        'article': CITATION_CRITERE_BANDES,
        'detail': copy.deepcopy(resultat.get('critere') or {}),
    }

    classes = [{
        'classe': classe,
        'test_id': u'Test ' + numero,
        'test_requis': True,
        'conforme': conforme_global,
        'couleur': verdict_global['couleur'],
        'texte_verdict': texte,
        'article': CITATION_TABLEAU_63,
    } for classe in sorted(resultat.get('classes_concernees', []))]

    return {
        'test_id': u'Test ' + numero,
        'numero_test': numero,
        'verdict_global': verdict_global,
        'classes': classes,
        'lignes': lignes,
        'note_variantes': TEXTE_VARIANTES,
    }


# ==========================================================================
# SYNTHÈSE PAR CLASSE DE VALIDATION -- tous tests confondus
# ==========================================================================
#
# C'est la seule vue qui réponde à la question du client : « quelles classes
# mon logiciel a-t-il ? ». Elle est donc aussi celle où un faux vert coûterait
# le plus cher.
#
# Règle appliquée sans exception : une classe n'est verte que si TOUS les
# tests que le tableau 63 lui impose sont présents ET verts. Un test absent du
# dossier rend la classe NON CONCLUANTE, jamais « verte sur ce qu'on a ».
# --------------------------------------------------------------------------

# SIA 4010:2023, §4.5, tableau 63 -- transcrit mot pour mot depuis
# refs/SIA-4010-2023.pdf p. 48, et repris dans
# traceability/classes-de-validation.spec.md §1.
TESTS_PAR_CLASSE = {
    '1A': ('1', '2A'),
    '1B': ('1', '2'),
    '2A': ('1', '2A', '3A-F'),
    '2B': ('1', '2', '3'),
    '3':  ('1', '4', '5', '6'),
    '4A': ('1', '2A', '3A-F', '4', '5', '6', '7'),
    '4B': ('1', '2', '3', '4', '5', '6', '7'),
    '5':  ('7',),
}

CITATION_TABLEAU_63 = (
    u'SIA 4010:2023, §4.5, tableau 63 — « Classes de validation ». '
    u'Colonne « Tests » transcrite verbatim.'
)

TEXTE_CLASSE_INCOMPLETE = (
    u'Non concluante — {0} test(s) exigé(s) sur {1} absent(s) du dossier : {2}'
)


# Un test couvert EN ENTIER couvre aussi ses sous-ensembles. Le tableau 63
# exige parfois « Test 2A », c'est-à-dire le Test 2 limité au cas 2A, et
# « Tests 3A à 3F », soit six des douze cas du Test 3. Disposer du test complet
# satisfait donc ces exigences ; l'ignorer laisserait des classes marquées
# incomplètes alors que tout ce qu'elles réclament est présent.
#
# L'inverse est FAUX et n'est pas encodé : couvrir 2A ne couvre pas le Test 2.
COUVERTURE_IMPLIQUEE = {
    '2': ('2A',),
    '3': ('3A-F',),
}


def _numero_test(une_vue):
    """Numéro de test d'une vue, ou `None` si elle ne le déclare pas."""
    return une_vue.get('numero_test')


def _numeros_couverts(numeros):
    """Étend un ensemble de numéros de test par les sous-ensembles impliqués.

    Args:
        numeros: Numéros de tests réellement présents.

    Returns:
        set[str]: Numéros couverts, sous-ensembles compris.
    """
    couverts = set(numeros)
    for numero in numeros:
        couverts.update(COUVERTURE_IMPLIQUEE.get(numero, ()))
    return couverts


def construire_synthese_classes(vues):
    """Une ligne par classe du tableau 63, tous tests confondus.

    `vues` : liste de vues (`construire_vue_test1`, `construire_vue_test7`, ...).

    Une classe est verte UNIQUEMENT si chacun des tests que le tableau 63 lui
    impose est présent dans `vues` ET conforme. Les tests manquants sont
    nommés : un lecteur doit pouvoir vérifier lui-même pourquoi une classe
    n'est pas acquise.
    """
    par_numero = {}
    for une_vue in vues:
        numero = _numero_test(une_vue)
        if numero is not None:
            par_numero[numero] = une_vue
    # Un test complet satisfait aussi les exigences portant sur ses
    # sous-ensembles : la vue du Test 2 vaut pour « Test 2A ».
    for numero in list(par_numero):
        for implique in COUVERTURE_IMPLIQUEE.get(numero, ()):
            par_numero.setdefault(implique, par_numero[numero])

    lignes = []
    for classe in sorted(TESTS_PAR_CLASSE):
        exiges = TESTS_PAR_CLASSE[classe]
        presents = [n for n in exiges if n in par_numero]
        manquants = [n for n in exiges if n not in par_numero]

        verdicts = [par_numero[n]['verdict_global'] for n in presents]
        couleurs = [v['couleur'] for v in verdicts]

        if manquants:
            # Un échec avéré doit rester visible même si d'autres tests
            # manquent : il est plus grave qu'une absence.
            conforme = False if COULEUR_NON_CONFORME in couleurs else None
            texte = TEXTE_CLASSE_INCOMPLETE.format(
                len(manquants), len(exiges),
                u', '.join(u'Test ' + n for n in manquants))
            if conforme is False:
                texte = TEXTE_NON_CONFORME + u' — ' + texte
        elif COULEUR_NON_CONFORME in couleurs:
            conforme = False
            texte = TEXTE_NON_CONFORME + u' — {0} test(s) en échec'.format(
                couleurs.count(COULEUR_NON_CONFORME))
        elif COULEUR_NON_APPLICABLE in couleurs:
            conforme = None
            texte = u'Non concluante — {0} test(s) non évalué(s)'.format(
                couleurs.count(COULEUR_NON_APPLICABLE))
        else:
            conforme = True
            texte = TEXTE_CONFORME + u' — {0}/{0} test(s) exigé(s) conforme(s)'.format(
                len(exiges))

        lignes.append({
            'classe': classe,
            'tests_exiges': list(exiges),
            'tests_couverts': presents,
            'tests_manquants': manquants,
            'conforme': conforme,
            'couleur': couleur_depuis_conforme(conforme),
            'texte_verdict': texte,
            'article': CITATION_TABLEAU_63,
        })
    return lignes
