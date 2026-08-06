# -*- coding: utf-8 -*-
u"""Fige en JSON les référentiels transmis par le SIA le 2026-08-04.

SOURCES (captures d'écran fournies par Yiqiao Yang, SIA, 2026-08-04) :
  - SIA 2024:2021, tableau 11 (p. 54-55) — valeurs de dimensionnement
  - SIA 2024:2021, annexe B (normative), tableau 13 (p. 58-59)
  - SIA 180:2014, chiffre 2.3.1 — exigences de confort
  - SIA 180:2014, chiffre 2.3.2 et figure 4 — plage de température ressentie
  - SIA 387/4:2017, tableau 9 et chiffre 3.4.3.5 — commande de stores à lamelles

Ces captures « reflètent les versions publiées à l'origine et peuvent ne pas
inclure les rectificatifs ultérieurs » (Yiqiao Yang, 2026-08-04). Des
rectificatifs EXISTENT pour SIA 2024 et SIA 180 → cf. champ `corrigenda` de
chaque fichier produit. **Aucune valeur de ce script n'est confirmée
post-rectificatif.**

Le script ne se contente pas de recopier : il VÉRIFIE la règle de décalage des
courbes de consigne de SIA 380/2:2022 §5.2.2.5 contre les sept décalages
énumérés par SIA 4010:2023 §3.1.4. Si un seul ne se reproduit pas, il échoue.
"""

from __future__ import print_function

import io
import json
import os

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data')

