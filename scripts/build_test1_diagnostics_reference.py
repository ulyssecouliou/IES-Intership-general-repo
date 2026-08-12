# -*- coding: utf-8 -*-
u"""Fige la chaîne des cas diagnostiques 1A à 1E du Test 1, depuis les PDF.

POURQUOI CE FICHIER EXISTE. Le cas **1E** est le seul cas du Test 1 à porter un
critère pass/fail, et il n'est pas générable : la spécification le définit comme
« Diagnosefall 1D, jedoch mit Stoffmarkisen-Sonnenschutz », et 1D est lui-même
au bout d'une chaîne 1A → 1B → 1C → 1D. Rien de tout cela n'était figé, donc
personne ne pouvait construire 1E sans deviner. Ce producteur relève la chaîne
et ses paramètres là où ils sont écrits.

TROIS SOURCES, TROIS RÔLES.

* `Spezifikation_Test1.pdf` énonce la chaîne elle-même (Diag 1A à 1D) et la
  définition de 1E. Le texte allemand est relevé **verbatim** : une
  paraphrase française dans un référentiel serait une interprétation déguisée
  en donnée.
* `Spezifikation_Test2.pdf` porte ce que chaque maillon ajoute — la fenêtre,
  l'infiltration, l'usage SIA 2024, la régulation du store.
* `Dokumentation_Beispielgebäude_V5.pdf` porte les propriétés de la fenêtre
  entière, store déployé et store rentré.

CE QUI N'EST PAS TROUVÉ N'EST PAS COMBLÉ. Chaque champ sort avec son statut :
`RELEVE` s'il a été trouvé tel quel dans la couche texte, `A_CONFIRMER` avec la
raison sinon. Un `null` explicite vaut mieux qu'une valeur plausible.

LE PIÈGE DE L'ORDRE DES COLONNES. Le tableau optique donne deux nombres par
ligne, sans les nommer : « Total solar energy transmittance gtot 0.545 0.059 ».
L'ordre vient d'un en-tête séparé, « Without shading With shading ». Si cet
en-tête est absent du texte extrait, **toutes** les propriétés optiques sortent
en `A_CONFIRMER` plutôt que sur une hypothèse d'ordre : les intervertir
donnerait un store qui laisse passer dix fois trop de soleil, et le résultat
resterait crédible.

CE QUE CE FICHIER NE FAIT PAS. Il ne construit aucun modèle VE, n'enregistre
aucun cas, et ne prétend pas que 1E est validable. Il fournit la donnée tracée
sans laquelle cette question ne peut même pas être posée.
"""

from __future__ import print_function

import hashlib
import io
import json
import os
import re
import sys


_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SPECS = os.path.join(_RACINE, 'SIA_4010_geteilter_Link')
_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data')

#: Statuts d'un champ. `A_CONFIRMER` n'est pas une variante polie de « ok ».
RELEVE = 'RELEVE'
A_CONFIRMER = 'A_CONFIRMER'

_NOMBRE = r'(-?\d+(?:[.,]\d+)?)'

#: Les trois sources, avec leur rôle. Le chemin est relatif à `_SPECS`.
SOURCES = (
    ('specification_test_1', os.path.join('Test1', 'Spezifikation_Test1.pdf'),
     u"Énonce la chaîne Diag 1A à 1D et la définition du cas 1E."),
    ('specification_test_2', os.path.join('Test2', 'Spezifikation_Test2.pdf'),
     u"Porte la fenêtre, l'infiltration, l'usage SIA 2024 et la régulation "
     u"du store que les maillons ajoutent."),
    ('documentation_batiment_exemple',
     os.path.join(u'Beispielgebäude', u'Dokumentation_Beispielgebäude_V5.pdf'),
     u"Porte les propriétés de la fenêtre entière, store déployé et rentré."),
)

#: Quatrième source, hors du lien partagé : l'extrait d'autorité SIA 2024 reçu
#: le 2026-08-10. La spécification renvoie à SIA 2024:2021 sans reproduire la
#: fiche ; c'est cet extrait qui donne le gain sensible des occupants et les
#: horaires. Sans lui, le maillon 1D resterait bloqué sur une conversion
#: met → watts — or aucune conversion n'est nécessaire, la fiche donne
#: directement des W/m².
SOURCE_SIA_2024 = os.path.join(
    'sia4010_evidence', 'source_audits', 'sia2024_3_1_authority_20260810',
    'sia2024_office_3_1_standard_profiles.binding.json')

