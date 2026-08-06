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
        candidats = projets.get(CLE_PROJET_CDB) or []
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

    # --- L'etape qui echoue, rejouee pour conserver son message exact.
    etape(u'constructions du cas (attendu en echec)',
          lambda: adaptateur.creer_constructions_cas(cdb, 'legere'))

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