# --------------------------------------------------------------------------
# SIA 2024:2021, tableau 11 — « Auslegungswerte für Heizungs-, Kälte- und
# lufttechnische Anlagen », p. 54-55.
#
# Colonnes, dans l'ordre du tableau :
#   0 theta_h  Raumtemperatur-Auslegungswert, Heizfall (Auslegung Norm-Heizlast), °C
#   1 theta_c  Raumtemperatur-Auslegungswert, Kühlfall (Auslegung Klimakälteleistung), °C
#   2 hr_h     Relative Raumluftfeuchte, Heizfall (Auslegung Befeuchtung), %
#   3 hr_c     Relative Raumluftfeuchte, Kühlfall (Auslegung Entfeuchtung), %
#   4 va_hyg   Hygienebedingter Aussenluft-Volumenstrom, m3/h par personne (jour)
#   5 va_nuit  idem, exploitation de nuit à débit réduit (valeur entre parenthèses)
#   6 va_proc  Prozessbedingter Aussenluft-Volumenstrom, m3/(h.m2)
#   7 notes    renvois de bas de tableau
#
# `None` = « – » (nicht relevant) dans le tableau.
# --------------------------------------------------------------------------
TABLEAU_11 = [
    (u'1.01', u'Wohnen MFH',                  21, 26,   30, 60, 29,   15,   None, [1, 2]),
    (u'1.02', u'Wohnen EFH',                  21, 26,   30, 60, 29,   15,   None, [1, 2]),
    (u'2.01', u'Hotelzimmer',                 21, 26,   30, 60, 29,   15,   None, [1]),
    (u'2.02', u'Empfang, Lobby',              21, 26,   30, 60, 29,   None, None, []),
    (u'3.01', u'Einzel-, Gruppenbüro',        21, 26,   30, 60, 29,   None, None, []),
    (u'3.02', u'Grossraumbüro',               21, 26,   30, 60, 29,   None, None, []),
    (u'3.03', u'Sitzungszimmer',              21, 26,   30, 60, 29,   None, None, []),
    (u'3.04', u'Schalterhalle, Empfang',      20, 26,   30, 60, 29,   None, None, []),
    (u'4.01', u'Schulzimmer',                 21, 26,   30, 60, 29,   None, None, []),
    (u'4.02', u'Lehrerzimmer, Aufenthaltsraum', 21, 26, 30, 60, 29,   None, None, []),
    (u'4.03', u'Bibliothek',                  21, 26,   30, 60, 29,   None, None, []),
    (u'4.04', u'Hörsaal',                     21, 26,   30, 60, 29,   None, None, []),
    (u'4.05', u'Schulfachraum',               21, 26,   30, 60, 29,   None, None, []),
    (u'5.01', u'Lebensmittelverkauf',         20, 26,   30, 60, 29,   None, None, []),
    (u'5.02', u'Fachgeschäft',                20, 26,   30, 60, 29,   None, None, []),
    (u'5.03', u'Verkauf Möbel, Bau, Garten',  20, 26,   30, 60, 29,   None, None, []),
    (u'6.01', u'Restaurant',                  21, 26,   30, 70, 29,   None, None, []),
    (u'6.02', u'Selbstbedienungsrestaurant',  21, 26,   30, 70, 29,   None, None, []),
    (u'6.03', u'Küche zu 6.1',                20, 28, None, None, 48, None, 80,   [3]),
    (u'6.04', u'Küche zu 6.2',                20, 28, None, None, 48, None, 80,   [3]),
    (u'7.01', u'Vorstellungsraum',            21, 26,   30, 60, 29,   None, None, []),
    (u'7.02', u'Mehrzweckhalle',              21, 26,   30, 60, 29,   None, None, []),
    (u'7.03', u'Ausstellungshalle',           21, 26,   30, 60, 29,   None, None, []),
    (u'8.01', u'Bettenzimmer',                22, 26,   30, 60, 29,   None, None, []),
    (u'8.02', u'Stationszimmer',              21, 26,   30, 60, 29,   None, None, []),
    (u'8.03', u'Behandlungsraum',             22, 26,   30, 60, 29,   None, None, []),
    (u'9.01', u'Produktion (grobe Arbeit)',   18, 30,   30, 70, 48,   None, 10,   []),
    (u'9.02', u'Produktion (feine Arbeit)',   21, 26,   30, 70, 29,   None, 5,    []),
    (u'9.03', u'Laborraum',                   21, 26,   30, 70, 29,   None, 12,   []),
    (u'10.01', u'Lagerraum',                  18, None, 30, 70, 29,   None, None, []),
    (u'11.01', u'Turnhalle',                  18, None, 30, 70, 73,   None, None, []),
    (u'11.02', u'Fitnessraum',                21, 26,   30, 70, 73,   None, None, []),
    (u'11.03', u'Schwimmhalle',               24, None, 55, 65, 29,   None, 20,   [4, 5]),
    (u'12.01', u'Verkehrsfläche',             21, None, None, None, None, None, None, []),
    (u'12.02', u'Verkehrsfläche 24 h',        21, 26, None, None, None, None, None, []),
    (u'12.03', u'Treppenhaus',                18, None, None, None, None, None, None, []),
    (u'12.04', u'Nebenraum',                  18, None, None, None, None, None, None, []),
    (u'12.05', u'Küche, Teeküche',            21, None, None, None, 29,   None, None, []),
    (u'12.06', u'WC, Bad, Dusche',            21, None, None, None, None, None, None, [6]),
    (u'12.07', u'WC',                         21, None, None, None, None, None, None, []),
    (u'12.08', u'Garderobe, Dusche',          21, None, None, None, None, None, None, [6]),
    (u'12.09', u'Parkhaus',                 None, None, None, None, None, None, 2,  [8]),
    (u'12.10', u'Wasch- und Trockenraum',   None, None, None, None, None, None, None, []),
    (u'12.11', u'Kühlraum',                 None, None, None, None, None, None, None, []),
    (u'12.12', u'Serverraum',               None, 26,   None, None, None, None, None, []),
]

NOTES_TABLEAU_11 = {
    1: u"Angabe gilt für Tagbetrieb; Angabe in Klammern gilt für den Nachtbetrieb "
       u"mit reduziertem Aussenluft-Volumenstrom",
    2: u"Massgebend für die Auslegung raumlufttechnischer Anlagen in Wohngebäuden "
       u"ist SIA 382/5",
    3: u"Massgebend für die Auslegung raumlufttechnischer Anlagen in "
       u"Gastwirtschaftsbetrieben ist SWKI VA102-01:2009",
    4: u"Mindestens Wassertemperatur, maximal 32 °C",
    5: u"Massgebend für die Auslegung raumlufttechnischer Anlagen in Hallenbädern "
       u"ist SWKI 2004-1:2005",
    6: u"Die Angabe gilt, sofern die angrenzende Hauptnutzung keine höheren "
       u"Raumtemperaturen für die Auslegung der Heizsysteme vorschreibt",
    7: u"Entspricht der Kategorie der Raumluftqualität II; «unterstützende "
       u"Fensterlüftung» bedeutet, dass bei Bedarf der Aussenluft-Volumenstrom über "
       u"eine Lüftungsöffnung kurzzeitig erhöht werden kann",
    8: u"Massgebend für die Auslegung von Lüftungsanlagen in Parkhäusern ist "
       u"SWKI VA103-01:2017",
}