#: Valeurs lues dans l'extrait : `(bloc, clé, chemin dans standard_values)`.
CHAMPS_SIA_2024 = (
    ('apports', 'personnes_gain_sensible_w_m2',
     ('people', 'sensible_heat_gain_at_24c_w_m2')),
    ('apports', 'personnes_simultaneite_annuelle',
     ('people', 'annual_simultaneity_factor')),
    ('apports', 'personnes_heures_par_jour',
     ('people', 'use_hours_per_day_h')),
    ('apports', 'personnes_jours_par_an',
     ('people', 'use_days_per_year_d')),
)

#: Maillons de la chaîne. Le motif relève la définition allemande verbatim dans
#: `Spezifikation_Test1.pdf`. `ajoute` nomme, en français, ce que le maillon
#: ajoute au précédent — c'est un index de lecture, pas une donnée normative :
#: la donnée est la citation allemande.
CHAINE = (
    ('1A', r'Diag\s*1A\s*(.*?)\s*Diag\s*1\s*B', u'climat Zürich-Kloten'),
    ('1B', r'Diag\s*1\s*B\s*(.*?)\s*Diag\s*1C', u'nouvelle fenêtre'),
    ('1C', r'Diag\s*1C\s*(.*?)\s*Diag\s*1D', u'infiltration ajustée'),
    ('1D', r'Diag\s*1D\s*(.*?)\s*Zu\s*liefernde', u'usage SIA 2024'),
    ('1E', r'Testfall\s*1E\s*:\s*(.*?)\s*Zu\s*liefernde',
     u'store tissu (Stoffmarkise)'),
)

