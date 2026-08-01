# -*- coding: utf-8 -*-
"""Export Excel -- remplissage du classeur SIA officiel par COM (Pywin32),
mode `Handeingabe` (docs/ADR-001-architecture-MSP.md §4).

--------------------------------------------------------------------------
STATUT D'EXÉCUTION -- À LIRE AVANT DE FAIRE CONFIANCE À CE MODULE
--------------------------------------------------------------------------
`pywin32` a pu être installé et **Excel (Office16) est réellement présent**
sur cette machine de développement (`reg query
"HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\EXCEL.EXE"`).
`ui/tests/test_export_excel_com.py` pilote donc un **vrai** processus Excel
via COM contre un classeur jetable créé pour le test (jamais un fichier de
`SIA_4010_geteilter_Link/`) : ouverture, écriture de cellules, relecture de
vérification, sauvegarde, fermeture -- ce test est marqué
`pytest.mark.skipif` si `win32com` est indisponible sur la machine qui
exécute la suite, pour ne jamais faire échouer la collecte ailleurs.

**Ce que ce test NE prouve PAS** :
1. Le comportement sur le **vrai** classeur SIA
   (`Resultaterfassung_Test1.xlsx`, feuille `Daten_Testprogramm`) : la
   présence réelle d'une feuille de ce nom, de la cellule `H3`, et des
   colonnes `J:N` de la zone Handeingabe (ADR-001 §4) n'a pas pu être
   vérifiée ici -- ces fichiers ne sont pas dans `/refs` de ce dépôt de
   développement (130 Mo, cf. ADR-001 §7 bis). Testé uniquement contre un
   classeur jetable qui REPRODUIT la structure minimale décrite par l'ADR
   (une feuille nommée `Daten_Testprogramm`, cellule `H3`).
2. Le comportement en environnement VEScripts réel (Python embarqué, Pywin32
   219 -- ADR-001 §2, version non confirmée dans cet environnement Python
   3.13 / pywin32 le plus récent disponible via pip).
3. **La carte cellule <-> (grandeur, cas, période)** : AUCUNE adresse de
   cellule Handeingabe (colonnes `J:N` de `Daten_Testprogramm`) n'est
   codée en dur ici. ADR-001 §5 renvoie cette carte à un descripteur futur
   (`refs/reference-data/testN.map.json`), qui n'existe pas encore. Ce
   module REFUSE explicitement de deviner une adresse : `carte_cellules`
   doit être fourni par l'appelant, sinon `remplir_classeur_sia` lève une
   erreur précise plutôt que d'écrire au hasard dans le classeur.

Ce module ne recalcule ni n'invente aucune valeur : il écrit exactement
`ligne['valeur_candidate']`, tel que déjà produit par
`engine/test1_engine.py::evaluer_test1()` et transmis sans changement par
`ui/verdict_view.py`.
"""

import shutil


# Cellule confirmée par ADR-001 §4 (preuve citée : formule
# `B16 = IF(Daten_Testprogramm!$H$3="Handeingabe"; ...)`, feuille
# `Zusammenfassung Testfälle`) -- LA SEULE adresse de cellule que ce module
# connaît avec certitude.
FEUILLE_DONNEES = u'Daten_Testprogramm'
CELLULE_MODE_SAISIE = u'H3'
VALEUR_MODE_HANDEINGABE = u'Handeingabe'


class CarteCellulesManquante(RuntimeError):
    """Levée si l'appelant n'a fourni aucune carte cellule <-> valeur.

    Voir docstring de module, réserve n° 3 : aucune adresse de cellule
    Handeingabe n'est inventée par ce dépôt à ce jour.
    """
    pass


class EcritureExcelDivergente(RuntimeError):
    """Levée si la relecture d'une cellule après écriture ne correspond pas
    à la valeur demandée -- garde-fou contre le risque documenté par
    ADR-001 §7 bis ("Erreur Excel convertie silencieusement en 0"), sur le
    même principe que `ve_adapter/test1_adapter.py::creer_materiau` (écrire,
    relire, échouer fort en cas de divergence)."""
    pass


def _win32com():
    try:
        import win32com.client
        return win32com.client
    except ImportError as erreur:
        raise ImportError(
            "Module 'win32com' indisponible : l'export Excel par COM exige "
            "Pywin32, présent dans VEScripts (docs/ADR-001-architecture-MSP.md "
            "§2) ou installable via `pip install pywin32` en développement. "
            "Erreur d'origine : " + str(erreur))


def _valeur_ligne(vue_test1, cle_periode, tolerance_absence=None):
    """Retrouve `valeur_candidate` pour une clé (grandeur, cas, periode) dans
    la structure produite par `ui/verdict_view.py::construire_vue_test1()`.

    Ne renvoie JAMAIS `0` par défaut si la ligne est absente ou si la valeur
    est `None` : renvoie explicitement `None`, laissé à l'appelant de
    décider (ce module n'écrit alors rien dans la cellule correspondante,
    cf. `remplir_classeur_sia`)."""
    grandeur, cas, periode = cle_periode
    for ligne in vue_test1['lignes']:
        if (ligne['grandeur'], ligne['cas'], ligne['periode']) == (grandeur, cas, periode):
            return ligne['valeur_candidate']
    return None