# --------------------------------------------------------------------------
# SIA 2024:2021, annexe B (NORMATIVE), tableau 13 — « Mittlere Raumtemperaturen
# für die Berechnung des jährlichen Klimakälte- und Heizwärmebedarfs », p. 58-59.
# (usage, theta_h_moy, theta_c_moy)
# --------------------------------------------------------------------------
TABLEAU_13 = [
    (u'1.01', 22, 25), (u'1.02', 22, 25), (u'2.01', 22, 25), (u'2.02', 22, 25),
    (u'3.01', 22, 25), (u'3.02', 22, 25), (u'3.03', 22, 25), (u'3.04', 22, 25),
    (u'4.01', 22, 25), (u'4.02', 22, 25), (u'4.03', 22, 25), (u'4.04', 22, 25),
    (u'4.05', 22, 25), (u'5.01', 22, 25), (u'5.02', 22, 25), (u'5.03', 22, 25),
    (u'6.01', 22, 25), (u'6.02', 22, 25), (u'6.03', 22, 25), (u'6.04', 22, 25),
    (u'7.01', 22, 25), (u'7.02', 22, 25), (u'7.03', 22, 25),
    (u'8.01', 22, 25), (u'8.02', 22, 25), (u'8.03', 22, 25),
    (u'9.01', 20, 25), (u'9.02', 20, 25), (u'9.03', 20, 25),
    (u'10.01', 18, None),
    (u'11.01', 18, None), (u'11.02', 22, 25), (u'11.03', 28, None),
    (u'12.01', 22, None), (u'12.02', 22, 25), (u'12.03', 20, None),
    (u'12.04', 20, None), (u'12.05', 22, None), (u'12.06', 22, None),
    (u'12.07', 22, None), (u'12.08', 22, None),
    (u'12.09', None, None), (u'12.10', None, None), (u'12.11', None, None),
    (u'12.12', None, 25),
]

# --------------------------------------------------------------------------
# CONTRÔLE — la règle de décalage de SIA 380/2:2022 §5.2.2.5 :
#   « les limites seront décalées suivant la différence entre les valeurs de
#     dimensionnement de l'utilisation correspondante et les utilisations
#     1.01 à 3.03 selon SIA 2024:2021, tableau 11 »
# confrontée aux sept décalages CHIFFRÉS de SIA 4010:2023 §3.1.4 (p. 10).
# --------------------------------------------------------------------------
GROUPE_REFERENCE = [u'1.01', u'1.02', u'2.01', u'2.02', u'3.01', u'3.02', u'3.03']

# (usage, décalage attendu de la courbe INFÉRIEURE, vers le bas, en K)
DECALAGES_4010_INFERIEURE = [
    (u'3.04', 1), (u'5.01', 1), (u'5.02', 1), (u'5.03', 1),
    (u'6.03', 1), (u'6.04', 1), (u'9.01', 3),
]
# (usage, décalage attendu de la courbe SUPÉRIEURE, vers le haut, en K)
DECALAGES_4010_SUPERIEURE = [
    (u'6.03', 2), (u'6.04', 2), (u'9.01', 4),
]


def _par_usage():
    return dict((l[0], l) for l in TABLEAU_11)