#: Paramètres relevés dans `Spezifikation_Test2.pdf`.
#: `(bloc, clé, motif, conversion, localisation)`.
PARAMETRES_TEST_2 = (
    ('usage', 'categorie_sia_2024',
     r'Standardnutzung\s*"([^"]+)"\s*gem[äa]ss\s*SIA\s*2024:2021',
     None, u'Nutzung / Standardnutzung'),
    ('usage', 'personnes_par_piece',
     r'Personen\s*Anzahl\s*→?\s*' + _NOMBRE,
     'nombre', u'Wärmeeinträge / Personen / Anzahl'),
    ('infiltration', 'debit_m3_h_m2',
     r'Infiltration\s*' + _NOMBRE + r'\s*m3/\(h\*m2\)\s*gem[äa]ss\s*SIA\s*2024:2021',
     'nombre', u'Lüftung / Infiltration'),
    ('consignes', 'chauffage_celsius',
     r'Ideales\s*Heizelement,\s*Raumtemperatur-Sollwert\s*' + _NOMBRE + r'\s*°C',
     'nombre', u'Wärmeabgabe'),
    ('consignes', 'refroidissement_celsius',
     r'Ideales\s*K[üu]hlelement,\s*Raumtemperatur-Sollwert\s*' + _NOMBRE + r'\s*°C',
     'nombre', u'Kälteabgabe'),
    # Le type porte une espace (« Soltis 92-2048-Alu »), donc pas de `\S+` sur
    # le premier groupe : il ne relevait que « Soltis ».
    ('store', 'produit',
     r'Test\s*2A\s*Stoffmarkise\s*Typ\s*(.+?)\s+von\s+(\S+)',
     'produit', u'Sonnenschutz / Test 2A Stoffmarkise'),
    ('store', 'seuil_activation_w_m2',
     r'Aktivierung\s*→?\s*Schwellenwert\s*' + _NOMBRE + r'\s*W/m2',
     'nombre', u'Sonnenschutz Extern / Aktivierung'),
    # La fenêtre du maillon 1B. La spécification la chiffre elle-même, ce qui
    # tranche une question que la documentation du bâtiment exemple laisse
    # ouverte : celle-ci donne deux g totaux, en conditions d'été (0,545) et de
    # référence (0,542). La spécification retient 0,545. On relève donc la
    # spécification, qui définit le cas, et non la documentation.
    # Le type porte des espaces, comme le store : `\S+` ne relevait que « SGG ».
    ('vitrage', 'type',
     r'Verglasung\s*Typ\s*(.+?)\s*Gesamtenergie',
     None, u'Verglasung / Typ'),
    ('vitrage', 'g_total',
     r'durchlassgrad\s*gg\s*:?\s*→?\s*' + _NOMBRE,
     'nombre', u'Verglasung / Gesamtenergiedurchlassgrad gg'),
    ('vitrage', 'u_vitrage_w_m2k',
     r'U-Wert\s*Ug\s*→?\s*' + _NOMBRE + r'\s*W/m2K',
     'nombre', u'Verglasung / U-Wert Ug'),
    # Les symboles grecs de ces deux lignes ne sont PAS des caractères Unicode
    # grecs : l'extraction rend « τv » et « ρv » comme  et , des
    # glyphes de zone privée de la police Symbol. Un motif écrit avec le vrai
    # τ ne mordrait jamais, et le champ sortirait en A_CONFIRMER en laissant
    # croire que la spécification ne donne pas la valeur. D'où le joker.
    ('vitrage', 'transmission_visible',
     r'Transmission\s*v\s*\S*:\s*→?\s*' + _NOMBRE,
     'nombre', u'Verglasung / Transmission v'),
    ('vitrage', 'reflexion_visible',
     r'Reflexion\s*v\s*\S*:\s*→?\s*' + _NOMBRE,
     'nombre', u'Verglasung / Reflexion v'),
    # Les apports du maillon 1D. Les densités de puissance sont dans la
    # spécification ; seuls les HORAIRES renvoient à SIA 2024:2021, et pour la
    # catégorie 3.1 nous détenons l'extrait d'autorité du 2026-08-10.
    ('apports', 'personnes_m2_par_personne',
     r'\(' + _NOMBRE + r'\s*m2\s*pro\s*Person\)',
     'nombre', u'Wärmeeinträge / Personen'),
    ('apports', 'personnes_activite_met',
     r'Aktivit[äa]tsgrad\s*→?\s*' + _NOMBRE + r'\s*met',
     'nombre', u'Wärmeeinträge / Personen / Aktivitätsgrad'),
    ('apports', 'appareils_w_m2',
     r'Ger[äa]te\s*W[äa]rmeeintragsleistung\s*→?\s*' + _NOMBRE + r'\s*W/m2',
     'nombre', u'Wärmeeinträge / Geräte'),
    ('apports', 'eclairage_w_m2',
     r'Beleuchtung\s*W[äa]rmeeintragsleistung\s*→?\s*' + _NOMBRE + r'\s*W/m2',
     'nombre', u'Wärmeeinträge / Beleuchtung'),
    ('apports', 'eclairage_puissance_installee_w_m2',
     r'Anschlusswert\s*→?\s*' + _NOMBRE + r'\s*W/m2',
     'nombre', u'Wärmeeinträge / Beleuchtung / Anschlusswert'),
)

#: Paramètres relevés dans la documentation du bâtiment exemple.
PARAMETRES_BATIMENT = (
    ('store', 'lame_d_air_cm',
     r'Luftspalt\s*von\s*' + _NOMBRE + r'\s*cm',
     'nombre', u'2.2.2 Verschattung'),
    ('store', 'seuil_fermeture_w_m2',
     r'bei\s*einer\s*Solarstrahlung\s*von\s*' + _NOMBRE + r'\s*W/m2',
     'nombre', u'2.2.2 Verschattung'),
)

#: En-tête qui FIXE l'ordre des deux colonnes du tableau optique. Sans lui,
#: aucune propriété optique n'est relevée.
ORDRE_COLONNES = re.compile(r'Without\s+shading\s+With\s+shading')

#: Blocs du tableau optique : `(clé, début, fin)`. Les bornes sont les
#: en-têtes imprimés ; elles évitent de confondre les deux lignes `gtot`, qui
#: portent des valeurs différentes en conditions d'été et de référence.
BLOCS_OPTIQUES = (
    ('en_iso_52022_3_conditions_ete',
     r'EN\s*ISO\s*52022-3\s*\(summer\s*conditions\)\s*:',
     r'EN\s*ISO\s*52022-3\s*\(reference\s*conditions\)\s*:'),
    ('en_iso_52022_3_conditions_reference',
     r'EN\s*ISO\s*52022-3\s*\(reference\s*conditions\)\s*:',
     r'EN\s*410\s*:'),
    ('en_410', r'EN\s*410\s*:', r'Layer\s*d\s*\[mm\]'),
)

