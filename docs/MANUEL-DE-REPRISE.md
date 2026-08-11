# Manuel de reprise — validation SIA 4010 pour IESVE

> **À lire en premier.** Ce document existe pour qu'une personne qui n'a jamais
> vu ce dépôt puisse, en une demi-heure, savoir ce qu'il fait, ce qu'il ne fait
> pas encore, pourquoi il est écrit ainsi, et où reprendre.
>
> Dernière mise à jour : **2026-08-10**. Les chiffres cités sont mesurés, pas
> estimés ; la commande qui les produit est indiquée à chaque fois.

---

## 1. La distinction à ne jamais perdre

Ce dépôt sert **deux travaux différents**, et les confondre est l'erreur la
plus coûteuse possible ici.

| | **SIA 4010** | **SIA 380/2** |
|---|---|---|
| Ce qui est jugé | le **logiciel** IESVE et ses méthodes | un **bâtiment client** |
| La question | « VE calcule-t-il juste ? » | « ce bâtiment est-il conforme ? » |
| La preuve | reproduire les valeurs des programmes de référence | des relevés du modèle client |
| Où c'est | `engine/`, `ve_adapter/`, `ui/` | `swiss_sia/` |

Trois états portent des noms voisins et ne veulent pas dire la même chose :

- **PASS technique** — une valeur simulée tombe dans la bande de référence ;
- **conformité SIA 380/2** — un bâtiment satisfait la norme ;
- **validation SIA 4010** — une classe est validée, ce qui exige une
  **signature indépendante**, jamais un calcul.

Un PASS technique n'est ni l'un ni l'autre. Cette phrase est affichée en pied
de l'interface (`ui/i18n.py`, clé `note.pass_is_not_compliance`) parce que la
confusion se produit devant l'écran, pas seulement à la lecture d'un rapport.

---

## 2. Ce que fait le produit

Un **navigateur** lancé depuis le *Python Scripts navigator* de VE. On y
choisit une classe de validation (1A à 5), et il montre, pour cette classe
seulement, les tests exigés, les grandeurs, la bande admissible, le verdict et
l'article de norme qui le fonde. Il exporte vers le classeur SIA officiel et
en PDF.

    Run_VE_SIA4010_Navigator.py        ← à lancer depuis VEScripts

Les autres lanceurs à la racine (`Run_VE_SIA4010_*.py`) sont des outils de
relevé ou de construction, décrits au §7.

---

## 3. Les cinq règles, et pourquoi elles existent

Elles sont dans `CLAUDE.md`. Elles n'y sont pas par principe : chacune répond à
un défaut réel, déjà survenu dans ce dépôt.

**1. Ne jamais inventer une valeur, une tolérance, un article ou un symbole
d'API.** Un symbole `iesve` plausible mais faux ne lève pas toujours : il rend
`None`, qui devient zéro plus loin.

**2. La vérité, ce sont les valeurs de référence publiées.** Le moteur n'est
correct que s'il les reproduit dans la tolérance. Pas « s'il semble
raisonnable ».

**3. Traçabilité.** Chaque contrôle cite son article. Une matrice qui cite un
fichier absent est un faux témoignage — d'où le contrôle d'existence dans
`scripts/build_traceability_matrix.py`.

**4. Séparation dur/pur.** `engine/` est du Python pur, zéro import `iesve`,
testable sans licence ni écran. Tout accès VE vit dans `ve_adapter/`.

**5. Rien n'est « done » sans signature indépendante.** Un script qui se
signerait lui-même ne vaudrait rien.

### La règle qui n'est pas écrite mais qui gouverne tout

**Une absence n'est jamais un zéro, et un « rien à signaler » doit être
mérité.** Presque tous les défauts trouvés ici sont de la même famille : du
code vert qui affirme quelque chose de faux avec assurance. Voir §8.

---

## 4. Comment c'est organisé