def verifier_regle_de_decalage():
    u"""Reproduit les sept décalages de SIA 4010 §3.1.4 à partir du tableau 11.

    Lève `AssertionError` au premier écart : ce contrôle est la seule preuve
    que notre transcription du tableau 11 est bonne ET que notre lecture de la
    règle de §5.2.2.5 est bonne.
    """
    t11 = _par_usage()

    # Le groupe de référence doit être unanime, sans quoi « la différence avec
    # les utilisations 1.01 à 3.03 » n'aurait pas de sens comme scalaire.
    th = set(t11[u][2] for u in GROUPE_REFERENCE)
    tc = set(t11[u][3] for u in GROUPE_REFERENCE)
    assert th == set([21]), u'groupe de référence non unanime en chauffage : %r' % th
    assert tc == set([26]), u'groupe de référence non unanime en refroidissement : %r' % tc
    ref_h, ref_c = 21, 26

    controles = []
    for usage, attendu in DECALAGES_4010_INFERIEURE:
        calcule = ref_h - t11[usage][2]
        assert calcule == attendu, (
            u'décalage inférieur %s : SIA 4010 annonce %d K, '
            u'le tableau 11 donne %d K' % (usage, attendu, calcule))
        controles.append((u'inférieure', usage, attendu, calcule))

    for usage, attendu in DECALAGES_4010_SUPERIEURE:
        calcule = t11[usage][3] - ref_c
        assert calcule == attendu, (
            u'décalage supérieur %s : SIA 4010 annonce %d K, '
            u'le tableau 11 donne %d K' % (usage, attendu, calcule))
        controles.append((u'supérieure', usage, attendu, calcule))

    return controles