#: Grandeurs cherchées dans chaque bloc optique, par leur symbole imprimé.
#: `(clé, motif du libellé et du symbole, unité)`.
GRANDEURS_OPTIQUES = (
    ('g_total', r'Total\s*solar\s*energy\s*transmittance\s*gtot', u'-'),
    ('facteur_convection_gc', r'Convection\s*factor\s*gc', u'-'),
    ('facteur_rayonnement_gth', r'Thermal\s*radiation\s*factor\s*gth', u'-'),
    ('facteur_ventilation_gv', r'Ventilation\s*factor\s*gv', u'-'),
    ('transfert_secondaire_qi',
     r'Secondary\s*internal\s*heat\s*transfer\s*factor\s*qi', u'-'),
    ('u_vitrage_w_m2k', r'U-value\s*of\s*glazing\s*Ug', u'W/(m2 K)'),
    ('transmission_solaire_directe_te',
     r'Direct\s*solar\s*transmittance\s*[τt]e', u'-'),
    ('reflexion_solaire_exterieure_re',
     r'Solar\s*reflectance\s*outside\s*[ρp]e', u'-'),
    ('reflexion_solaire_interieure_re_prime',
     r"Solar\s*reflectance\s*inside\s*[ρp]'e", u'-'),
    ('transmission_visible_tv', r'Visual\s*transmittance\s*[τt]v', u'-'),
    ('reflexion_visible_exterieure_rv',
     r'Visual\s*reflectance\s*outside\s*[ρp]v', u'-'),
    ('reflexion_visible_interieure_rv_prime',
     r"Visual\s*reflectance\s*inside\s*[ρp]'v", u'-'),
    ('transmission_uv_tuv', r'UV-transmittance\s*[τt]uv', u'-'),
)


def _nombre(texte):
    u"""Convertit un nombre du PDF en valeur numérique.

    Args:
        texte: Nombre tel qu'écrit dans le PDF.

    Returns:
        float | int: Valeur numérique.
    """
    valeur = float(texte.replace(u',', u'.'))
    return int(valeur) if valeur == int(valeur) else valeur


def _empreinte(chemin):
    u"""Renvoie le SHA-256 d'un fichier source.

    Args:
        chemin: Chemin du fichier.

    Returns:
        str: Empreinte hexadécimale.
    """
    digest = hashlib.sha256()
    with open(chemin, 'rb') as flux:
        for bloc in iter(lambda: flux.read(65536), b''):
            digest.update(bloc)
    return digest.hexdigest()


def _texte_normalise(chemin):
    u"""Extrait la couche texte d'un PDF, espaces normalisés.

    La normalisation est nécessaire : l'extraction coupe les lignes du tableau
    à des endroits qui varient, et un motif écrit sur le texte brut mordrait
    ou non selon la mise en page.

    Args:
        chemin: Chemin du PDF.

    Returns:
        str: Texte, espaces réduits à un seul.

    Raises:
        IOError: Si le PDF est absent.
    """
    if not os.path.exists(chemin):
        raise IOError(u'source absente : %s' % chemin)
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    lecteur = PdfReader(chemin)
    brut = u'\n'.join((page.extract_text() or u'') for page in lecteur.pages)
    return u' '.join(brut.split())


def _champ_absent(source, raison):
    u"""Renvoie un champ non relevé, avec la raison de son absence.

    Args:
        source: Localisation cherchée dans le document.
        raison: Pourquoi la valeur n'a pas été relevée.

    Returns:
        dict: Champ en `A_CONFIRMER`.
    """
    return {'valeur': None, 'statut': A_CONFIRMER, 'source': source,
            'raison': raison}