```
engine/          moteur de validation, Python PUR
engine/tests/    ils reproduisent les valeurs de référence — c'est la vérité
ve_adapter/      tout ce qui touche à `iesve` et aux fichiers .aps
ui/              le navigateur, la charte, les exports
scripts/         extracteurs de référence, sondes, générateurs de documents
swiss_sia/       chantier SIA 380/2 — voir §1, ne pas mélanger
refs/            référentiels FIGÉS, lecture seule
traceability/    matrices clause → code → test, une par test
docs/            ce manuel, les fiches de saisie, les ADR
```

### Ce qui est généré et ne se modifie pas à la main

| Document | Producteur |
|---|---|
| `traceability/test-N.matrix.md` | `scripts/build_traceability_matrix.py` |
| `docs/FICHE-APACHEHVAC-TEST{4,5,6}.md` | `scripts/build_fiche_apachehvac*.py` |
| `docs/FICHE-LIAISONS-APS.md` | `scripts/match_aps_variables.py` |
| `refs/reference-data/*.json` | les extracteurs de `scripts/` |

Un hook (`.claude/hooks/garde_refs.py`) **refuse** l'édition manuelle d'un
référentiel figé. Si l'un est faux, on corrige l'extracteur et on relance.

Le générateur de matrices **n'écrase jamais un document qu'il n'a pas écrit** :
il reconnaît ses propres sorties à leur ligne de signature. La matrice du
Test 7 est un audit rédigé à la main ; le relevé automatique va à côté, dans
`test-7.matrix.releve.md`.

### Langue

Décision du propriétaire, 2026-08-10 : **le code passe à l'anglais**,
identifiants, commentaires et docstrings. **Le texte affiché à l'utilisateur
est bilingue, français par défaut**, et passe par `ui/i18n.py` — jamais un
littéral dans un widget. **La documentation reste en français.** Les libellés
allemands qui servent de clé de recherche dans les classeurs SIA restent
verbatim : les traduire casse la correspondance.

La conversion se fait **module par module, entier**. Un fichier à moitié
traduit est celui que personne ne peut lire.

---

## 5. Où on en est, au 2026-08-10

**Les huit classes sont `NON_EVALUEE`. Aucune valeur simulée n'existe encore.**
C'est le seul constat qui compte.

```bash
python -c "import sys;sys.path.insert(0,'.');from engine import test1_engine as m;from ui import verdict_view as v,class_selection as s;print([ (c, s.diagnose(c,[v.construire_vue_test1(m.evaluer_test1(m.charger_reference()))])['statut']) for c in s.CLASSES])"
```

### Trois verrous, dans cet ordre

**1. Le climat SIA 2028 DRY Zürich-Kloten est absent du dépôt.** Il bloque les
tests 2 à 7 entièrement. Pour le Test 1 il bloque les cas diagnostiques 1A–1E,
et **1E porte le seul critère pass/fail du test** : sans lui le Test 1 tourne
(ses six cas principaux utilisent DRYCOLD, présent) mais ne rend aucun verdict
formel.

> `DRYCOLD_IESVE.epw` n'est **pas** un climat suisse approuvé. Sa présence
> prouve seulement une correspondance technique entre VE et APS.

**2. Les réseaux ApacheHVAC.** `HVACNetwork` n'expose **aucune méthode de
création** : la saisie est manuelle, une fois, dans l'éditeur VE. Les fiches
sont prêtes (`docs/FICHE-APACHEHVAC-TEST{4,5,6}.md`) mais **11 points doivent
être tranchés sur les PDF avant de saisir** — dont cinq paramètres du Test 5
dont la répartition entre variantes 5A–5D n'est pas dans la couche texte.

**3. Les 20 noms de variables APS** des tests 2 à 6, tous à 0/20. Ce ne sont
pas des symboles d'API : ils se relèvent sur un `.aps` réel.

### Ce qui est acquis

- Test 1 : géométrie, gbXML, constructions et matériaux construits et relus ;
  **première concordance VE↔norme** — R du mur 1,7893 contre 1,789 (ISO 52016-1)
- références figées des tests 2 à 7, bandes recalculées et confrontées
- distributions de fréquence des tests 2, 3 et 5 extraites
- navigateur, charte IES, exports Excel et PDF

---

## 6. La boucle de travail d'un test