def remplir_classeur_sia(chemin_source, vue_test1, carte_cellules=None,
                          chemin_sortie=None, feuille=FEUILLE_DONNEES,
                          garder_excel_visible=False):
    """Remplit une COPIE du classeur SIA officiel en mode `Handeingabe`.

    `chemin_source` : chemin d'un classeur EXISTANT -- de préférence déjà
    une copie de travail (jamais un fichier de `SIA_4010_geteilter_Link/`,
    ADR-001 §4 : "à exécuter sur une copie, jamais sur les fichiers ...
    qui sont la source figée"). Ce module fait lui-même une copie
    supplémentaire vers `chemin_sortie` par précaution (défense en
    profondeur) et n'ouvre JAMAIS `chemin_source` directement en écriture.

    `vue_test1` : structure produite par
    `ui/verdict_view.py::construire_vue_test1()`.

    `carte_cellules` : dict obligatoire `{(grandeur, cas, periode):
    adresse_cellule}` (ex. `{('sensible_heating_demand_kwh', '1E',
    'annual'): 'N28'}`), sur la feuille `feuille`. AUCUNE valeur par défaut
    fournie ici (cf. docstring de module) -- lève `CarteCellulesManquante`
    si `None` ou vide, plutôt que de deviner une adresse.

    `chemin_sortie` : chemin du classeur rempli (défaut :
    `<chemin_source>` suffixé `_rempli` avant l'extension).

    Retourne le chemin du classeur rempli.

    # ⚠ À VÉRIFIER -- comportement non prouvé contre le VRAI classeur SIA
    (cf. docstring de module, réserves 1 et 2).
    """
    if not carte_cellules:
        raise CarteCellulesManquante(
            "Aucune carte cellule <-> (grandeur, cas, periode) fournie. "
            "ADR-001 §5 renvoie cette carte a un descripteur futur "
            "(refs/reference-data/testN.map.json), absent a ce jour. "
            "Fournir explicitement `carte_cellules` plutot que de deviner "
            "une adresse de cellule Handeingabe.")

    if chemin_sortie is None:
        racine, extension = _decouper_extension(chemin_source)
        chemin_sortie = racine + u'_rempli' + extension

    # Defense en profondeur : ne jamais ouvrir chemin_source en ecriture,
    # meme si l'appelant l'a deja lui-meme copie (ADR-001 §4).
    shutil.copyfile(chemin_source, chemin_sortie)

    win32com_client = _win32com()
    excel = win32com_client.Dispatch(u'Excel.Application')
    excel.Visible = bool(garder_excel_visible)
    excel.DisplayAlerts = False
    classeur = None
    try:
        classeur = excel.Workbooks.Open(chemin_sortie)
        feuille_donnees = classeur.Worksheets(feuille)

        # Active le mode Handeingabe -- SEULE adresse confirmee par ADR-001 §4.
        _ecrire_et_verifier_cellule(
            feuille_donnees, CELLULE_MODE_SAISIE, VALEUR_MODE_HANDEINGABE)

        cellules_ecrites = []
        cellules_ignorees_valeur_absente = []
        for cle_periode, adresse_cellule in carte_cellules.items():
            valeur = _valeur_ligne(vue_test1, cle_periode)
            if valeur is None:
                # Ne JAMAIS ecrire 0 a la place d'une valeur absente
                # (candidat non simule) -- laisser la cellule Excel vide/
                # inchangee plutot que de fabriquer un faux zero qui
                # pourrait passer pour une vraie mesure nulle.
                cellules_ignorees_valeur_absente.append((cle_periode, adresse_cellule))
                continue
            _ecrire_et_verifier_cellule(feuille_donnees, adresse_cellule, valeur)
            cellules_ecrites.append((cle_periode, adresse_cellule))

        # Force le recalcul complet -- indispensable pour que les colonnes
        # `Testprogramm` (calculees, jamais saisies -- ADR-001 §4) refletent
        # les nouvelles valeurs Handeingabe avant sauvegarde.
        excel.CalculateFullRebuild()

        classeur.Save()
    finally:
        if classeur is not None:
            classeur.Close(SaveChanges=False)  # deja sauvegarde explicitement ci-dessus
        excel.Quit()

    return chemin_sortie


def _decouper_extension(chemin):
    indice_point = chemin.rfind(u'.')
    if indice_point == -1:
        return chemin, u''
    return chemin[:indice_point], chemin[indice_point:]


def _ecrire_et_verifier_cellule(feuille_com, adresse_cellule, valeur, tolerance=1e-9):
    """Ecrit une valeur dans une cellule puis la relit pour verifier la
    persistance -- garde-fou direct contre ADR-001 §7 bis ("Erreur Excel
    convertie silencieusement en 0"), sur le meme principe que le pattern
    ecrire/relire deja etabli par `ve_adapter/test1_adapter.py`."""
    plage = feuille_com.Range(adresse_cellule)
    plage.Value = valeur
    valeur_relue = plage.Value
    if isinstance(valeur, (int, float)) and not isinstance(valeur, bool):
        if valeur_relue is None or abs(float(valeur_relue) - float(valeur)) > tolerance:
            raise EcritureExcelDivergente(
                u'Cellule {0} : ecrit={1!r}, relu={2!r} -- divergence, '
                u'ne pas continuer.'.format(adresse_cellule, valeur, valeur_relue))
    elif valeur_relue != valeur:
        raise EcritureExcelDivergente(
            u'Cellule {0} : ecrit={1!r}, relu={2!r} -- divergence, '
            u'ne pas continuer.'.format(adresse_cellule, valeur, valeur_relue))
