# -*- coding: utf-8 -*-
"""Inventaire du batiment exemple SIA 4010 depuis son IFC.

LECTURE SEULE. Ne modifie ni l'IFC ni aucun modele VE. Sert a etablir, AVANT
tout import dans VE, ce que le fichier contient reellement : locaux, etages,
surfaces, et le rattachement de chaque local a son etage.

Pourquoi ce script existe : le batiment exemple (`SIA 4010:2023` §4.3) est requis
par les Tests 4 a 7, donc par les classes de validation 3, 4A et 4B. La
specification du Test 4 designe nommement le local « Hoersaal » avec une surface
de 165.8 m2 -- c'est un controle croise verifiable entre la specification et
l'IFC, et le premier point a etablir avant de faire confiance au fichier.

L'IFC est un IFC2X3 « CoordinationView » produit par AbstractBIM
(`FILE_SCHEMA(('IFC2X3'))`), 312 Ko, 4897 entites. On le lit par analyse
lexicale du format STEP plutot qu'avec une bibliotheque IFC : le besoin se
limite aux entites `IFCSPACE`, `IFCBUILDINGSTOREY` et aux quantites associees,
et cela evite d'ajouter une dependance lourde a la CI.

Les noms IFC sont encodes en ISO-10303-21 : « Hoersaal » s'y ecrit
`H\\X2\\00F6\\X0\\rsaal`. Le decodage est explicite plus bas.
"""

import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IFC_DEFAUT = os.path.join(
    RACINE, 'SIA_4010_geteilter_Link', 'Beispielgebäude',
    'IFC_Beispielebäude_201106_abstractBIM.ifc')

# Encodage des caracteres non ASCII dans STEP : \X2\<hex UTF-16>\X0\
_MOTIF_X2 = re.compile('\\\\X2\\\\((?:[0-9A-Fa-f]{4})+)\\\\X0\\\\')
_MOTIF_X = re.compile('\\\\X\\\\([0-9A-Fa-f]{2})')
_MOTIF_ENTITE = re.compile(r'#(\d+)\s*=\s*([A-Z0-9_]+)\s*\((.*?)\);', re.S)


def decoder(texte):
    """Rend un libelle STEP lisible."""
    def _x2(m):
        brut = m.group(1)
        return ''.join(chr(int(brut[i:i + 4], 16))
                       for i in range(0, len(brut), 4))
    texte = _MOTIF_X2.sub(_x2, texte)
    texte = _MOTIF_X.sub(lambda m: chr(int(m.group(1), 16)), texte)
    return texte


def champs(corps):
    """Decoupe les champs d'une entite STEP en respectant parentheses et chaines."""
    resultat, profondeur, courant, dans_chaine = [], 0, '', False
    for caractere in corps:
        if caractere == "'":
            dans_chaine = not dans_chaine
        if not dans_chaine:
            if caractere == '(':
                profondeur += 1
            elif caractere == ')':
                profondeur -= 1
            elif caractere == ',' and profondeur == 0:
                resultat.append(courant.strip())
                courant = ''
                continue
        courant += caractere
    resultat.append(courant.strip())
    return resultat


def charger(chemin):
    """Rend {identifiant: (type, champs)} pour tout le fichier."""
    with open(chemin, encoding='utf-8', errors='replace') as flux:
        brut = flux.read()
    entites = {}
    for trouve in _MOTIF_ENTITE.finditer(brut):
        entites[int(trouve.group(1))] = (trouve.group(2),
                                         champs(trouve.group(3)))
    return entites


def _texte(valeur):
    valeur = (valeur or '').strip()
    if valeur in ('$', '*', ''):
        return ''
    return decoder(valeur.strip("'"))


def _nombre(valeur):
    try:
        return float((valeur or '').strip())
    except ValueError:
        return None


def _references(valeur):
    return [int(x) for x in re.findall(r'#(\d+)', valeur or '')]


