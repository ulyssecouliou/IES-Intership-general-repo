# -*- coding: utf-8 -*-
u"""Fige le réseau de ventilation des tests SIA 5 et 6, depuis leurs PDF.

POURQUOI UN EXTRACTEUR, ET PAS UN FICHIER ÉCRIT À LA MAIN. La règle 2 du
projet fait de la spécification publiée la seule vérité. Un JSON retapé ne
prouve rien : il affirme, avec l'autorité d'un référentiel, ce que quelqu'un a
cru lire. Ici chaque valeur est TROUVÉE dans la couche texte du PDF par un
motif nommé, et **ce qui n'est pas trouvé n'est pas comblé** : le champ sort à
`null`, en `A_CONFIRMER`, avec la raison.

CE QUE LA COUCHE TEXTE NE DONNE PAS. Deux familles, et elles portent des
valeurs qui décident du résultat :

* **les graphiques.** Les consignes glissantes sont dessinées. Leurs étiquettes
  de données (« 12; 20 ») sont dans le texte et sont donc relevées — mais les
  PALIERS au-delà des points étiquetés ne le sont pas. La courbe
  caractéristique des ventilateurs n'a aucune étiquette : elle sort vide.
* **les tableaux de variantes.** Le Test 5 porte quatre colonnes (5A à 5D) et
  souvent deux cellules fusionnées. Le point de partage n'est pas dans le
  texte. Deviner reviendrait à construire deux variantes sur quatre fausses.

Usage :
    python scripts/build_reseau_ventilation_reference.py [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import re
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

_SPECS = os.path.join(_RACINE, 'SIA_4010_geteilter_Link')
_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data')

#: Statuts possibles d'une valeur. `RELEVE` veut dire « trouvé tel quel dans
#: la couche texte ». Les deux autres disent exactement pourquoi on ne peut pas
#: aller plus loin — ils ne sont PAS des variantes polies de « ok ».
RELEVE = 'RELEVE'
SUR_GRAPHIQUE = 'RELEVE_SUR_GRAPHIQUE'
A_CONFIRMER = 'A_CONFIRMER'

#: Motif d'une étiquette de données de graphique : « abscisse; ordonnée ».
_ETIQUETTE = re.compile(r'(-?\d+(?:\.\d+)?); ?(-?\d+(?:\.\d+)?)')

_NOMBRE = r'([\d\'’]+(?:\.\d+)?)'


def _nombre(texte):
    u"""Convertit un nombre du PDF, séparateurs de milliers compris.

    Args:
        texte: Nombre tel qu'écrit dans le PDF (« 1'040 »).

    Returns:
        float | int: Valeur numérique.
    """
    net = texte.replace(u"'", u'').replace(u'’', u'')
    valeur = float(net)
    return int(valeur) if valeur == int(valeur) else valeur


def _texte_du_pdf(numero_test):
    u"""Extrait la couche texte d'une spécification.

    Args:
        numero_test: 5 ou 6.

    Returns:
        str: Texte concaténé.

    Raises:
        IOError: Si le PDF est absent.
    """
    chemin = os.path.join(_SPECS, 'Test%d' % numero_test,
                          'Spezifikation_Test%d.pdf' % numero_test)
    if not os.path.exists(chemin):
        raise IOError(u'spécification absente : %s' % chemin)
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    lecteur = PdfReader(chemin)
    return u'\n'.join((page.extract_text() or u'') for page in lecteur.pages)


#: Champs cherchés, par test. Chaque entrée est
#: `(bloc, clé, motif, conversion, source)`. Le motif est appliqué au texte
#: entier ; s'il ne mord pas, le champ sort en `A_CONFIRMER`.
CHAMPS = {
    5: [
        ('reseau', 'debit_nominal_m3_h',
         r'Nennvolumenstrom\s*→?\s*' + _NOMBRE + r'\s*m3/h',
         _nombre, u'Volumenstrom / Nennvolumenstrom'),
        ('reseau', 'debit_variable_min_pourcent',
         r'Variabel von bis\s*→?\s*' + _NOMBRE + r'\s*[–-]',
         _nombre, u'Volumenstrom / Variabel von bis'),
        ('reseau', 'horaire_fonctionnement',
         r'Betriebszeit\s*(Werktags[^\n]*)',
         None, u'Regelung / Betriebszeit'),
        ('reseau', 'perte_de_charge_soufflage_pa',
         r'Zuluft\s*→\s*' + _NOMBRE + r'\s*Pa',
         _nombre, u'Nenn-Druckverlust / Zuluft'),
        ('reseau', 'perte_de_charge_reprise_pa',
         r'Abluft\s*→\s*' + _NOMBRE + r'\s*Pa',
         _nombre, u'Nenn-Druckverlust / Abluft'),
        ('reseau', 'infiltration_m3_h_m2',
         r'Infiltration\s*' + _NOMBRE + r'\s*m3/\(h',
         _nombre, u'Infiltration'),
        ('reseau', 'debit_par_personne_m3_h',
         _NOMBRE + r'\s*m3/h pro Person',
         _nombre, u'Lüftung — « abweichend von SIA 2024:2021 »'),
        ('reseau', 'co2_exterieur_ppm',
         r'Aussenluftkonzentration:\s*' + _NOMBRE + r'\s*ppm',
         _nombre, u'Sollwerte / CO2'),
        ('reseau', 'humidite_relative_min_pourcent',
         r'Rel\. Feuchte min\.\s*' + _NOMBRE + r'%',
         _nombre, u'Sollwerte / Rel. Feuchte'),
        ('ventilateurs', 'puissance_soufflage_w',
         r'Zuluftventilator:\s*' + _NOMBRE + r'\s*W',
         _nombre, u'Ventilatoren / Nennleistung'),
        ('ventilateurs', 'puissance_reprise_w',
         r'Abluftventilator:\s*' + _NOMBRE + r'\s*W',
         _nombre, u'Ventilatoren / Nennleistung'),
        ('ventilateurs', 'vitesse_soufflage_min_1',
         r'Zuluftventilator:\s*' + _NOMBRE + r'\s*min-1',
         _nombre, u'Ventilatoren / Drehzahl'),
        ('ventilateurs', 'vitesse_reprise_min_1',
         r'Abluftventilator:\s*' + _NOMBRE + r'\s*min-1',
         _nombre, u'Ventilatoren / Drehzahl'),
        ('recuperateur', 'vitesse_nominale_min_1',
         r'Nominale Drehzahl\s*' + _NOMBRE + r'\s*min-1',
         _nombre, u'Nominale Drehzahl'),
        ('recuperateur', 'puissance_entrainement_w',
         r'Nominale Antriebsleistung\s*' + _NOMBRE + r'\s*W',
         _nombre, u'Nominale Antriebsleistung'),
        ('recuperateur', 'charge_partielle',
         r'Teillastverhalten\s*(Gemäss EN[^\n]*)',
         None, u'Teillastverhalten'),
        ('batterie_froide', 'puissance_kw',
         r'Auslegungsleistung\s*' + _NOMBRE + r'\s*kW',
         _nombre, u'Luftkühler / Auslegungsleistung', u'Luftkühler'),
        ('batterie_froide', 'rendement_echange',
         r'wir-?\s*kungsgrad\s*' + _NOMBRE, _nombre,
         u'Wärmeübertragungswirkungsgrad', u'Luftkühler'),
        ('batterie_froide', 'facteur_bypass',
         r'Bypassfaktor\s*' + _NOMBRE, _nombre, u'Bypassfaktor', u'Luftkühler'),
        ('batterie_froide', 'air_entrant_c',
         r'Eintritts-Lufttemperatur\s*' + _NOMBRE + r'°C',
         _nombre, u'Luftkühler / Eintritts-Lufttemperatur', u'Luftkühler'),
        ('batterie_froide', 'air_entrant_g_kg',
         r'Feuchtegehalt\s*' + _NOMBRE + r'\s*g/kg',
         _nombre, u'Feuchtegehalt', u'Luftkühler'),
        ('batterie_froide', 'air_sortant_c',
         r'Austrittstemperatur\s*' + _NOMBRE + r'°C',
         _nombre, u'Luftkühler / Austrittstemperatur', u'Luftkühler'),
        ('batterie_froide', 'eau_glacee_entree_c',
         r'Kaltwasser-Eintrittstemperatur\s*' + _NOMBRE + r'\s*°C',
         _nombre, u'Kaltwasser-Eintrittstemperatur', u'Luftkühler'),
        ('batterie_chaude', 'puissance_kw',
         r'Auslegungsleistung\s*' + _NOMBRE + r'\s*kW',
         _nombre, u'Lufterhitzer / Auslegungsleistung', u'Lufterhitzer'),
        ('batterie_chaude', 'air_entrant_c',
         r'Eintritts-Lufttemperatur\s*\+?' + _NOMBRE + r'°C',
         _nombre, u'Lufterhitzer / Eintritts-Lufttemperatur', u'Lufterhitzer'),
        ('batterie_chaude', 'air_sortant_c',
         r'Austrittstemperatur\s*' + _NOMBRE + r'°C',
         _nombre, u'Lufterhitzer / Austrittstemperatur', u'Lufterhitzer'),
        ('batterie_chaude', 'eau_chaude_entree_c',
         r'Heizwasser-Eintrittstempera-?\s*tur\s*' + _NOMBRE + r'°C',
         _nombre, u'Heizwasser-Eintrittstemperatur', u'Lufterhitzer'),
        ('humidificateur', 'debit_eau_kg_h',
         r'strom Wasser\s*' + _NOMBRE + r'\s*kg/h',
         _nombre, u'Nenn-Massenstrom Wasser'),
        ('humidificateur', 'energie_pompe_wh_m3',
         r'feuchters\s*' + _NOMBRE + r'\s*Wh/m3',
         _nombre, u'Spez. Pumpenenergie des Befeuchters'),
    ],
    6: [
        ('reseau', 'debit_nominal_stufe3_m3_h',
         r'Stufe 3\s*' + _NOMBRE + r'\s*m3/h',
         _nombre, u'Volumenstrom / Nennvolumenstrom Stufe 3'),
        ('reseau', 'debit_nominal_stufe2_m3_h',
         r'Stufe 2\s*' + _NOMBRE + r'\s*m3/h',
         _nombre, u'Volumenstrom / Stufe 2'),
        ('reseau', 'debit_nominal_stufe1_m3_h',
         r'Stufe 1\s*' + _NOMBRE + r'\s*m3/h',
         _nombre, u'Volumenstrom / Stufe 1'),
        ('reseau', 'horaire_fonctionnement',
         r'Betriebszeit\s*(Montag[^\n]*)',
         None, u'Regelung / Betriebszeit'),
        ('reseau', 'perte_de_charge_soufflage_pa',
         r'Zuluft\s*→\s*' + _NOMBRE + r'\s*Pa',
         _nombre, u'Nenn-Druckverlust / Zuluft'),
        ('reseau', 'perte_de_charge_reprise_pa',
         r'Abluft\s*→\s*' + _NOMBRE + r'\s*Pa',
         _nombre, u'Nenn-Druckverlust / Abluft'),
        ('reseau', 'infiltration_m3_h_m2',
         r'Infiltration\s*' + _NOMBRE + r'\s*m3/\(h',
         _nombre, u'Infiltration'),
        ('reseau', 'surface_nette_m2',
         r'Gemäss Dokumentation \(' + _NOMBRE + r'\s*m2\)',
         _nombre, u'Räume / Nettofläche'),
        ('ventilateurs', 'puissance_soufflage_w',
         r'Zuluftventilator:\s*' + _NOMBRE + r'\s*W',
         _nombre, u'Ventilatoren / Nennleistung'),
        ('ventilateurs', 'puissance_reprise_w',
         r'Abluftventilator:\s*' + _NOMBRE + r'\s*W',
         _nombre, u'Ventilatoren / Nennleistung'),
        ('ventilateurs', 'vitesse_soufflage_min_1',
         r'Zuluftventilator:\s*' + _NOMBRE + r'\s*min-1',
         _nombre, u'Ventilatoren / Drehzahl'),
        ('ventilateurs', 'vitesse_reprise_min_1',
         r'Abluftventilator:\s*' + _NOMBRE + r'\s*min-1',
         _nombre, u'Ventilatoren / Drehzahl'),
        ('recuperateur', 'taux_temperature',
         r'Nominale Temperaturänderungszahl\s*' + _NOMBRE,
         _nombre, u'Kreislaufverbund / Nominale Temperaturänderungszahl'),
        ('recuperateur', 'fluide',
         r'Transportmedium\s*([^\n]+)',
         None, u'Transportmedium'),
        ('recuperateur', 'debit_pompe_l_h',
         r'Volumenstrom Pumpkreis\s*' + _NOMBRE + r'\s*l/h',
         _nombre, u'Nominaler Volumenstrom Pumpkreis'),
        ('recuperateur', 'puissance_pompe_w',
         r'Pumpen-Antriebsleistung\s*' + _NOMBRE + r'\s*W',
         _nombre, u'Nominale Pumpen-Antriebsleistung'),
        ('recuperateur', 'debit_pompe_min_pourcent',
         r'Minimaler Volumenstrom Pumpkreis\s*' + _NOMBRE + r'%',
         _nombre, u'Minimaler Volumenstrom Pumpkreis'),
        ('recuperateur', 'protection_antigel',
         r'schutz\s*(Mit Pumpendrehzahl-Anpassung auf Fortlufttemperatur[^\n]*)',
         None, u'Vereisungsschutz'),
        ('batterie_froide', 'puissance_kw',
         r'Auslegungsleistung\s*' + _NOMBRE + r'\s*kW',
         _nombre, u'Luftkühler / Auslegungsleistung', u'Luftkühler'),
        ('batterie_froide', 'rendement_echange',
         r'wir-?\s*kungsgrad\s*' + _NOMBRE, _nombre,
         u'Wärmeübertragungswirkungsgrad', u'Luftkühler'),
        ('batterie_froide', 'air_entrant_c',
         r'Eintritts-Lufttemperatur\s*' + _NOMBRE + r'°C',
         _nombre, u'Luftkühler / Eintritts-Lufttemperatur', u'Luftkühler'),
        ('batterie_froide', 'air_entrant_g_kg',
         r'Feuchtegehalt\s*' + _NOMBRE + r'\s*g/kg',
         _nombre, u'Feuchtegehalt', u'Luftkühler'),
        ('batterie_froide', 'air_sortant_c',
         r'Austrittstemperatur\s*' + _NOMBRE + r'°C',
         _nombre, u'Luftkühler / Austrittstemperatur', u'Luftkühler'),
        ('batterie_froide', 'eau_glacee_entree_c',
         r'Kaltwasser-Eintrittstemperatur\s*' + _NOMBRE + r'\s*°C',
         _nombre, u'Kaltwasser-Eintrittstemperatur', u'Luftkühler'),
        ('batterie_chaude', 'puissance_kw',
         r'Auslegungsleistung\s*' + _NOMBRE + r'\s*kW',
         _nombre, u'Lufterhitzer / Auslegungsleistung', u'Lufterhitzer'),
        ('batterie_chaude', 'air_entrant_c',
         r'Eintritts-Lufttemperatur\s*\+?' + _NOMBRE + r'°C',
         _nombre, u'Lufterhitzer / Eintritts-Lufttemperatur', u'Lufterhitzer'),
        ('batterie_chaude', 'air_sortant_c',
         r'Austrittstemperatur\s*' + _NOMBRE + r'°C',
         _nombre, u'Lufterhitzer / Austrittstemperatur', u'Lufterhitzer'),
        ('batterie_chaude', 'eau_chaude_entree_c',
         r'Heizwasser-Eintrittstemperatur\s*' + _NOMBRE + r'°C',
         _nombre, u'Heizwasser-Eintrittstemperatur', u'Lufterhitzer'),
    ],
}

#: Graphiques cherchés, par test : `(clé, titre dans le PDF, ordonnée)`. Les
#: points viennent des ÉTIQUETTES DE DONNÉES, seule partie d'un graphique
#: présente dans la couche texte.
COURBES = {
    5: [('temperature_soufflage', u'Zulufttemperatur', u'Zulufttemperatur'),
        ('temperature_eau_glacee', u'Kaltwassertemperatur',
         u'Kaltwassertemperatur'),
        ('temperature_eau_chaude', u'Heizwassertemperatur',
         u'Heizwassertemperatur')],
    6: [('temperature_soufflage', u'Zulufttemperatur', u'Zulufttemperatur'),
        ('temperature_eau_glacee', u'Kaltwassertemperatur',
         u'Kaltwassertemperatur'),
        ('temperature_eau_chaude', u'Heizwassertemperatur',
         u'Heizwassertemperatur')],
}

#: Champs que la couche texte ne peut PAS trancher, avec la raison. Ils sont
#: déclarés ici plutôt que devinés : un référentiel muet sur ses trous est plus
#: dangereux qu'un référentiel incomplet.
TROUS = {
    5: [
        ('ventilateurs', 'kennfeld', u'Ventilatoren / Kennfeld',
         u'Courbe caractéristique : graphique SANS étiquette de données. '
         u'Aucun point n\'en est extractible. Sans elle, la puissance des '
         u'ventilateurs à charge partielle n\'est pas reproductible — et '
         u'c\'est une des grandeurs à livrer.'),
        ('ventilateurs', 'part_pression_constante_pa',
         u'Variante 5A 5B 5C 5D / Konstantdruckanteil (ZUL+ABL)',
         u'Deux cellules (« 50+50 Pa », « 270+270 Pa ») pour QUATRE colonnes '
         u'de variantes. Le point de partage n\'est pas dans la couche texte.'),
        ('recuperateur', 'type_par_variante', u'Variante 5A 5B 5C 5D / Typ',
         u'Deux cellules (« Hygroskopisch », « Nicht hygroskopisch ») pour '
         u'quatre colonnes.'),
        ('recuperateur', 'taux_temperature_par_variante',
         u'Nominale Temperaturänderungszahl',
         u'Deux cellules (0.67, 0.69) pour quatre colonnes.'),
        ('recuperateur', 'taux_humidite_par_variante',
         u'Nominale Feuchteänderungszahl',
         u'Deux cellules (0.42, 0.3) pour quatre colonnes.'),
        ('humidificateur', 'type_par_variante',
         u'Luftbefeuchter / Variante 5A 5B 5C 5D / Typ',
         u'Deux cellules (« Kontaktbefeuchter », « Dampf ») pour quatre '
         u'colonnes. Le dépôt suppose ailleurs « contact 5A-5C, vapeur 5D » '
         u'(build_traceability_matrix.ANCRAGE) : cette supposition n\'est PAS '
         u'confirmée par la couche texte et doit être tranchée.'),
    ],
    6: [
        ('ventilateurs', 'kennfeld', u'Ventilatoren / Kennfeld',
         u'Courbe caractéristique : graphique sans étiquette de données.'),
        ('reseau', 'debit_du_local_restaurant_m3_h',
         u'Lüftung (p. 1) contre RLT-Anlage / Volumenstrom (p. 3)',
         u'CONTRADICTION APPARENTE : la page 1 annonce « Zuluft 3\'000 m3/h, '
         u'Abluft 2\'650 m3/h » et la section RLT un nominal de 6\'150 m3/h '
         u'en étage 3. Les deux ne se rapportent probablement pas au même '
         u'périmètre (local seul / centrale desservant aussi la cuisine), '
         u'mais la spécification ne le dit pas. Saisir l\'un pour l\'autre '
         u'fausserait tout le bilan aéraulique.'),
        ('reseau', 'profil_stufenbetrieb',
         u'Regelung / Stufenbetrieb',
         u'Le profil horaire des trois étages est un GRAPHIQUE (débit relatif '
         u'0 / 0.33 / 0.67 / 1.00 sur 24 h). Les paliers y sont lisibles mais '
         u'pas les heures de bascule.'),
    ],
}


def _chercher(texte, motif, conversion, source, depuis=None):
    u"""Cherche un champ dans la couche texte.

    Args:
        texte: Texte du PDF.
        motif: Expression régulière à un groupe.
        conversion: Fonction de conversion, ou `None` pour du texte brut.
        source: Section du PDF, pour la traçabilité.
        depuis: Titre de section à partir duquel chercher. Sans lui, les
            libellés partagés — `Auslegungsleistung`, `Austrittstemperatur` —
            mordent sur le premier appareil venu : la batterie chaude
            hériterait des valeurs du refroidisseur, en silence.

    Returns:
        dict: Valeur et statut. `null` + `A_CONFIRMER` si le motif ne mord pas
        — jamais une valeur par défaut.
    """
    if depuis is not None:
        debut = texte.find(depuis)
        if debut < 0:
            return {'valeur': None, 'statut': A_CONFIRMER, 'source': source,
                    'a_confirmer': u'Section « %s » introuvable dans le PDF.'
                                   % depuis}
        texte = texte[debut:]
    trouve = re.search(motif, texte)
    if trouve is None:
        return {'valeur': None, 'statut': A_CONFIRMER, 'source': source,
                'a_confirmer': u'Motif introuvable dans la couche texte du '
                               u'PDF. La valeur n\'a PAS été devinée.'}
    brut = trouve.group(1).strip()
    return {'valeur': conversion(brut) if conversion else brut,
            'statut': RELEVE, 'source': source}


#: Distance maximale, en caractères, entre une étiquette de données et le
#: titre du graphique auquel elle appartient. Au-delà, l'étiquette est
#: orpheline : mieux vaut ne pas l'attribuer que l'attribuer au hasard.
PORTEE_ETIQUETTE = 400

#: Écart maximal, en caractères, entre deux étiquettes d'un MÊME
#: graphique. Au-delà, elles viennent de graphiques différents.
ECART_MEME_GRAPHIQUE = 60

#: Nombre isolé, pour relever les graduations d'un axe.
_GRADUATION = re.compile(r'-?\d+(?:\.\d+)?')


def _attribuer_les_etiquettes(texte, titres):
    u"""Rattache chaque étiquette de données au graphique le PLUS PROCHE.

    Une simple recherche « le titre apparaît-il dans les N caractères qui
    suivent » ne suffit pas : deux graphiques se succèdent dans le flux, et
    les points de l'eau glacée se retrouvaient aussi rangés sous l'eau chaude.
    Le graphique le plus proche gagne.

    Args:
        texte: Texte du PDF.
        titres: Titres des graphiques cherchés.

    Returns:
        dict: `{titre: [(couple, position, fin_du_graphique)]}`.
    """
    attribution = dict((titre, []) for titre in titres)
    for etiquette in _ETIQUETTE.finditer(texte):
        proche, distance = None, None
        for titre in titres:
            position = texte.find(titre, etiquette.end())
            if position < 0:
                continue
            ecart = position - etiquette.end()
            if distance is None or ecart < distance:
                proche, distance = titre, ecart
        if proche is None or distance > PORTEE_ETIQUETTE:
            continue
        attribution[proche].append(
            (etiquette.group(0),
             [_nombre(etiquette.group(1)), _nombre(etiquette.group(2))],
             etiquette.end(), etiquette.end() + distance))
    return attribution


def _courbe(texte, titre, ordonnee, attribution):
    u"""Relève les étiquettes de données d'un graphique de consigne glissante.

    Un point dont l'ordonnée sort des graduations de l'axe n'est pas corrigé :
    il fait ÉCHOUER la courbe entière. « 20; 2018 » vient d'une graduation
    collée à la valeur ; deviner que 2018 voulait dire 20 serait exactement
    l'invention que la règle 1 interdit.

    Args:
        texte: Texte du PDF.
        titre: Titre du graphique.
        ordonnee: Libellé de l'ordonnée.
        attribution: Ce que rend `_attribuer_les_etiquettes`.

    Returns:
        dict: Points relevés et réserves de lecture.
    """
    retenues, suspects = [], []
    for brut, couple, debut, fin in attribution.get(titre, []):
        graduations = [float(g) for g in _GRADUATION.findall(texte[debut:fin])]
        if graduations and not (min(graduations) <= couple[1]
                                <= max(graduations)):
            suspects.append(u'« %s » : ordonnée %s hors des graduations '
                            u'[%g ; %g] du graphique — l\'extraction a '
                            u'probablement collé deux nombres.'
                            % (brut, couple[1], min(graduations),
                               max(graduations)))
            continue
        retenues.append((brut, couple, debut))
    if suspects:
        return {'points': None, 'statut': A_CONFIRMER, 'ordonnee': ordonnee,
                'a_confirmer': u' '.join(suspects)}

    # Les étiquettes d'un même graphique se suivent dans le flux. Un saut
    # révèle un graphique VOISIN, capté parce qu'il n'a pas de titre à lui —
    # cas du Test 6, où trois points d'une autre consigne se rangeaient sous
    # la température de soufflage. On ne choisit pas : on refuse et on montre
    # les groupes, pour que la lecture du PDF prenne dix secondes.
    groupes = []
    for brut, couple, debut in retenues:
        if groupes and debut - groupes[-1][-1][2] <= ECART_MEME_GRAPHIQUE:
            groupes[-1].append((brut, couple, debut))
        else:
            groupes.append([(brut, couple, debut)])
    if len(groupes) > 1:
        return {
            'points': None, 'statut': A_CONFIRMER, 'ordonnee': ordonnee,
            'groupes_candidats': [[c for _, c, _ in groupe]
                                  for groupe in groupes],
            'a_confirmer':
                u'%d groupes d\'étiquettes se disputent ce graphique : %s. Un '
                u'graphique voisin sans titre propre a été capté. Lire le PDF '
                u'et retenir le bon groupe.'
                % (len(groupes),
                   u' / '.join(u'[%s]' % u', '.join(brut for brut, _, _ in g)
                               for g in groupes)),
        }
    points = []
    for _, couple, _ in retenues:
        if couple not in points:
            points.append(couple)
    if not points:
        return {'points': None, 'statut': A_CONFIRMER,
                'ordonnee': ordonnee,
                'a_confirmer': u'Aucune étiquette de données lisible pour ce '
                               u'graphique.'}
    return {
        'points': points, 'statut': SUR_GRAPHIQUE,
        'abscisse': u'Aussenlufttemperatur (°C)', 'ordonnee': ordonnee,
        'reserve_de_lecture':
            u'Points relevés sur les ÉTIQUETTES DE DONNÉES du graphique. Les '
            u'PALIERS au-delà de ces points ne sont pas étiquetés : le tracé '
            u'les suggère constants, la spécification ne l\'écrit pas.',
    }


def construire(numero_test):
    u"""Extrait le réseau de ventilation d'un test.

    Args:
        numero_test: 5 ou 6.

    Returns:
        dict: Référentiel figé.

    Raises:
        ValueError: Si le test n'a pas de réseau décrit ici.
    """
    if numero_test not in CHAMPS:
        raise ValueError(u'test %r sans réseau de ventilation décrit ici. '
                         u'Concernés : %s.' % (numero_test, sorted(CHAMPS)))
    texte = _texte_du_pdf(numero_test)
    reference = {
        '_source': 'SIA_4010_geteilter_Link/Test%d/Spezifikation_Test%d.pdf'
                   % (numero_test, numero_test),
        '_producteur': 'scripts/build_reseau_ventilation_reference.py',
        '_avertissement':
            u'Ce fichier fige une LECTURE de la spécification, pas une '
            u'validation. Rien n\'y est calculé ni complété : un champ que la '
            u'couche texte ne donne pas sort à `null`, en `A_CONFIRMER`.',
        'test': numero_test,
    }
    for entree in CHAMPS[numero_test]:
        bloc, cle, motif, conversion, source = entree[:5]
        depuis = entree[5] if len(entree) > 5 else None
        reference.setdefault(bloc, {})[cle] = _chercher(
            texte, motif, conversion, source, depuis)
    for bloc, cle, source, raison in TROUS[numero_test]:
        reference.setdefault(bloc, {})[cle] = {
            'valeur': None, 'statut': A_CONFIRMER, 'source': source,
            'a_confirmer': raison}
    attribution = _attribuer_les_etiquettes(
        texte, [titre for _, titre, _ in COURBES[numero_test]])
    reference['courbes'] = dict(
        (cle, _courbe(texte, titre, ordonnee, attribution))
        for cle, titre, ordonnee in COURBES[numero_test])
    reference['_bilan'] = bilan(reference)
    return reference


def bilan(reference):
    u"""Compte ce qui est relevé et ce qui ne l'est pas.

    Un référentiel dont on ne sait pas combien de champs sont vides invite à
    le croire complet.

    Args:
        reference: Référentiel construit.

    Returns:
        dict: Effectifs par statut, et liste des champs à confirmer.
    """
    effectifs, a_confirmer = {}, []
    for nom_bloc, bloc in sorted(reference.items()):
        if nom_bloc.startswith('_') or not isinstance(bloc, dict):
            continue
        for cle, champ in sorted(bloc.items()):
            if not isinstance(champ, dict) or 'statut' not in champ:
                continue
            statut = champ['statut']
            effectifs[statut] = effectifs.get(statut, 0) + 1
            if statut == A_CONFIRMER:
                a_confirmer.append(u'%s.%s' % (nom_bloc, cle))
    return {'effectifs': effectifs, 'a_confirmer': a_confirmer}


def main(arguments=()):
    u"""Point d'entrée.

    Args:
        arguments: `--ecrire` pour figer les fichiers.

    Returns:
        int: 0 si les deux tests ont pu être extraits.
    """
    for numero in sorted(CHAMPS):
        try:
            reference = construire(numero)
        except IOError as erreur:
            print(u'Test %d : %s' % (numero, erreur))
            return 1
        compte = reference['_bilan']['effectifs']
        print(u'Test %d : %d relevés, %d sur graphique, %d à confirmer'
              % (numero, compte.get(RELEVE, 0), compte.get(SUR_GRAPHIQUE, 0),
                 compte.get(A_CONFIRMER, 0)))
        for champ in reference['_bilan']['a_confirmer']:
            print(u'    à confirmer : %s' % champ)
        if '--ecrire' in arguments:
            chemin = os.path.join(_SORTIE, 'test-%d.reseau.json' % numero)
            with io.open(chemin, 'w', encoding='utf-8') as flux:
                flux.write(json.dumps(reference, ensure_ascii=False, indent=2,
                                      sort_keys=True))
            print(u'    écrit : %s' % os.path.relpath(chemin, _RACINE))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