1. `norm-analyst` → spec, tolérances, citations
2. `reference-data-engineer` → références figées en JSON
3. `validation-engine-engineer` → moteur + tests qui reproduisent les valeurs
4. `ve-adapter-engineer` → extraction des grandeurs
5. `ui-engineer` → câblage dans le navigateur
6. `qa-auditor` → contrôle indépendant, signe la traçabilité
7. `docs-writer` → doc

Ne pas passer au test suivant tant que le courant n'est pas « done ».

---

## 7. Les outils, et quand s'en servir

| Commande | À quoi ça sert |
|---|---|
| `python -m pytest -o addopts="" -q` | la suite complète (~2-3 min) |
| `python scripts/build_traceability_matrix.py --ecrire` | régénère les matrices |
| `python scripts/match_aps_variables.py --write` | confronte un relevé APS aux grandeurs déclarées |
| `python scripts/build_reseau_ventilation_reference.py` | relit les réseaux 5 et 6 dans les PDF |
| `python scripts/bootstrap_check.py` | contrôle que VEScripts charge le bon dépôt |

Depuis **VEScripts** uniquement :

| Lanceur | Effet |
|---|---|
| `Run_VE_SIA4010_Navigator.py` | ouvre le navigateur |
| `Run_VE_SIA4010_Sonde_APS.py` | relève toutes les variables d'un `.aps` |
| `Run_VE_SIA4010_Importer_Geometrie_Test1.py` | **MODIFIE le modèle** — projet jetable |

> VEScripts garde **un seul interpréteur** d'un clic sur Run au suivant.
> `sys.modules` persiste : un module d'un autre dépôt reste chargé et sera
> réutilisé en silence. `scripts/bootstrap_check.py` purge et vérifie. Le cas
> dangereux est un nom qui existe dans les deux dépôts — il s'importe sans
> erreur, et on débogue le mauvais fichier.

---

## 8. Les défauts trouvés, et ce qu'ils enseignent

Cette section est la plus utile du manuel. Tous ces défauts avaient une suite
de tests verte.

**Les couches de 1 mm.** 18 étapes sur 18 au vert dans la sonde ; les couches
étaient restées à l'épaisseur VE par défaut. R = 0,038 au lieu de 1,789 —
**47 fois trop faible**. Trouvé en relisant le code après un succès, par aucun
test. → *Écrire puis RELIRE toute écriture VE.*

**Le filtrage par classe qui ne retenait rien.** `_numero_du_test` lisait les
chiffres de tête ; les `test_id` réels sont `SIA-4010-Test-1` et `Test 7`. Le
filtre rendait toujours vide, l'écran affichait « 0/2 tests présents » avec les
résultats à l'écran, et les exports seraient partis vides. Les tests le
manquaient : leurs identifiants synthétiques étaient `'1'` et `'7'`.
→ *Tester contre la forme RÉELLE des données, pas contre un double commode.*

**Les tests 4 et 6 « sans distribution ».** Écrit dans l'extracteur comme
« un constat, pas un oubli ». C'était un oubli. Leurs classeurs nomment la
feuille `Haeufigkeits**k**assen` — sans le « l » de `Haeufigkeitsklassen`. Une
faute de frappe dans les fichiers officiels, prise pour une absence, puis
répétée dans deux matrices générées.
→ *Une absence constatée par un seul chemin de recherche n'est pas une absence.*

**Le diagnostic qui donnait un bulletin de santé propre.** `diagnose` ne
signalait un test que s'il était *absent*. Un test présent mais non évalué —
ou **en échec** — ne produisait aucun blocage : « 0 blocage, atteignable ».
→ *Un « rien à signaler » doit être mérité, pas obtenu par omission.*

**Le pied de page à un pixel.** Le rappel « un PASS technique n'est pas une
conformité » disparaissait de l'écran, sans erreur : le contenu demandait plus
de hauteur que la fenêtre, et Tk sert dans l'ordre d'empaquetage. Trouvé en
regardant une capture, pas en relisant.
→ *Regarder l'écran fait partie du contrôle.*

**Le verdict qui affichait « ? ».** Une table indexée par `vert`/`rouge`/`gris`
remplacée par une table indexée par `pass`/`fail`. 255 tests verts : ils
vérifient quels tags sont *posés*, jamais ce qu'un tag *rend*.