def construire_sia2024():
    lignes_11 = []
    for (usage, libelle, th, tc, hrh, hrc, vah, van, vap, notes) in TABLEAU_11:
        lignes_11.append({
            u'usage': usage,
            u'libelle_de': libelle,
            u'theta_h_design_c': th,
            u'theta_c_design_c': tc,
            u'humidite_relative_h_pct': hrh,
            u'humidite_relative_c_pct': hrc,
            u'air_neuf_hygiene_m3_h_pers': vah,
            u'air_neuf_hygiene_nuit_m3_h_pers': van,
            u'air_neuf_process_m3_h_m2': vap,
            u'renvois': notes,
        })
    lignes_13 = [{u'usage': u, u'theta_h_moyenne_c': h, u'theta_c_moyenne_c': c}
                 for (u, h, c) in TABLEAU_13]

    return {
        u'norme': u'SIA 2024:2021',
        u'titre': u"Données d'utilisation des locaux pour l'énergie et les "
                  u"installations du bâtiment",
        u'statut': u'FIGÉ — sous réserve des rectificatifs (cf. corrigenda)',
        u'date_extraction': u'2026-08-04',
        u'source': {
            u'nature': u"captures d'écran des pages du document publié",
            u'fournisseur': u'Yiqiao Yang, SIA',
            u'date_reception': u'2026-08-04',
            u'pages': [54, 55, 58, 59],
            u'reserve_du_fournisseur':
                u"« they reflect the originally published versions of the "
                u"standards/merkblätter and may not include any subsequent "
                u"corrigenda »",
        },
        u'corrigenda': {
            u'existent': True,
            u'source_declaree': u'Yiqiao Yang, SIA, 2026-08-04 : '
                                u'« corrigenda are available for SIA 2024 and SIA 180 »',
            u'gratuits': True,
            u'ou': u'SIA Shop',
            u'controle_effectue': False,
            u'consequence': u'⚠ À VÉRIFIER — aucune valeur de ce fichier n\'est '
                            u'confirmée post-rectificatif.',
        },
        u'tableau_11': {
            u'titre_de': u'Auslegungswerte für Heizungs-, Kälte- und '
                         u'lufttechnische Anlagen',
            u'pages': [54, 55],
            u'niveau_de_valeur': {
                u'distingue_standard_ziel_grenz': False,
                u'constat': u"Le tableau 11 ne comporte QU'UNE colonne par "
                            u"grandeur : aucune distinction Standardwert / "
                            u"Zielwert / Grenzwert. La température ambiante de "
                            u"dimensionnement ne dépend donc PAS du niveau de "
                            u"valeur demandé par une spécification de test.",
                u'portee': u"Ferme la seconde moitié du point ouvert O1 de "
                           u"traceability/batiment-exemple-zonage.spec.md §8.3.",
            },
            u'unites': {
                u'theta_h_design_c': u'°C — Auslegung Norm-Heizlast',
                u'theta_c_design_c': u'°C — Auslegung Klimakälteleistung',
                u'humidite_relative_h_pct': u'% — Auslegung Befeuchtung',
                u'humidite_relative_c_pct': u'% — Auslegung Entfeuchtung',
                u'air_neuf_hygiene_m3_h_pers': u'm3/h par personne, exploitation de jour',
                u'air_neuf_hygiene_nuit_m3_h_pers':
                    u'm3/h par personne, exploitation de nuit à débit réduit '
                    u'(valeur entre parenthèses au tableau) — renvoi 1',
                u'air_neuf_process_m3_h_m2': u'm3/(h.m2)',
            },
            u'convention_null': u'null = « – » (nicht relevant) au tableau',
            u'renvois': dict((str(k), v) for k, v in NOTES_TABLEAU_11.items()),
            u'lignes': lignes_11,
        },
        u'tableau_13': {
            u'titre_de': u'Mittlere Raumtemperaturen für die Berechnung des '
                         u'jährlichen Klimakälte- und Heizwärmebedarfs gemäss SIA 2024',
            u'annexe': u'B (normative)',
            u'pages': [58, 59],
            u'avertissement_de_lannexe':
                u"« Die angegebenen mittleren Raumtemperaturen gelten nur in "
                u"SIA 2024 und sind für andere Normen, insbesondere für "
                u"SIA 380/1, nicht massgebend. »",
            u'lecture_de_lavertissement':
                u"L'exclusion nomme SIA 380/**1**, pas SIA 380/2. Et SIA 380/2:2022 "
                u"§5.2.2.6 autorise EXPLICITEMENT cette voie simplifiée « surtout "
                u"dans les phases de planification précoce ». Pas de contradiction : "
                u"pour SIA 380/2 la voie normale reste la figure 1.",
            u'convention_null': u'null = « – » (nicht relevant) au tableau',
            u'lignes': lignes_13,
        },
        u'usages_requis_par_les_tests_sia_4010': {
            u'commentaire': u'Usages cités par les spécifications des tests 4, 5 et 6 '
                            u'et par la documentation du bâtiment exemple.',
            u'test_4': [u'4.04'],
            u'test_5': [u'3.01', u'3.02', u'3.03'],
            u'test_6': [u'6.02', u'6.04'],
        },
        u'ce_qui_reste_manquant': [
            u"Les FICHES D'UTILISATION (Merkblatt-Nutzungsdaten) 3.1, 3.2, 3.3, "
            u"4.4, 6.2, 6.4 : apports internes (personnes, appareils, éclairage), "
            u"horaires, simultanéités, surface par personne. NON contenues dans "
            u"les tableaux 11 et 13. Disponibles GRATUITEMENT en ligne — cf. "
            u"champ `fiches_utilisation_en_ligne`.",
            u"Les niveaux Standardwert / Zielwert / Grenzwert de ces fiches "
            u"(le test 4 demande les Zielwerte, les tests 5 et 6 les Standardwerte).",
        ],
        u'fiches_utilisation_en_ligne': {
            u'url': u'https://www.sia.ch/de/cms/dienstleistungen/'
                    u'normenundordnungen?item=15143#15152',
            u'gratuit': True,
            u'source': u'Yiqiao Yang, SIA, 2026-08-04',
            u'note_du_fournisseur':
                u"« The data sheet is updated and includes all changes regarding "
                u"data sheet in the two corrigenda of SIA 2024. » → la version en "
                u"ligne des FICHES est post-rectificatif ; les tableaux 11 et 13 "
                u"ci-dessus ne le sont pas.",
            u'telecharge': False,
        },
    }