def _chercher(texte, motif, conversion, source):
    u"""Relève un champ par son motif, ou explique pourquoi il manque.

    Args:
        texte: Texte normalisé du document.
        motif: Expression régulière à un ou deux groupes.
        conversion: `'nombre'`, `'produit'` ou `None` pour du texte brut.
        source: Localisation dans le document, citée dans le référentiel.

    Returns:
        dict: Champ relevé ou en `A_CONFIRMER`.
    """
    trouve = re.search(motif, texte)
    if trouve is None:
        return _champ_absent(source, u'motif absent de la couche texte')
    if conversion == 'nombre':
        try:
            valeur = _nombre(trouve.group(1))
        except ValueError:
            return _champ_absent(
                source, u'valeur non numérique : %r' % trouve.group(1))
    elif conversion == 'produit':
        valeur = {'type': trouve.group(1), 'fabricant': trouve.group(2)}
    else:
        valeur = trouve.group(1).strip()
    return {'valeur': valeur, 'statut': RELEVE, 'source': source}


def _proprietes_optiques(texte):
    u"""Relève le tableau de la fenêtre entière, store rentré et déployé.

    L'ordre des deux colonnes n'est pas déductible des lignes : il vient de
    l'en-tête « Without shading With shading ». Sans cet en-tête, rien n'est
    relevé — une interversion donnerait un store dix fois trop transparent
    sans que le résultat cesse d'être crédible.

    Args:
        texte: Texte normalisé de la documentation du bâtiment exemple.

    Returns:
        dict: Blocs normatifs, chacun portant ses grandeurs.
    """
    en_tete = ORDRE_COLONNES.search(texte)
    if en_tete is None:
        return {
            'statut': A_CONFIRMER,
            'raison': (u"l'en-tête « Without shading With shading » est absent "
                       u"du texte extrait ; l'ordre des deux colonnes n'est "
                       u"donc pas démontré et aucune propriété n'est relevée"),
            'blocs': {},
        }

    blocs = {}
    for cle_bloc, debut, fin in BLOCS_OPTIQUES:
        borne_debut = re.search(debut, texte)
        # La borne de fin est cherchée APRÈS la borne de début, et pas dans le
        # document entier : « Layer d [mm] » apparaît deux fois, et la première
        # occurrence précède « EN 410: ». La chercher globalement donnait un
        # segment de longueur négative, donc un bloc vide, sans erreur visible.
        borne_fin = (re.compile(fin).search(texte, borne_debut.end())
                     if borne_debut is not None else None)
        if borne_debut is None or borne_fin is None:
            blocs[cle_bloc] = {
                'statut': A_CONFIRMER,
                'raison': u'bornes du bloc absentes de la couche texte',
                'grandeurs': {},
            }
            continue
        segment = texte[borne_debut.end():borne_fin.start()]
        grandeurs = {}
        for cle, libelle, unite in GRANDEURS_OPTIQUES:
            trouve = re.search(libelle + r'\s*' + _NOMBRE + r'\s*' + _NOMBRE,
                               segment)
            if trouve is None:
                continue
            grandeurs[cle] = {
                'unite': unite,
                'store_rentre': _nombre(trouve.group(1)),
                'store_deploye': _nombre(trouve.group(2)),
                'statut': RELEVE,
            }
        blocs[cle_bloc] = {
            'statut': RELEVE if grandeurs else A_CONFIRMER,
            'grandeurs': grandeurs,
        }
        if not grandeurs:
            blocs[cle_bloc]['raison'] = (
                u'aucune grandeur du tableau relevée dans ce bloc')
    return {
        'statut': RELEVE,
        'ordre_colonnes': u'première colonne = store rentré, seconde = store '
                          u'déployé, d\'après l\'en-tête imprimé',
        'blocs': blocs,
    }