def quantites_par_objet(entites):
    """Rend {identifiant objet: {nom de quantite: valeur}}.

    Les quantites vivent dans des `IFCELEMENTQUANTITY` relies aux objets par
    des `IFCRELDEFINESBYPROPERTIES`. On ne retient que les quantites nommees
    (surface, longueur, volume), sans interpreter leur signification.
    """
    par_objet = {}
    for _identifiant, (type_entite, valeurs) in entites.items():
        if type_entite != 'IFCRELDEFINESBYPROPERTIES':
            continue
        # IfcRelDefinesByProperties(GlobalId, OwnerHistory, Name, Description,
        #                           RelatedObjects, RelatingPropertyDefinition)
        if len(valeurs) < 6:
            continue
        objets = _references(valeurs[4])
        definition = _references(valeurs[5])
        if not definition:
            continue
        cible = entites.get(definition[0])
        if cible is None or cible[0] != 'IFCELEMENTQUANTITY':
            continue
        # IfcElementQuantity(..., Quantities) : dernier champ
        mesures = {}
        for reference in _references(cible[1][-1]):
            mesure = entites.get(reference)
            if mesure is None:
                continue
            type_mesure, champs_mesure = mesure
            if not type_mesure.startswith('IFCQUANTITY'):
                continue
            nom = _texte(champs_mesure[0]) if champs_mesure else ''
            valeur = None
            for brut in reversed(champs_mesure):
                valeur = _nombre(brut)
                if valeur is not None:
                    break
            if nom and valeur is not None:
                # ⚠ CE FICHIER STOCKE LES SURFACES ET VOLUMES EN NEGATIF :
                #   #54=IFCQUANTITYAREA('GrossFloorArea',$,#14, -237.36);
                # C'est une propriete de l'export AbstractBIM, pas une erreur de
                # lecture. On prend la valeur absolue et on conserve le signe
                # d'origine dans `signes_negatifs` pour pouvoir le signaler :
                # une surface negative doit etre remontee, jamais absorbee en
                # silence.
                mesures[nom] = abs(valeur)
                if valeur < 0:
                    mesures.setdefault('_signes_negatifs', set()).add(nom)
        for objet in objets:
            par_objet.setdefault(objet, {}).update(mesures)
    return par_objet


def etage_par_objet(entites):
    """Rend ({identifiant objet: nom d'etage}, {identifiant etage: nom}).

    Dans CE fichier, les locaux ne sont PAS rattaches par `IFCRELAGGREGATES` :
    celui-ci ne porte que la chaine projet -> site -> batiment (3 occurrences).
    Le rattachement des locaux aux etages passe par
    `IFCRELCONTAINEDINSPATIALSTRUCTURE` (5 occurrences, une par etage).
    Les deux relations sont lues, la seconde primant, afin que le script reste
    correct sur un IFC produit par un autre outil.
    """
    etages = {}
    for identifiant, (type_entite, valeurs) in entites.items():
        if type_entite == 'IFCBUILDINGSTOREY':
            etages[identifiant] = _texte(valeurs[2]) if len(valeurs) > 2 else ''

    rattachement = {}
    for relation, index_parent, index_enfants in (
            ('IFCRELAGGREGATES', 4, 5),
            ('IFCRELCONTAINEDINSPATIALSTRUCTURE', 5, 4)):
        for _identifiant, (type_entite, valeurs) in entites.items():
            if type_entite != relation or len(valeurs) <= max(index_parent,
                                                              index_enfants):
                continue
            parents = _references(valeurs[index_parent])
            if not parents or parents[0] not in etages:
                continue
            for enfant in _references(valeurs[index_enfants]):
                rattachement[enfant] = etages[parents[0]]
    return rattachement, etages


def inventaire(chemin):
    entites = charger(chemin)
    quantites = quantites_par_objet(entites)
    rattachement, etages = etage_par_objet(entites)

    locaux = []
    for identifiant, (type_entite, valeurs) in sorted(entites.items()):
        if type_entite != 'IFCSPACE':
            continue
        locaux.append({
            'id': identifiant,
            'nom': _texte(valeurs[2]) if len(valeurs) > 2 else '',
            'designation': _texte(valeurs[7]) if len(valeurs) > 7 else '',
            'etage': rattachement.get(identifiant, ''),
            'quantites': quantites.get(identifiant, {}),
        })
    return entites, etages, locaux