def construire_sia180():
    return {
        u'norme': u'SIA 180:2014',
        u'titre': u"Protection thermique, protection contre l'humidité et climat "
                  u"intérieur dans les bâtiments",
        u'statut': u'FIGÉ — sous réserve des rectificatifs',
        u'date_extraction': u'2026-08-04',
        u'source': {
            u'nature': u"captures d'écran du document publié",
            u'fournisseur': u'Yiqiao Yang, SIA',
            u'date_reception': u'2026-08-04',
            u'chiffres': [u'2.3.1', u'2.3.2 (avec figure 4)'],
        },
        u'corrigenda': {
            u'existent': True,
            u'source_declaree': u'Yiqiao Yang, SIA, 2026-08-04',
            u'gratuits': True,
            u'ou': u'SIA Shop',
            u'controle_effectue': False,
        },
        u'chiffre_2_3_1': {
            u'titre_de': u'Anforderungen an Räume, während diese beheizt, '
                         u'gekühlt oder mechanisch belüftet sind — Allgemein',
            u'renvoi': u'Ces conditions correspondent pour l\'essentiel à la '
                       u'CATÉGORIE B de SN EN ISO 7730, annexe A.',
            u'portee': u"À respecter pendant TOUTE la durée d'utilisation "
                       u"(« während der ganzen Nutzungszeit »).",
            u'criteres': [
                {u'grandeur': u'PPD',
                 u'libelle_de': u'erwarteter Anteil mit der thermischen '
                                u'Behaglichkeit unzufriedener Personen',
                 u'operateur': u'<', u'valeur': 10, u'unite': u'%'},
                {u'grandeur': u'PMV',
                 u'libelle_de': u'erwartete durchschnittliche Bewertung der '
                                u'thermischen Behaglichkeit',
                 u'operateur': u'dans', u'valeur': [-0.5, 0.5], u'unite': u'-'},
                {u'grandeur': u'insatisfaits_courant_dair_ventilation_naturelle',
                 u'libelle_de': u'prozentualer Anteil zusätzlicher Unzufriedener '
                                u'wegen Zugluft, natürliche Lüftung',
                 u'operateur': u'<', u'valeur': 20, u'unite': u'%'},
                {u'grandeur': u'insatisfaits_courant_dair_ventilation_mecanique',
                 u'libelle_de': u'prozentualer Anteil zusätzlicher Unzufriedener '
                                u'wegen Zugluft, mechanische Lüftung',
                 u'operateur': u'<', u'valeur': 15, u'unite': u'%'},
                {u'grandeur': u'insatisfaits_gradient_tete_chevilles',
                 u'libelle_de': u'prozentualer Anteil zusätzlicher Unzufriedener '
                                u'wegen Temperaturdifferenz zwischen Kopf und Knöcheln',
                 u'operateur': u'<', u'valeur': 5, u'unite': u'%'},
                {u'grandeur': u'insatisfaits_temperature_du_sol',
                 u'libelle_de': u'prozentualer Anteil zusätzlicher Unzufriedener '
                                u'wegen Fussbodentemperatur',
                 u'operateur': u'<', u'valeur': 10, u'unite': u'%'},
                {u'grandeur': u'insatisfaits_asymetrie_de_rayonnement',
                 u'libelle_de': u'prozentualer Anteil zusätzlicher Unzufriedener '
                                u'wegen Asymmetrie der Strahlungstemperatur',
                 u'operateur': u'<', u'valeur': 5, u'unite': u'%'},
            ],
        },
        u'chiffre_2_3_2_figure_4': {
            u'titre_de': u'Zulässiger Bereich der empfundenen Temperatur in Wohn- '
                         u'und Büroräumen, während diese beheizt, gekühlt oder '
                         u'mechanisch belüftet sind, je nach gleitendem Mittelwert '
                         u'der Aussentemperatur',
            u'grandeur_ordonnee': u'empfundene Temperatur (température ressentie), °C',
            u'grandeur_abscisse': u'gleitender Mittelwert der Aussentemperatur über '
                                  u'48 Stunden, °C',
            u'condition_prealable': u'Avec la variation saisonnière de l\'habillement '
                                    u'selon la figure 2 (§2.3.2).',
            u'domaine_dapplication': u'locaux d\'habitation et bureaux '
                                     u'(Wohn- und Büroräume)',
            u'identite_avec_sia_380_2': {
                u'etablie': True,
                u'citation': u'SIA 380/2:2022 §5.2.2.5 : « La limite supérieure et '
                             u'la limite inférieure de la figure 1 découlent des '
                             u'exigences de SIA 180:2014, chiffre 2.3.1. Elles '
                             u'CORRESPONDENT À CELLES DE SIA 180:2014, FIGURE 4, '
                             u'pour les locaux d\'habitation et les bureaux. »',
                u'consequence': u'Les sommets ci-dessous ne sont PAS lus à l\'œil sur '
                                u'la capture : ils sont extraits du dessin VECTORIEL '
                                u'de la figure 1 de refs/SIA-380-2-2022.pdf p. 27 '
                                u'(résidu < 0,001 °C), puis confrontés à la capture '
                                u'de la figure 4. Concordance sur les 8 valeurs.',
                u'fichier': u'sia-380-2-2022.figure1.json',
            },
        },
    }


