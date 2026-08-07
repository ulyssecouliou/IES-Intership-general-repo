# -*- coding: utf-8 -*-
u"""Enchaîne le Test 1 de bout en bout, depuis le Python Scripts navigator de VE.

Les briques existaient déjà dans `ve_adapter/test1_adapter.py` — génération des
cas, affectation de la météo, lancement d'ApacheSim, extraction — mais rien ne
les enchaînait. C'est ce que fait ce script.

DEUX MODES.

    python scripts/run_test1_dans_ve.py --preflight
        Contrôle l'installation SANS rien simuler. Exécutable hors VE.
        À lancer en premier : six simulations prennent du temps, autant
        savoir avant qu'il manque un fichier.

    python scripts/run_test1_dans_ve.py --run
        Génère, simule et extrait les six cas DRYCOLD, écrit le candidat,
        évalue et affiche le verdict. Exige une session VEScripts.

CE QUE CE SCRIPT NE FAIT PAS. Il ne traite pas les cas diagnostiques 1A à 1E :
ils exigent le climat de Zürich-Kloten (`KLO_dry_normal.PRN`), absent de toute
source en notre possession. Or **1E est le seul cas du Test 1 porteur d'un
critère pass/fail**. Ce run produit donc la comparaison chiffrée des six cas
principaux — démontrable et montrable — mais PAS le verdict formel du Test 1.
Le script le dit à chaque exécution plutôt que de le laisser croire.

DEUX AVERTISSEMENTS DU FICHIER CLIMATIQUE ISO, à ne pas manquer :

1. Son premier mois est un mois d'INITIALISATION (décembre recopié, 744 h).
   Une simulation de 8760 h partant du 1er janvier ne reproduit pas l'état
   initial des programmes de référence. L'effet est maximal sur les cas à
   forte masse — 900, 940, 900FF.
2. Il fournit l'irradiance DÉJÀ CALCULÉE sur huit surfaces nommées, sans
   décomposition global/direct/diffus. Un `.epw` livre global/direct/diffus et
   laisse VE dériver les surfaces : l'entrée n'est pas la même. D'où le
   contrôle solaire ci-dessous, à faire AVANT d'interpréter tout écart
   thermique.
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

# Les six cas principaux du Test 1, ceux qui tournent sous DRYCOLD.
CAS_DRYCOLD = ('600', '640', '900', '940', '600FF', '900FF')

# Cas diagnostiques, hors de portée sans le climat de Kloten.
CAS_KLOTEN = ('1A', '1B', '1C', '1D', '1E')

# Bibliothèque météo de VE : c'est là que le .epw doit être déposé.
DOSSIER_METEO_VE = r'C:\Program Files\IES\Shared Content\Weather'
FICHIER_METEO = 'DRYCOLD_IESVE.epw'

# Irradiation annuelle de référence sur la façade SUD, depuis le fichier
# climatique public d'EN ISO 52016-1 (colonne « SV »), figée dans
# refs/reference-data/iso-52016-1-climat-drycold.json.
IRRADIATION_SUD_REFERENCE_KWH_M2 = 1547.1

# Au-delà de cet écart relatif, le modèle de ciel de VE devient un facteur
# confondant : tout écart thermique s'expliquerait d'abord par le solaire.
TOLERANCE_SOLAIRE_RELATIVE = 0.01

CHEMIN_CANDIDAT = os.path.join(_RACINE, 'outputs', 'test1_candidat.json')


def ascii_sur(texte):
    u"""Retire les accents pour l'affichage console.

    La fenêtre de script de VEScripts n'est pas en UTF-8 : « détecté » y
    ressort en « d鐵ct遡 ». Les accents sont donc retirés à
    l'affichage — et uniquement là. Les fichiers écrits restent en UTF-8
    accentué.

    Args:
        texte: Texte à afficher.

    Returns:
        str: Le même texte, sans caractère non-ASCII.
    """
    import unicodedata
    decompose = unicodedata.normalize('NFKD', u'%s' % texte)
    return decompose.encode('ascii', 'ignore').decode('ascii')


def dire(texte=u''):
    u"""Affiche une ligne lisible dans la console de VEScripts.

    Args:
        texte: Texte à afficher.
    """
    print(ascii_sur(texte))


#: Nombre maximal d'éléments conservés d'une séquence dans le rapport. Assez
#: haut pour ne rien perdre d'un `dir()` : c'est justement la partie tronquée
#: qui contient d'ordinaire le nom qu'on cherche.
LIMITE_ELEMENTS = 500


def _serialisable(valeur, profondeur=0):
    u"""Convertit une valeur quelconque en structure sérialisable en JSON.

    Ne lève jamais : un objet exotique de l'API `iesve` est réduit à son
    `repr`, jamais escamoté.

    Args:
        valeur: Valeur à convertir.
        profondeur: Profondeur de récursion courante.

    Returns:
        Any: Structure faite de types JSON.
    """
    if valeur is None or isinstance(valeur, (bool, int, float)):
        return valeur
    if isinstance(valeur, str):
        return valeur
    if profondeur >= 3:
        return repr(valeur)[:400]
    if isinstance(valeur, (list, tuple, set)):
        elements = list(valeur)[:LIMITE_ELEMENTS]
        return [_serialisable(e, profondeur + 1) for e in elements]
    if isinstance(valeur, dict):
        return dict(
            ('%s' % cle, _serialisable(val, profondeur + 1))
            for cle, val in list(valeur.items())[:LIMITE_ELEMENTS]
        )
    return repr(valeur)[:400]


def _membres(objet):
    u"""Noms publics exposés par un objet, liste COMPLÈTE.

    Args:
        objet: Objet à inspecter.

    Returns:
        list[str]: Noms triés, sans les membres privés.
    """
    try:
        return sorted(nom for nom in dir(objet) if not nom.startswith('_'))
    except Exception as erreur:  # noqa: BLE001
        return ['<dir() a echoue : %s>' % erreur]


#: Clé sous laquelle `VECdbDatabase.get_projects()` range les projets. Les deux
#: autres (« system », « manufacturer ») sont des bibliothèques fournies, pas le
#: projet ouvert.
#:
#: ATTENTION, ce n'est PAS une chaîne. Les clés sont des membres de
#: `iesve.project_types`, et le rapport de sonde du 2026-08-07 l'a montré :
#:
#:     {iesve.project_types.project: [<VECdbProject>], ...}
#:
#: Sérialisées en JSON elles ressortent en « project », ce qui donne
#: l'illusion d'un dictionnaire à clés textuelles. La comparaison se fait donc
#: sur la forme textuelle de la clé, pas sur la clé elle-même.
CLE_PROJET_CDB = 'project'


def _premier_projet_cdb(projets):
    u"""Extrait un `VECdbProject` de ce que renvoie `get_projects()`.

    POURQUOI CETTE FONCTION. La sonde v2 faisait `projets[0]` et a introspecté
    une **liste** : elle a donc rapporté `['append', 'clear', 'copy', 'count',
    'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort']` comme
    étant les attributs de `VECdbProject`. `get_projects()` renvoie en réalité
    un dictionnaire `{'project': [...], 'system': [...], 'manufacturer':
    [...]}`.

    Le piège est qu'un dictionnaire est vrai, itérable et indexable : rien
    n'échoue, et le rapport paraît valide. Seule la lecture des attributs
    relevés a révélé l'erreur.

    Args:
        projets: Valeur renvoyée par `get_projects()`, ou `None` si l'étape a
            échoué.

    Returns:
        Le premier projet, ou `None` si l'on n'en trouve aucun. Jamais un objet
        d'un autre type : mieux vaut une étape en échec qu'un relevé faux.
    """
    if not projets:
        return None
    if isinstance(projets, dict):
        candidats = _valeur_par_cle_textuelle(projets, CLE_PROJET_CDB)
    else:
        # Forme inattendue : on l'accepte plutôt que d'échouer, mais sans
        # supposer qu'elle contient des projets — le contrôle de type ci-dessous
        # tranche.
        candidats = projets
    for candidat in candidats:
        # Une liste ou une chaîne à cette place signale qu'on s'est encore
        # trompé de niveau : ne pas l'introspecter.
        if not isinstance(candidat, (list, tuple, dict)) and not _est_texte(candidat):
            return candidat
    return None


def _valeur_par_cle_textuelle(table, nom):
    u"""Cherche une entrée par la forme TEXTUELLE de sa clé.

    `get_projects()` indexe par membres de `iesve.project_types`, pas par
    chaînes. Un `table.get('project')` échoue donc silencieusement et rend une
    liste vide — ce qui se lit comme « aucun projet » alors qu'il y en a un.

    Args:
        table: Dictionnaire dont les clés peuvent être des énumérés.
        nom: Nom cherché, sous sa forme textuelle.

    Returns:
        list: Valeur associée, ou liste vide si la clé est absente.
    """
    for cle, valeur in table.items():
        if cle == nom or u'%s' % (cle,) == nom or getattr(cle, 'name', None) == nom:
            return valeur or []
    return []


def _est_texte(valeur):
    u"""Vrai si la valeur est une chaîne, sur Python 2 comme sur Python 3.

    Args:
        valeur: Valeur à tester.

    Returns:
        bool: Vrai pour une chaîne de caractères ou d'octets.
    """
    try:
        types_texte = (str, unicode, bytes)  # noqa: F821 -- Python 2
    except NameError:
        types_texte = (str, bytes)
    return isinstance(valeur, types_texte)


#: Échelle croissante essayée pour l'isolant idéal. Zéro d'abord, puisque
#: c'est ce que donne ISO 52016-1 ; puis des valeurs de plus en plus grandes
#: jusqu'à ce que VE en restitue une à l'identique.
ECHELLE_MINIMUM = (0.0, 0.001, 0.01, 0.1, 1.0, 10.0)

#: Tolérance de relecture. VE stocke en flottant 32 bits.
TOLERANCE_RELECTURE = 1e-6


def _proprietes_des_couches(construction):
    u"""Relit les couches d'une construction et leurs propriétés.

    Sert à répondre à une question précise : `add_layer` n'écrit aucune
    épaisseur, et l'épaisseur n'existe pas au niveau matériau. Les couches
    portent-elles donc les bonnes valeurs, ou celles que VE leur donne par
    défaut ?

    Args:
        construction: `VECdbConstruction` construite.

    Returns:
        list: Une entrée par couche, ou une description de l'échec.
    """
    releves = []
    try:
        couches = list(construction.get_layers() or [])
    except Exception as erreur:  # noqa: BLE001
        return {'get_layers_a_echoue': u'%s: %s' % (type(erreur).__name__,
                                                    erreur)}
    for rang, couche in enumerate(couches):
        entree = {'rang': rang, 'attributs': _membres(couche)}
        try:
            entree['proprietes'] = couche.get_properties()
        except Exception as erreur:  # noqa: BLE001
            entree['proprietes'] = u'%s: %s' % (type(erreur).__name__, erreur)
        releves.append(entree)
    return releves


def _signature(methode):
    u"""Décrit une méthode : docstring et signature si elle en expose une.

    Les méthodes natives de `iesve` n'exposent d'ordinaire pas de signature
    introspectable ; leur docstring, elle, porte la liste des paramètres.
    C'est ainsi qu'ont été relevés les setters de `VEApacheSystem`.

    Args:
        methode: Méthode ou fonction.

    Returns:
        dict: Ce qui a pu être relevé.
    """
    import inspect
    releve = {'doc': (getattr(methode, '__doc__', None) or u'')[:400]}
    try:
        releve['signature'] = u'%s' % (inspect.signature(methode),)
    except (TypeError, ValueError) as erreur:
        releve['signature'] = u'non exposee (%s)' % type(erreur).__name__
    return releve


def _signature_dimport(module_iesve):
    u"""Relève ce qu'attend l'importeur gbXML.

    La documentation annonce `Import_file(file_name, heal_geometry, cap_mode,
    cap_height)` avec un I majuscule ; l'introspection donne `import_file`.
    Elle s'est donc déjà trompée une fois : on relève la docstring réelle
    plutôt que de la croire sur le reste.

    Args:
        module_iesve: Module `iesve`.

    Returns:
        dict: Ce qui a pu être relevé sur les deux orthographes.
    """
    releve = {}
    importeur = getattr(module_iesve, 'ImportGBXML', None)
    if importeur is None:
        return {'ImportGBXML': u'absent du module'}
    releve['membres'] = _membres(importeur)
    for orthographe in ('import_file', 'Import_file'):
        methode = getattr(importeur, orthographe, None)
        releve[orthographe] = (u'absent' if methode is None
                               else _signature(methode))
    return releve


def _corps_du_modele(projet):
    u"""Relève les corps du modèle courant et leurs surfaces.

    C'est à ces surfaces que l'on comparera celles d'un gbXML importé. Sans ce
    relevé, un import « réussi » ne prouverait rien : c'est exactement le
    piège des épaisseurs à 1 mm.

    Args:
        projet: `VEProject` courant.

    Returns:
        list | dict: Un relevé par corps, ou la description de l'échec.
    """
    try:
        modeles = list(projet.models or [])
    except Exception as erreur:  # noqa: BLE001
        return {'models_a_echoue': u'%s: %s' % (type(erreur).__name__, erreur)}
    if not modeles:
        return {'aucun_modele': True}

    releves = []
    for modele in modeles[:2]:
        entree = {'model_type': u'%s' % getattr(modele, 'model_type', None)}
        try:
            corps = list(modele.get_bodies(False) or [])
        except Exception as erreur:  # noqa: BLE001
            entree['get_bodies_a_echoue'] = u'%s: %s' % (
                type(erreur).__name__, erreur)
            releves.append(entree)
            continue
        entree['nb_corps'] = len(corps)
        entree['corps'] = []
        for objet in corps[:6]:
            detail = {'id': u'%s' % getattr(objet, 'id', None),
                      'nom': u'%s' % getattr(objet, 'name', None),
                      'type': u'%s' % getattr(objet, 'type', None)}
            for appel in ('get_areas', 'get_room_data'):
                try:
                    detail[appel] = _serialisable(getattr(objet, appel)())
                except Exception as erreur:  # noqa: BLE001
                    detail[appel] = u'%s: %s' % (type(erreur).__name__, erreur)
            entree['corps'].append(detail)
        releves.append(entree)
    return releves


def _supprimer_materiaux(projet_cdb, identifiants):
    u"""Supprime les matériaux d'essai créés par la sonde.

    POURQUOI. Chaque passage créait des matériaux et n'en supprimait aucun :
    sept runs ont laissé **76 matériaux** dans la base de constructions du
    projet de l'utilisateur. Une sonde en lecture doit rendre le modèle tel
    qu'elle l'a trouvé ; ceux-ci n'ont aucune raison d'y rester.

    Les matériaux des CONSTRUCTIONS ne sont pas concernés : ils sont
    légitimement utilisés par les parois créées.

    Args:
        projet_cdb: `VECdbProject` ouvert.
        identifiants: Identifiants à supprimer.

    Returns:
        dict: Ce qui a été supprimé, et ce qui a résisté.
    """
    supprimes, echecs = [], {}
    for identifiant in identifiants:
        if not identifiant:
            continue
        try:
            projet_cdb.delete_material(identifiant)
            supprimes.append(identifiant)
        except Exception as erreur:  # noqa: BLE001 -- un refus est un resultat
            echecs[identifiant] = u'%s: %s' % (type(erreur).__name__, erreur)
    return {'supprimes': supprimes, 'echecs': echecs}


def _echelle_de_minimum(projet_cdb, module_iesve):
    u"""Relève la plus petite masse volumique que VE accepte de conserver.

    Écrit chaque valeur de `ECHELLE_MINIMUM` sur un matériau d'essai, relit, et
    consigne le couple écrit/relu. Aucune conclusion n'est tirée ici : le
    rapport donne les couples, et c'est leur lecture qui tranche.

    Args:
        projet_cdb: `VECdbProject` ouvert.
        module_iesve: Module `iesve`.

    Returns:
        list[dict]: Un relevé par valeur essayée.
    """
    categorie = _membre_enum(module_iesve, 'material_categories', 'other')
    releves = []
    for valeur in ECHELLE_MINIMUM:
        essai = {'ecrit': valeur}
        try:
            materiau = projet_cdb.create_material(categorie)
            materiau.set_properties({'conductivity': 0.04,
                                     'density': valeur,
                                     'specific_heat_capacity': valeur})
            proprietes = materiau.get_properties() or {}
            essai['density_relu'] = proprietes.get('density')
            essai['cp_relu'] = proprietes.get('specific_heat_capacity')
            essai['conserve'] = _proche(essai['density_relu'], valeur)
            essai['id'] = proprietes.get('id')
        except Exception as erreur:  # noqa: BLE001 -- un refus est un resultat
            essai['erreur'] = u'%s: %s' % (type(erreur).__name__, erreur)
            essai['conserve'] = False
        releves.append(essai)
    return releves


def _proche(obtenu, attendu):
    u"""Compare deux flottants avec la tolérance de relecture.

    Args:
        obtenu: Valeur relue.
        attendu: Valeur écrite.

    Returns:
        bool: Vrai si les deux coïncident.
    """
    if obtenu is None:
        return False
    reference = abs(attendu) if attendu else 1.0
    return abs(obtenu - attendu) <= TOLERANCE_RELECTURE * reference


def _membre_enum(module, nom_enum, nom_membre):
    u"""Membre d'un énuméré du module `iesve`, résolu sans supposer.

    Args:
        module: Module `iesve`.
        nom_enum: Nom de l'énuméré, par exemple `'material_categories'`.
        nom_membre: Nom du membre, par exemple `'other'`.

    Returns:
        Le membre.

    Raises:
        RuntimeError: Si l'énuméré ou le membre manque — auquel cas c'est
            l'API qui a changé, et le dire vaut mieux que de retomber sur une
            valeur par défaut.
    """
    enum = getattr(module, nom_enum, None)
    if enum is None:
        raise RuntimeError(u'enum %r absent du module iesve' % nom_enum)
    membre = getattr(enum, nom_membre, None)
    if membre is None:
        raise RuntimeError(
            u'membre %r absent de %r' % (nom_membre, nom_enum))
    return membre


def _echouer(message):
    u"""Fait échouer une étape volontairement, avec un message explicite.

    Une étape absente du rapport est une information perdue ; une étape en
    échec explique pourquoi elle n'a pas pu être faite.

    Args:
        message: Motif de l'échec.

    Raises:
        RuntimeError: Toujours.
    """
    raise RuntimeError(message)


def _enums(objet):
    u"""Membres de type énuméré exposés par un objet, avec leurs valeurs.

    Dans l'API `iesve`, les catégories d'élément et classes de construction
    sont portées par des classes dont les attributs publics sont des entiers.
    C'est précisément ce que cherche `creer_constructions_cas`, et c'est ce
    qui a changé de nom depuis VE 2023.

    Args:
        objet: Objet ou module à inspecter.

    Returns:
        dict: `{nom de l'enum: {membre: valeur}}`, vide si aucun.
    """
    import types

    trouves = {}
    for nom in _membres(objet):
        try:
            candidat = getattr(objet, nom)
        except Exception:  # noqa: BLE001 -- certains attributs lèvent à la lecture
            continue
        # Restreint aux CLASSES et MODULES : sans ce filtre, un simple entier
        # produit un faux énuméré via ses attributs `numerator`, `real`, etc.,
        # et le rapport se remplit de bruit qui masque les vrais.
        if not isinstance(candidat, (type, types.ModuleType)):
            continue
        membres = {}
        for sous_nom in dir(candidat):
            if sous_nom.startswith('_'):
                continue
            try:
                valeur = getattr(candidat, sous_nom)
            except Exception:  # noqa: BLE001
                continue
            if isinstance(valeur, int) and not isinstance(valeur, bool):
                membres[sous_nom] = valeur
        if membres:
            trouves[nom] = membres
    return trouves


def _ok(libelle, detail=''):
    dire(u'  [OK]   %-42s %s' % (libelle, detail))
    return True


def _ko(libelle, detail=''):
    dire(u'  [MANQUE] %-40s %s' % (libelle, detail))
    return False


def preflight():
    u"""Contrôle l'installation sans rien simuler.

    Returns:
        bool: Vrai si un run est possible. Faux si un prérequis manque.
    """
    dire(u'=== PRÉFLIGHT Test 1 ===')
    controles = []

    # 1. Référence figée
    try:
        from engine import test1_engine as moteur
        reference = moteur.charger_reference()
        nb = len(reference.get('reference_values', {}))
        controles.append(_ok(u'référence Test 1 chargée', u'%d grandeurs' % nb))
    except Exception as erreur:
        controles.append(_ko(u'référence Test 1', str(erreur)[:60]))
        reference = None

    # 2. Fichier météo déployé dans VE
    chemin_meteo = os.path.join(DOSSIER_METEO_VE, FICHIER_METEO)
    if os.path.isfile(chemin_meteo):
        controles.append(_ok(u'météo DRYCOLD déployée',
                             u'%d octets' % os.path.getsize(chemin_meteo)))
    else:
        controles.append(_ko(u'météo DRYCOLD', chemin_meteo))

    # 3. Adaptateur importable
    try:
        from ve_adapter import test1_adapter  # noqa: F401
        controles.append(_ok(u'adaptateur Test 1 importable'))
    except Exception as erreur:
        controles.append(_ko(u'adaptateur Test 1', str(erreur)[:60]))

    # 4. Session VE ?
    dans_ve = _dans_ve()
    if dans_ve:
        controles.append(_ok(u'session VEScripts détectée'))
    else:
        dire(u'  [INFO] hors VEScripts — le préflight est complet, '
              u'mais --run exigera VE.')

    # 5. Dossier de sortie
    dossier = os.path.dirname(CHEMIN_CANDIDAT)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    controles.append(_ok(u'dossier de sortie', dossier))

    dire()
    dire(u'  cas simulables sous DRYCOLD : %s' % u', '.join(CAS_DRYCOLD))
    dire(u'  cas EXCLUS (climat Kloten absent) : %s' % u', '.join(CAS_KLOTEN))
    dire(u'  ⚠ 1E est le seul cas porteur du critère pass/fail du Test 1.')
    dire(u'    Ce run produit une DÉMONSTRATION chiffrée, pas le verdict SIA.')
    dire()

    pret = all(controles)
    dire(u'=> %s' % (u'prêt pour --run' if pret
                      else u'PRÉREQUIS MANQUANT, --run refusé'))
    return pret


def _dans_ve():
    u"""Indique si le module `iesve` est disponible.

    Returns:
        bool: Vrai en session VEScripts.
    """
    try:
        import iesve  # noqa: F401
        return True
    except ImportError:
        return False


def controler_solaire(irradiation_sud_calculee):
    u"""Compare l'irradiation sud de VE à la référence ISO.

    À faire AVANT d'interpréter tout écart thermique : le fichier ISO fournit
    l'irradiance de surface déjà calculée, alors que VE la dérive du global.
    Un écart ici expliquerait des divergences qu'on attribuerait sinon, à tort,
    au moteur thermique.

    Args:
        irradiation_sud_calculee: Irradiation annuelle incidente sur la façade
            sud relevée dans VE, en kWh/m2.

    Returns:
        dict: Écart absolu, relatif, et verdict du contrôle.
    """
    ecart = irradiation_sud_calculee - IRRADIATION_SUD_REFERENCE_KWH_M2
    relatif = ecart / IRRADIATION_SUD_REFERENCE_KWH_M2
    return {
        'reference_kwh_m2': IRRADIATION_SUD_REFERENCE_KWH_M2,
        'calculee_kwh_m2': irradiation_sud_calculee,
        'ecart_kwh_m2': ecart,
        'ecart_relatif': relatif,
        'modele_de_ciel_neutre': abs(relatif) <= TOLERANCE_SOLAIRE_RELATIVE,
        'interpretation': (
            u'modèle de ciel neutre : un écart thermique viendra du moteur'
            if abs(relatif) <= TOLERANCE_SOLAIRE_RELATIVE else
            u'ATTENTION : le modèle de ciel est un facteur confondant ; '
            u'expliquer tout écart thermique par le solaire AVANT le moteur'
        ),
    }


def executer():
    u"""Génère, simule et extrait les six cas DRYCOLD.

    Returns:
        dict: Candidat extrait, prêt pour `evaluer_test1`.

    Raises:
        RuntimeError: Hors session VEScripts, ou si un prérequis manque.
    """
    if not _dans_ve():
        raise RuntimeError(
            u'`iesve` indisponible : --run doit s\'exécuter depuis le Python '
            u'Scripts navigator de VE. Utiliser --preflight hors VE.')
    if not preflight():
        raise RuntimeError(u'préflight en échec : run refusé.')

    raise NotImplementedError(
        u"L'enchaînement génération -> simulation -> extraction n'a jamais été "
        u"exécuté dans une VE réelle. Les briques existent dans "
        u"ve_adapter/test1_adapter.py (generer_cas_test1, "
        u"assigner_meteo_drycold, lancer_apachesim_cas, extraire_candidat_test1) "
        u"mais leur enchaînement doit être déroulé une première fois à la main, "
        u"cas par cas, pour relever les noms d'objets réels. Les câbler ici "
        u"sans cette étape produirait un script qui échoue au premier appel, en "
        u"donnant l'illusion d'être prêt.")


def sonder(cas_id='600'):
    u"""Déroule UN cas pas à pas dans VE, en capturant ce que l'API renvoie.

    C'est le run à faire en premier dans une VE réelle. Il n'essaie pas de
    réussir : il essaie d'APPRENDRE. Chaque étape est tentée isolément, son
    résultat ou son erreur est consigné, et le rapport permet ensuite de câbler
    l'enchaînement complet sans deviner un seul nom d'objet.

    Args:
        cas_id: Cas à sonder. « 600 » est le plus simple des six.

    Returns:
        dict: Rapport de sonde, écrit aussi sur disque.
    """
    rapport = {
        'cas': cas_id,
        'dans_ve': _dans_ve(),
        'etapes': [],
        'avertissement': (
            u"Rapport de SONDE. Aucune valeur ici n'est un résultat de "
            u"validation : ce fichier sert uniquement à relever les noms "
            u"d'objets et signatures réels de l'API iesve."
        ),
    }

    def etape(nom, fonction):
        u"""Exécute une étape en capturant son issue INTÉGRALE.

        Le rapport ne tronque rien : c'est précisément la partie coupée d'une
        liste d'attributs qui contient le nom qu'on cherche.

        Args:
            nom: Libellé de l'étape.
            fonction: Appelable sans argument.

        Returns:
            Any: Le résultat, ou `None` en cas d'échec.
        """
        try:
            valeur = fonction()
        except Exception as erreur:  # noqa: BLE001 -- on consigne, on ne masque pas
            rapport['etapes'].append({
                'nom': nom, 'statut': 'ECHEC',
                'type_erreur': type(erreur).__name__,
                'erreur': u'%s' % erreur,
            })
            dire(u'  [ECHEC] %-38s %s' % (nom, type(erreur).__name__))
            return None
        rapport['etapes'].append({
            'nom': nom, 'statut': 'OK',
            'type': type(valeur).__name__,
            'valeur': _serialisable(valeur),
        })
        dire(u'  [OK]    %-38s %s' % (nom, repr(valeur)[:56]))
        return valeur

    dire(u'=== SONDE Test 1, cas %s ===' % cas_id)
    if not rapport['dans_ve']:
        dire(u'  hors VEScripts : la sonde ne peut rien apprendre ici.')
        return rapport

    import iesve
    from ve_adapter import test1_adapter as adaptateur

    # Identifiants des materiaux D ESSAI, a supprimer en fin de sonde. Ceux
    # des constructions n en font pas partie : les parois s en servent.
    jetables = []

    # --- Projet et modèle -------------------------------------------------
    projet = etape(u'projet courant', lambda: iesve.VEProject.get_current_project())
    etape(u'modeles du projet', lambda: projet.models)
    etape(u'attributs du projet', lambda: _membres(projet))

    # --- Base de constructions : VECdbDatabase n'a que 3 methodes, la vraie
    # --- porte d'entree est get_projects() -> VECdbProject.
    cdb = etape(u'base de constructions',
                lambda: iesve.VECdbDatabase.get_current_database())
    etape(u'attributs de la base', lambda: _membres(cdb))
    projets_cdb = etape(u'projets de la base', lambda: cdb.get_projects())
    projet_cdb = _premier_projet_cdb(projets_cdb)
    if projet_cdb is not None:
        etape(u'attributs de VECdbProject', lambda: _membres(projet_cdb))
        etape(u'enums de VECdbProject', lambda: _enums(projet_cdb))
    else:
        etape(u'attributs de VECdbProject',
              lambda: _echouer(u'aucun projet dans %r' % (projets_cdb,)))

    # --- Enums du module iesve : c'est la que se trouvent tres probablement
    # --- les categories d'element et classes de construction.
    etape(u'classes du module iesve', lambda: _membres(iesve))
    etape(u'enums du module iesve', lambda: _enums(iesve))

    # --- Meteo : deja concluant au premier passage, on le rejoue pour la trace.
    etape(u'affectation meteo DRYCOLD',
          lambda: adaptateur.assigner_meteo_drycold(
              os.path.join(DOSSIER_METEO_VE, FICHIER_METEO)))

    # --- Proprietes d un materiau : les CLES acceptees, pas celles supposees.
    #
    # Le 2026-08-07, `set_properties({'description': 'plasterboard', ...})` a
    # repondu « could not convert string to float: 'plasterboard' » : VE tente
    # de convertir TOUTES les valeurs en flottant, donc `description` n est pas
    # une cle acceptee — ou pas sous ce nom. En essayer d autres a l aveugle
    # serait la cinquieme fois qu on devine ; on releve.
    if projet_cdb is not None:
        materiau = etape(
            u'create_material (materiau d essai)',
            lambda: projet_cdb.create_material(
                _membre_enum(iesve, 'material_categories', 'other')))
        if materiau is not None:
            jetables.append((materiau.get_properties() or {}).get('id'))
            etape(u'attributs du materiau', lambda: _membres(materiau))
            etape(u'get_properties() : LES CLES ACCEPTEES',
                  lambda: materiau.get_properties())
            # Ecriture des seules valeurs numeriques : si elle passe, la cle
            # fautive etait bien `description`.
            etape(u'set_properties sans description (essai)',
                  lambda: materiau.set_properties({
                      'conductivity': 0.16, 'thickness': 0.012,
                      'density': 950.0, 'specific_heat_capacity': 840.0}))
            etape(u'get_properties() apres ecriture',
                  lambda: materiau.get_properties())

    # --- Minimum de masse accepte par VE, pour l isolant IDEAL du plancher.
    #
    # ISO 52016-1 Table 23 donne 0 de masse volumique et 0 de chaleur
    # massique ; ASHRAE 140 note (a) impose « le minimum que le logiciel teste
    # autorise, mais pas < 0 ». La valeur est donc dependante du logiciel PAR
    # CONSTRUCTION de la norme : elle se releve, elle ne se choisit pas.
    #
    # On ecrit une echelle croissante et on RELIT : la premiere valeur que VE
    # restitue a l identique est le minimum accepte.
    if projet_cdb is not None:
        essais = etape(u'minimum de masse accepte par VE',
                       lambda: _echelle_de_minimum(projet_cdb, iesve))
        for essai in (essais or []):
            jetables.append(essai.get('id'))

    # --- Creation des constructions.
    #
    # CORRIGE le 2026-08-07 : la sonde passait `cdb`, la BASE, alors que
    # `creer_constructions_cas` attend un `VECdbProject`. VE repondait
    # « 'VECdbDatabase' object has no attribute 'create_construction' » —
    # meme classe d erreur que les enums cherches sur le mauvais conteneur.
    constructions = None
    if projet_cdb is not None:
        constructions = etape(
            u'constructions du cas',
            lambda: adaptateur.creer_constructions_cas(projet_cdb, 'legere'))

    # --- LES EPAISSEURS SONT-ELLES POSEES ?
    #
    # `add_layer(materiau_id, False)` cree la couche mais n ecrit AUCUNE
    # epaisseur — et depuis le 2026-08-07 l epaisseur n est plus sur le
    # materiau non plus, puisque `thickness` n y existe pas. Les couches
    # portent donc ce que VE leur donne par defaut.
    #
    # Une construction qui se cree sans lever, avec des epaisseurs fausses,
    # produirait des U credibles et faux. On relit.
    if constructions:
        etape(u'couches du mur : epaisseurs REELLES',
              lambda: _proprietes_des_couches(constructions['mur']))

    # --- GEOMETRIE : ce que l importeur attend, et ce que le modele contient.
    #
    # L API n expose AUCUN constructeur de geometrie : la seule voie est
    # `ImportGBXML.import_file`. Sa signature n a jamais ete observee. La
    # documentation annonce `Import_file(file_name, heal_geometry, cap_mode,
    # cap_height)` — mais elle se trompe deja sur la casse, l introspection
    # donnant `import_file`. On releve donc avant d ecrire un gbXML contre une
    # signature supposee.
    etape(u'ImportGBXML : signature',
          lambda: _signature_dimport(iesve))

    # Et ce que le modele porte DEJA : s il contient une geometrie, ses
    # surfaces se lisent, et c est a elles qu on comparera l import.
    etape(u'corps du modele courant',
          lambda: _corps_du_modele(projet))

    # --- Menage. Une sonde doit rendre le modele tel qu elle l a trouve.
    if projet_cdb is not None and jetables:
        etape(u'suppression des materiaux d essai',
              lambda: _supprimer_materiaux(projet_cdb, jetables))
    else:
        etape(u'constructions du cas',
              lambda: _echouer(u'aucun VECdbProject : etape impossible'))

    chemin = os.path.join(_RACINE, 'outputs', 'sonde_test1_%s.json' % cas_id)
    if not os.path.isdir(os.path.dirname(chemin)):
        os.makedirs(os.path.dirname(chemin))
    with io.open(chemin, 'w', encoding='utf-8') as flux:
        flux.write(json.dumps(rapport, ensure_ascii=False, indent=2))
    dire()
    dire(u'rapport de sonde : %s' % chemin)
    dire(u'-> me renvoyer ce fichier : il contient ce qu\'il me manque pour '
          u'câbler l\'enchaînement sans deviner.')
    return rapport


def evaluer_et_afficher(candidat=None):
    u"""Évalue un candidat et affiche le tableau des écarts.

    Args:
        candidat: Candidat déjà extrait. Si `None`, tente de relire
            `outputs/test1_candidat.json` ; à défaut, évalue sans candidat
            (tout gris).

    Returns:
        dict: Résultat de `evaluer_test1`.
    """
    from engine import test1_engine as moteur

    if candidat is None and os.path.isfile(CHEMIN_CANDIDAT):
        with io.open(CHEMIN_CANDIDAT, encoding='utf-8') as flux:
            candidat = json.load(flux)
            dire(u'candidat relu : %s' % CHEMIN_CANDIDAT)

    if candidat is None:
        dire(u'aucun candidat : état « avant première simulation », tout gris.')

    resultat = moteur.evaluer_test1(moteur.charger_reference(), candidat)
    verdict = resultat.get('verdict_test1') or {}
    conforme = verdict.get('conforme')
    libelle = {True: u'CONFORME', False: u'NON CONFORME'}.get(
        conforme, u'NON ÉVALUÉ')
    dire()
    dire(u'verdict Test 1 : %s' % libelle)
    if verdict.get('motif'):
        dire(u'  motif : %s' % verdict['motif'])
    dire(u'  périodes 1E non évaluées : %s / %s'
          % (verdict.get('nb_periodes_non_evaluees'),
             verdict.get('nb_periodes_totales')))
    dire(u'  rappel : le verdict du Test 1 porte sur le SEUL cas 1E, qui '
          u'exige le climat de Kloten. Les six cas DRYCOLD sont comparés à '
          u'titre démonstratif, sans critère de déviation.')
    return resultat


# --------------------------------------------------------------------------
# MODE D'EXÉCUTION
#
# Le Python Scripts navigator de VE n'offre PAS de terminal : il n'y a qu'un
# bouton « Run », donc aucun moyen de passer `--sonde`. Le mode est donc
# déterminé automatiquement :
#
#     dans VE   -> SONDE     (la seule action qui apprenne quelque chose)
#     hors VE   -> PREFLIGHT (contrôle d'installation, sans rien simuler)
#
# Pour forcer un mode depuis VE, remplacer 'auto' ci-dessous par 'preflight',
# 'sonde', 'evaluer' ou 'run', puis appuyer sur Run. C'est le seul réglage à
# modifier ; aucune autre ligne du fichier n'a besoin d'être touchée.
# --------------------------------------------------------------------------
MODE = 'auto'

MODES_CONNUS = ('auto', 'preflight', 'sonde', 'evaluer', 'run')


def _mode_effectif(arguments):
    u"""Détermine le mode à exécuter.

    Les arguments de ligne de commande priment quand il y en a — pour ceux qui
    disposent d'un terminal. Sinon on retombe sur `MODE`, puis sur la
    détection automatique.

    Args:
        arguments: Arguments de la ligne de commande, sans le nom du script.

    Returns:
        str: Un mode parmi 'preflight', 'sonde', 'evaluer', 'run'.
    """
    for nom in ('run', 'sonde', 'evaluer', 'preflight'):
        if '--' + nom in arguments:
            return nom

    if MODE in MODES_CONNUS and MODE != 'auto':
        return MODE

    return 'sonde' if _dans_ve() else 'preflight'


def main(arguments=()):
    u"""Point d'entrée, utilisable au clavier comme au bouton Run.

    Args:
        arguments: Arguments de la ligne de commande, sans le nom du script.
            Vide quand le script est lancé depuis le bouton Run de VE.

    Returns:
        int: Code de sortie, 0 si tout s'est bien passé.
    """
    mode = _mode_effectif(arguments)
    dire(u'mode : %s%s' % (mode, u'  (détecté automatiquement)'
                            if not arguments and MODE == 'auto' else u''))
    dire()

    if mode == 'sonde':
        rapport = sonder()
        return 0 if rapport['dans_ve'] else 1

    if mode == 'evaluer':
        evaluer_et_afficher()
        return 0

    if mode == 'preflight':
        return 0 if preflight() else 1

    if mode == 'run':
        try:
            candidat = executer()
        except (RuntimeError, NotImplementedError) as erreur:
            dire(u'RUN IMPOSSIBLE : %s' % erreur)
            return 1
        with io.open(CHEMIN_CANDIDAT, 'w', encoding='utf-8') as flux:
            flux.write(json.dumps(candidat, ensure_ascii=False, indent=2))
        dire(u'candidat écrit : %s' % CHEMIN_CANDIDAT)
        evaluer_et_afficher(candidat)
        return 0

    dire(u'mode inconnu : %r — modes valides : %s'
          % (mode, u', '.join(MODES_CONNUS)))
    return 1


if __name__ == '__main__':
    # `sys.argv` peut être absent ou réduit quand VEScripts exécute le fichier
    # depuis son bouton Run : on ne suppose rien.
    _arguments = tuple(getattr(sys, 'argv', ())[1:])
    _code = main(_arguments)

    dire()
    dire(u'--- terminé (code %d) ---' % _code)

    # `sys.exit` lève SystemExit, que VEScripts remonte comme une erreur dans
    # sa fenêtre de script. On ne sort donc explicitement que lorsqu'un
    # terminal est manifestement présent (des arguments ont été passés).
    if _arguments:
        sys.exit(_code)