def _divergences(texte_batiment, parametres):
    u"""Relève les écarts entre la spécification et la documentation.

    Deux documents officiels donnent le U du vitrage, et ils ne disent pas la
    même chose. Trancher ici reviendrait à corriger l'un des deux à la place de
    son auteur ; on consigne l'écart et on nomme celui qui définit le cas.

    Args:
        texte_batiment: Texte normalisé de la documentation du bâtiment exemple.
        parametres: Paramètres déjà relevés dans la spécification Test 2.

    Returns:
        list[dict]: Écarts constatés, vide si les sources concordent.
    """
    ecarts = []
    spec = parametres.get('vitrage', {}).get('u_vitrage_w_m2k', {})
    if spec.get('statut') != RELEVE:
        return ecarts
    trouve = re.search(r'U-value\s*of\s*glazing\s*Ug\s*' + _NOMBRE, texte_batiment)
    if trouve is None:
        return ecarts
    documentation = _nombre(trouve.group(1))
    if documentation == spec['valeur']:
        return ecarts
    ecarts.append({
        'grandeur': 'u_vitrage_w_m2k',
        'specification_test_2': spec['valeur'],
        'documentation_batiment_exemple': documentation,
        'ecart': round(abs(spec['valeur'] - documentation), 6),
        'retenu': 'specification_test_2',
        'pourquoi': (
            u"La spécification définit le cas de test ; la documentation décrit "
            u"le bâtiment exemple. En cas d'écart, c'est la spécification qui "
            u"fait foi pour construire le modèle. L'écart est consigné et non "
            u"corrigé : le signaler à la sous-commission vaut mieux que de "
            u"réparer un document officiel à la place de son auteur."
        ),
    })
    return ecarts


def construire():
    u"""Assemble le référentiel de la chaîne 1A à 1E.

    Returns:
        dict: Référentiel tracé, prêt à être figé en JSON.
    """
    sources = {}
    textes = {}
    for cle, relatif, role in SOURCES:
        chemin = os.path.join(_SPECS, relatif)
        textes[cle] = _texte_normalise(chemin)
        sources[cle] = {
            'fichier': u'SIA_4010_geteilter_Link/' + relatif.replace('\\', '/'),
            'sha256': _empreinte(chemin),
            'role': role,
        }

    chaine = []
    for cas, motif, ajoute in CHAINE:
        releve = _chercher(textes['specification_test_1'], motif, None,
                           u'Diagnosefälle / Testfall 1E')
        chaine.append({
            'cas': cas,
            'definition_verbatim_de': releve['valeur'],
            'statut': releve['statut'],
            'source': releve['source'],
            'ajoute_au_precedent': ajoute,
            'raison': releve.get('raison'),
        })

    # L'extrait d'autorité SIA 2024, s'il est présent. Son absence ne fait pas
    # échouer la production : les champs concernés sortent en `A_CONFIRMER`,
    # comme n'importe quelle valeur non trouvée.
    chemin_sia_2024 = os.path.join(_RACINE, SOURCE_SIA_2024)
    extrait_sia_2024 = None
    if os.path.exists(chemin_sia_2024):
        with io.open(chemin_sia_2024, encoding='utf-8') as flux:
            extrait_sia_2024 = json.load(flux)
        sources['extrait_autorite_sia_2024'] = {
            'fichier': SOURCE_SIA_2024.replace('\\', '/'),
            'sha256': _empreinte(chemin_sia_2024),
            'role': (
                u"Extrait d'autorité du 2026-08-10 pour la catégorie d'usage "
                u"3.1. Donne le gain sensible des occupants en W/m² et les "
                u"horaires, que la spécification ne reproduit pas."
            ),
            'categorie': extrait_sia_2024.get('use_category'),
        }

    parametres = {}
    for bloc, cle, motif, conversion, source in PARAMETRES_TEST_2:
        parametres.setdefault(bloc, {})[cle] = _chercher(
            textes['specification_test_2'], motif, conversion, source)
    for bloc, cle, motif, conversion, source in PARAMETRES_BATIMENT:
        parametres.setdefault(bloc, {})[cle] = _chercher(
            textes['documentation_batiment_exemple'], motif, conversion, source)
    for bloc, cle, chemin in CHAMPS_SIA_2024:
        localisation = u"SIA 2024:2021 fiche 3.1, standard_values.%s" % (
            u'.'.join(chemin))
        if extrait_sia_2024 is None:
            parametres.setdefault(bloc, {})[cle] = _champ_absent(
                localisation,
                u"extrait d'autorité SIA 2024 absent du dépôt : %s"
                % SOURCE_SIA_2024.replace('\\', '/'))
            continue
        noeud = extrait_sia_2024.get('standard_values', {})
        for partie in chemin:
            noeud = (noeud or {}).get(partie) if isinstance(noeud, dict) else None
        if noeud is None:
            parametres.setdefault(bloc, {})[cle] = _champ_absent(
                localisation, u"champ absent de l'extrait d'autorité")
        else:
            parametres.setdefault(bloc, {})[cle] = {
                'valeur': noeud, 'statut': RELEVE, 'source': localisation}

    return {
        'test': 1,
        'perimetre': u'Cas diagnostiques 1A à 1D et cas 1E du Test 1',
        'statut': u'FIGÉ — chaque champ relevé dans la couche texte de sa source',
        'pourquoi': (
            u"Le cas 1E est le seul cas du Test 1 à porter un critère "
            u"pass/fail, et il n'est pas générable sans cette chaîne. "
            u"Ce référentiel ne rend pas 1E validable : il rend la question "
            u"posable."
        ),
        'sources': sources,
        'chaine': chaine,
        'parametres': parametres,
        'fenetre_entiere': _proprietes_optiques(
            textes['documentation_batiment_exemple']),
        'divergences_entre_sources': _divergences(
            textes['documentation_batiment_exemple'], parametres),
        'reserves': [
            u"Les propriétés relevées sont celles de la FENÊTRE ENTIÈRE "
            u"(EN ISO 52022-3 / EN 410), store rentré et déployé. La "
            u"documentation donne aussi les propriétés couche par couche dans "
            u"des figures ; elles ne sont PAS relevées ici.",
            u"L'usage du maillon 1D renvoie à SIA 2024:2021. Seule la "
            u"catégorie citée par la spécification est relevée ; les valeurs "
            u"de la fiche restent à lier depuis l'extrait d'autorité.",
            u"Aucun cas n'est enregistré et aucun générateur VE n'est écrit "
            u"par ce producteur.",
        ],
    }