def construire_sia387_4():
    return {
        u'norme': u'SIA 387/4:2017',
        u'titre': u"Éclairage — Calcul et exigences (partie protection solaire)",
        u'statut': u'FIGÉ pour l\'édition 2017 — ⚠ ÉDITION DIVERGENTE, cf. '
                   u'`reserve_dedition`',
        u'date_extraction': u'2026-08-04',
        u'source': {
            u'nature': u"captures d'écran du document publié",
            u'fournisseur': u'Yiqiao Yang, SIA',
            u'date_reception': u'2026-08-04',
            u'elements': [u'chiffre 3.4.3.5', u'tableau 9'],
        },
        u'reserve_dedition': {
            u'edition_recue': u'SIA 387/4:2017',
            u'edition_citee_par_les_normes': u'SIA 387/4:2023',
            u'citation': u'SIA 4010:2023 §3.1.5 (p. 10) : « les commandes de '
                         u'protection solaire de type X = 1 ou 2 selon le '
                         u'tableau 9 de SIA 387/4:2023 »',
            u'indice_de_stabilite': u"La TYPOLOGIE X = 1 / 2 / 3 et le NUMÉRO de "
                                    u"tableau (9) concordent entre l'édition 2017 "
                                    u"reçue et la citation 2023 de SIA 4010. "
                                    u"Présomption de stabilité, PAS une preuve.",
            u'statut': u'⚠ À VÉRIFIER — les équations (18), (19), (20) de '
                       u'l\'édition 2023 ne sont pas en notre possession.',
        },
        u'tableau_9': {
            u'titre_de': u'Berechnung des Lamellen-Anstellwinkels für die drei '
                         u'Funktionstypen der Sonnenschutzsteuerung',
            u'grandeur_calculee': u'beta — Lamellen-Anstellwinkel (angle '
                                  u'd\'inclinaison des lamelles), en degrés',
            u'symbole_hauteur_solaire': u'delta_s_n — hauteur solaire',
            u'types': [
                {
                    u'x': 1,
                    u'type_sia_411': 1,
                    u'libelle_de': u'Motorbetrieben mit manueller Betätigung',
                    u'description_de': u'Die Lamellen gehen in Arbeitsposition 45° '
                                       u'und werden mehr geschlossen, wenn '
                                       u'Direktstrahlung eindringen würde. Sie werden '
                                       u'nicht mehr zurückgestellt, wenn sie mehr '
                                       u'geschlossen sind.',
                    u'equation_numero': 18,
                    u'formule': u'beta = max(45 ; 90 - 2*delta_s_n ; beta_{h-1})',
                    u'a_memoire': True,
                    u'symbole_memoire': u'beta_{h-1} = Lamellen-Anstellwinkel der '
                                        u'vorangehenden Stunde',
                },
                {
                    u'x': 2,
                    u'type_sia_411': 2,
                    u'libelle_de': u'Motorbetrieben mit automatischer Steuerung '
                                   u'(mit oder ohne Berücksichtigung der Verschattung)',
                    u'description_de': u'Die Lamellen gehen in Arbeitsposition 45° '
                                       u'und werden mehr geschlossen, wenn '
                                       u'Direktstrahlung eindringen würde.',
                    u'equation_numero': 19,
                    u'formule': u'beta = max(45 ; 90 - 2*delta_s_n)',
                    u'a_memoire': False,
                },
                {
                    u'x': 3,
                    u'type_sia_411': 3,
                    u'libelle_de': u'Motorbetrieben mit automatischer Steuerung '
                                   u'und Lamellennachführung',
                    u'description_de': u'Die Lamellen gehen in die optimale Position, '
                                       u'so dass keine Direktstrahlung eindringt.',
                    u'equation_numero': 20,
                    u'formule': u'beta = max(0 ; min(90 ; 90 - 2*delta_s_n))',
                    u'a_memoire': False,
                },
            ],
        },
        u'chiffre_3_4_3_5': {
            u'enonce_de': u'Bei Lamellenstoren sind tau_v_sp_B = tau_v_B_45, '
                          u'rho_v_sp_B = rho_v_B_45 sowie tau_v_sp_D = tau_v_D_45 '
                          u'und rho_v_sp_D = rho_v_B_D einzusetzen.',
            u'symboles': {
                u'tau_v_B_45': u'Lichttransmissionsgrad des Sonnenschutzes für '
                               u'direkte Strahlung in Arbeitsstellung (45°) bei '
                               u'Sonnenhöhe 45° gemäss SN EN 14500',
                u'rho_v_B_45': u'Lichtreflexionsgrad, direkte Strahlung, '
                               u'Arbeitsstellung 45°, Sonnenhöhe 45°, SN EN 14500',
                u'tau_v_D_45': u'Lichttransmissionsgrad, diffuse Strahlung, '
                               u'Arbeitsstellung 45°, Sonnenhöhe 45°, SN EN 14500',
                u'rho_v_D_45': u'Lichtreflexionsgrad, diffuse Strahlung, '
                               u'Arbeitsstellung 45°, Sonnenhöhe 45°, SN EN 14500',
            },
            u'source_des_valeurs': u'Herstellerangaben. À défaut, les valeurs du '
                                   u'TABLEAU 8 selon le type de protection solaire '
                                   u'du §3.3.2.9.',
            u'tableau_8_en_notre_possession': False,
            u'anomalie_de_lenonce': u"L'énoncé imprimé écrit "
                                    u"« rho_v_sp_D = rho_v_B_D » alors que la liste "
                                    u"de symboles définit rho_v_D_45 et non "
                                    u"rho_v_B_D. Coquille probable pour "
                                    u"rho_v_sp_D = rho_v_D_45. ⚠ À VÉRIFIER.",
        },
        u'pertinence_pour_les_tests': {
            u'commentaire': u"Le bâtiment exemple porte un STORE EN TISSU "
                            u"(Stoffmarkise Soltis), pas des lamelles : le "
                            u"tableau 9 ne s'applique donc pas aux tests 4 à 6. "
                            u"Il s'applique au TEST 2 (cas à lamelles) — c'est "
                            u"précisément le modèle que TAS ne possède pas "
                            u"(« Kein Lamellenmodell », anwender_test2_3).",
            u'voie_alternative_pour_le_tissu': u"SIA 4010:2023 §3.1.5 : pour les "
                                               u"stores en tissu, remplacer g_g du "
                                               u"vitrage par g_tot (vitrage + "
                                               u"protection) selon SN EN ISO 52022-3 "
                                               u"ou ISO 15099 lorsque la protection "
                                               u"est actionnée — « plus simple et "
                                               u"donne des résultats plus précis ».",
        },
    }