---

## 9. Décisions de l'autorité, 2026-08-10

Une clarification écrite du **Prof. Gerhard Zweifel**, fournie par le
propriétaire, est consignée dans
`traceability/sia4010-authority-clarification-2026-08-10.json`. Cinq décisions,
dont :

- **`Streubereich` = l'enveloppe min/max des programmes de référence, classe
  par classe.** La bande « moyenne ± écart maximal » devient diagnostique. Cela
  débloque le second critère des tests 2, 3 et 5.
- Les classeurs des tests 4 et 6 **contiennent** des classes de fréquence et
  des feuilles de distribution (voir §8).
- Les résultats exigés sont ceux listés dans les classeurs d'évaluation ; un
  résultat listé et manquant reste `NOT_CHECKABLE`, jamais omis en silence.

---

## 10. Par où reprendre

Dans l'ordre de rendement :

1. **Relever les dispositions des tests 4 et 6** dans
   `scripts/build_sia_distribution_reference.py::DISPOSITIONS`, puis extraire
   leurs distributions. La structure est identifiée (Test 4 : section
   « Stündliche Häufigkeitsverteilung », `Zusammenfassung` ligne 19) ; il reste
   à relever les numéros de ligne exacts. Cet extracteur ne devine jamais une
   disposition — c'est sa règle, elle tient.
2. **Terminer la conversion en anglais.** 266 fichiers Python suivis, environ
   105 portent encore du français. `ui/` est fait à sept modules sur neuf ;
   restent `verdict_view.py` et `dialog_tkinter.py`.
3. **Obtenir le climat Kloten** — c'est le verrou le plus haut et il ne dépend
   d'aucun code.
4. **Trancher les 11 points des fiches ApacheHVAC**, puis saisir les réseaux.

### Ce qui bloque, et qui peut le lever

| Blocage | Qui |
|---|---|
| Climat SIA 2028 Kloten | la SIA / Johan |
| Périmètre de `Beleuchtungsenergie` (système ou bâtiment ?) | la spécification / la SIA |
| Répartition 5A–5D des 5 paramètres du Test 5 | lecture du PDF d'origine |
| Saisie des réseaux ApacheHVAC | une personne dans VE |
| Fiches d'usage SIA 2024 exploitables | la SIA |

---

## 11. Pièges de l'environnement

- **Deux dépôts se ressemblent.** `SIA_Compliance_Scripts` est l'ancien. Le
  travail vit dans `IES-Intership-general-repo`. `scripts/bootstrap_check.py` vérifie
  lequel est chargé.
- **`tkinter.Tk()` échoue par intermittence** sur ce poste (Python du Microsoft
  Store, `init.tcl` introuvable alors que le fichier existe). C'est un artefact
  de cette distribution, pas un défaut du code : les tests le convertissent en
  *skip*.
- **VE stocke en float32.** Une égalité exacte échoue sur une écriture pourtant
  correcte.
- **ttk démarre sur `vista` sous Windows**, qui **ignore** `background`. Sans
  bascule vers `clam`, toute la charte est ignorée sans qu'aucune erreur ne se
  produise (`ui/theme.py`).
- **`ApacheSystems` n'est pas ApacheHVAC.** C'est un modèle de rendements
  saisonniers (SFP, SEER, SCoP) : il ne sait pas exprimer les batteries, le
  bypass, la protection antigel ni le débit piloté par le CO2.

---

## 12. Ce que ce dépôt ne prouve pas

À dire à quiconque demande où on en est :

- **aucune classe n'est validée**, et aucune ne peut l'être sans simulation ;
- l'export Excel n'a **jamais** été exécuté contre le vrai classeur SIA — les
  fichiers font 130 Mo et ne sont pas dans `/refs` ;
- le comportement **dans** le processus VE (thread partagé, boucle
  d'événements) n'est testé nulle part ;
- les liaisons APS des tests 2 à 6 sont à **0 sur 20**.

Dire ce qu'on n'a pas vérifié vaut mieux que de le masquer. C'est la seule
règle qui rend les autres utiles.