def bilan(reference):
    u"""Compte les champs relevés et ceux à confirmer.

    Args:
        reference: Référentiel construit.

    Returns:
        tuple[int, int]: Nombre de champs relevés, nombre à confirmer.
    """
    releves = [0]
    a_confirmer = [0]

    def visiter(noeud):
        if isinstance(noeud, dict):
            statut = noeud.get('statut')
            if statut == RELEVE:
                releves[0] += 1
            elif statut == A_CONFIRMER:
                a_confirmer[0] += 1
            for valeur in noeud.values():
                visiter(valeur)
        elif isinstance(noeud, list):
            for valeur in noeud:
                visiter(valeur)

    visiter(reference)
    return releves[0], a_confirmer[0]


def main(arguments=()):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Arguments sans le nom du script. `--ecrire` fige le JSON.

    Returns:
        int: 0 si tout s'est bien passé.
    """
    reference = construire()
    releves, a_confirmer = bilan(reference)

    print(u'Chaîne 1A → 1E : %d maillon(s)' % len(reference['chaine']))
    for maillon in reference['chaine']:
        print(u'  %-3s %-28s %s'
              % (maillon['cas'], maillon['ajoute_au_precedent'],
                 maillon['statut']))
        if maillon['definition_verbatim_de']:
            print(u'      « %s »' % maillon['definition_verbatim_de'])
    print()
    for bloc in sorted(reference['parametres']):
        print(u'  %s' % bloc)
        for cle in sorted(reference['parametres'][bloc]):
            champ = reference['parametres'][bloc][cle]
            print(u'    %-26s %-12s %s'
                  % (cle, champ['statut'], champ['valeur']))
    print()
    fenetre = reference['fenetre_entiere']
    print(u'  fenêtre entière : %s' % fenetre['statut'])
    for cle_bloc in sorted(fenetre['blocs']):
        grandeurs = fenetre['blocs'][cle_bloc]['grandeurs']
        print(u'    %-40s %d grandeur(s)' % (cle_bloc, len(grandeurs)))
    print()
    print(u'  %d champ(s) relevé(s), %d à confirmer' % (releves, a_confirmer))

    if '--ecrire' in arguments:
        sortie = os.path.join(_SORTIE, 'test-1.diagnostics.ref.json')
        with io.open(sortie, 'w', encoding='utf-8') as flux:
            flux.write(json.dumps(reference, ensure_ascii=False, indent=2))
            flux.write(u'\n')
        print(u'  écrit : %s' % sortie)
    else:
        print(u'  (ajouter --ecrire pour figer le JSON)')
    return 0


if __name__ == '__main__':
    sys.exit(main(tuple(sys.argv[1:])))