def _ecrire(nom, donnees):
    chemin = os.path.join(_SORTIE, nom)
    with io.open(chemin, 'w', encoding='utf-8') as f:
        f.write(json.dumps(donnees, ensure_ascii=False, indent=2, sort_keys=False))
        f.write(u'\n')
    return chemin


def main():
    controles = verifier_regle_de_decalage()
    print(u'Règle de décalage SIA 380/2 §5.2.2.5 vs SIA 4010 §3.1.4 :')
    for courbe, usage, attendu, calcule in controles:
        print(u'  courbe %-11s usage %-5s  annoncé %d K  calculé %d K  OK'
              % (courbe, usage, attendu, calcule))
    print(u'  -> %d/%d décalages reproduits.' % (len(controles), len(controles)))

    t11 = _par_usage()
    print()
    print(u'Usage 4.04 Hörsaal (consigne du test 4, point ouvert O1) :')
    print(u'  tableau 11 : chauffage %s °C, refroidissement %s °C'
          % (t11[u'4.04'][2], t11[u'4.04'][3]))
    print(u'  groupe 1.01-3.03 : 21 / 26  ->  décalage 0 K / 0 K')

    for nom, donnees in (
            (u'sia-2024-2021.tables.json', construire_sia2024()),
            (u'sia-180-2014.comfort.json', construire_sia180()),
            (u'sia-387-4-2017.blinds.json', construire_sia387_4()),
    ):
        print(u'écrit : %s' % _ecrire(nom, donnees))


if __name__ == '__main__':
    main()
