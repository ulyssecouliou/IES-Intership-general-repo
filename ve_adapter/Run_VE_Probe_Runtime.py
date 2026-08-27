# -*- coding: utf-8 -*-
"""Sonde de runtime VEScripts — repond a la seule question encore ouverte.

A lancer depuis la fenetre Scripts d'IESVE (bouton Run). Ne modifie rien, ne
simule rien, n'ecrit qu'un fichier texte a cote de ce script.

Pourquoi ce fichier existe : `docs/ADR-001-architecture-MSP.md` §2 constate une
contradiction non resolue. Le guide VE 2023 annonce Python 3.4.3 et des
bibliotheques de 2016 ; le depot `IES-Intership-general-repo`, qui tourne dans VE,
utilise `@dataclass` (3.7+) dans 49 modules sur 90. Les deux ne peuvent pas etre
vrais. Tant que ce n'est pas tranche, on ne peut ecrire aucune regle de style ni
choisir la voie de remplissage du classeur SIA.

Volontairement ecrit sans f-string ni annotation : il doit pouvoir s'executer meme
si le guide dit vrai.
"""

import os
import sys

BIBLIOTHEQUES = [
    # (module importable, usage prevu dans le produit)
    ("numpy", "agregation des series horaires"),
    ("pandas", "classes de frequence"),
    ("scipy", "statistiques"),
    ("matplotlib", "graphiques du PDF"),
    ("win32com.client", "PILOTAGE EXCEL PAR COM — remplissage du classeur SIA"),
    ("reportlab", "PDF client"),
    ("xlsxwriter", "creation de classeurs"),
    ("xlrd", "lecture de classeurs"),
    ("openpyxl", "lecture/ecriture xlsx (non documente comme fourni)"),
    ("jinja2", "gabarits de rapport"),
    ("PIL", "images"),
    ("tkinter", "interface dans VE"),
    ("dataclasses", "exige Python 3.7+ — presence = guide VE perime"),
    ("iesve", "API VE elle-meme"),
]


def _ligne(texte, sortie):
    print(texte)
    sortie.append(texte)


def main():
    sortie = []
    _ligne("=== SONDE RUNTIME VESCRIPTS ===", sortie)
    _ligne("sys.version      : " + sys.version.replace("\n", " "), sortie)
    _ligne("sys.version_info : " + repr(tuple(sys.version_info)), sortie)
    _ligne("sys.executable   : " + str(sys.executable), sortie)
    _ligne("plateforme       : " + sys.platform, sortie)
    _ligne("", sortie)

    _ligne("--- bibliotheques ---", sortie)
    for nom, usage in BIBLIOTHEQUES:
        try:
            module = __import__(nom)
        except Exception as erreur:  # ImportError et tout le reste
            _ligne(
                "  ABSENT   {0:20s} ({1}) : {2}".format(
                    nom, usage, erreur.__class__.__name__
                ),
                sortie,
            )
            continue
        version = getattr(module, "__version__", None)
        if version is None:
            version = getattr(module, "version", "(version inconnue)")
        _ligne("  present  {0:20s} {1:12s} {2}".format(nom, str(version), usage), sortie)

    _ligne("", sortie)
    _ligne("--- verdict ---", sortie)
    if sys.version_info >= (3, 7):
        _ligne("  Python >= 3.7 : le guide VE 2023 est PERIME sur ce point.", sortie)
        _ligne("  Aucune contrainte 3.4 a imposer au code.", sortie)
    else:
        _ligne("  Python < 3.7 : le guide dit vrai. Pas de f-string ni de", sortie)
        _ligne("  dataclasses dans le code destine a VE.", sortie)

    chemin = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "probe_runtime_resultat.txt"
    )
    try:
        with open(chemin, "w") as flux:
            flux.write("\n".join(sortie))
        print("")
        print("Ecrit dans : " + chemin)
    except Exception as erreur:
        print("Ecriture impossible (" + str(erreur) + ") — copier la sortie ci-dessus.")


if __name__ == "__main__":
    main()