def main():
    chemin = sys.argv[1] if len(sys.argv) > 1 else IFC_DEFAUT
    if not os.path.isfile(chemin):
        sys.stderr.write('IFC introuvable : ' + chemin + '\n')
        return 1
    entites, etages, locaux = inventaire(chemin)

    print('=== BATIMENT EXEMPLE SIA 4010 -- inventaire IFC (lecture seule) ===')
    print('fichier  : ' + os.path.basename(chemin))
    print('entites  : %d' % len(entites))
    print('etages   : %d -> %s' % (len(etages),
                                   ', '.join(sorted(v for v in etages.values() if v))))
    print('locaux   : %d' % len(locaux))
    print('')

    # Quantites de surface reellement presentes, sans presomption : ce fichier
    # ne porte AUCUN `NetFloorArea`. La valeur de 165.8 m2 citee par la spec du
    # Test 4 correspond au `GrossFloorArea` (verifie : 165.81).
    noms_quantites = set()
    for local in locaux:
        noms_quantites.update(k for k in local['quantites'] if not k.startswith('_'))
    print('quantites de surface presentes sur les locaux : %s' % (
        ', '.join(sorted(noms_quantites)) or '(aucune)'))
    print('')

    print('%-6s %-6s %-24s %-13s %10s %10s' % (
        '#id', 'Nom', 'Designation', 'Etage', 'Brut m2', 'Volume m3'))
    total = 0.0
    for local in locaux:
        mesures = local['quantites']
        brut = mesures.get('GrossFloorArea')
        volume = mesures.get('GrossVolume')
        if brut:
            total += brut
        print('%-6s %-6s %-24s %-13s %10s %10s' % (
            '#' + str(local['id']), local['nom'][:6], local['designation'][:24],
            local['etage'][:13],
            '%.2f' % brut if brut is not None else '-',
            '%.2f' % volume if volume is not None else '-'))
    print('')
    print('somme des surfaces brutes : %.2f m2' % total)

    negatifs = sorted(set(
        nom for local in locaux
        for nom in local['quantites'].get('_signes_negatifs', ())))
    if negatifs:
        print('⚠ quantites stockees en NEGATIF dans l IFC (valeur absolue prise) : %s'
              % ', '.join(negatifs))

    print('')
    print('=== controle croise avec la specification du Test 4 ===')
    print("La spec designe le local « Hoersaal », sans fenetre, sur deux niveaux")
    print('(1er et 2e etage), toiture sur extérieur, de 165.8 m2.')
    candidats = [l for l in locaux
                 if 'rsaal' in (l['nom'] + l['designation']).lower()]
    if not candidats:
        print('  AUCUN local dont le nom contienne « rsaal ».')
        print('  ⚠ Le rattachement spec <-> IFC doit etre etabli autrement.')
    for local in candidats:
        mesures = local['quantites']
        print('  #%-6s %-6s %-12s etage=%-13s brut=%s m2  hauteur=%s m  vol=%s m3' % (
            local['id'], local['nom'], local['designation'], local['etage'],
            '%.2f' % mesures['GrossFloorArea'] if 'GrossFloorArea' in mesures else '-',
            '%.2f' % mesures['AverageHeight'] if 'AverageHeight' in mesures else '-',
            '%.2f' % mesures['GrossVolume'] if 'GrossVolume' in mesures else '-'))
    if candidats:
        cumul = sum(l['quantites'].get('GrossFloorArea') or 0.0 for l in candidats)
        ecart = cumul - 165.8
        print('  surface cumulee : %.2f m2 -- ecart a la spec (165.8) : %+.2f m2' % (
            cumul, ecart))
        print('  %s' % ('CONCORDE (l IFC est bien le batiment de la spec).'
                        if abs(ecart) < 0.05
                        else 'ECART SIGNIFICATIF -- a elucider avant tout import.'))
        # La spec dit « zweigeschossig, im 1. und 2. OG » : le local doit couvrir
        # deux niveaux. Les etages sont a 3.4, 6.8 et 9.8 m, donc une hauteur
        # d'environ 6.4 m confirmerait la double hauteur, 3.4 m la refuterait.
        for local in candidats:
            hauteur = local['quantites'].get('AverageHeight')
            if hauteur is None:
                continue
            print('  hauteur moyenne %.2f m -> %s' % (
                hauteur,
                'coherent avec un local sur DEUX niveaux' if hauteur > 5.0
                else 'un seul niveau : CONTREDIT « zweigeschossig », a elucider'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
