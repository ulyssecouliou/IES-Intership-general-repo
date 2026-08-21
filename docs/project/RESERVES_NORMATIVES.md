# Réserves normatives — conformité client SIA 380/2 (« on fait sans, sous réserve »)

Ce registre liste les points où une **norme sous licence** n'est pas en notre
possession, **où la trouver**, comment l'outil **fonctionne sans elle**, et la
**réserve explicite** attachée au verdict correspondant.

> **Politique (décision projet 2026-08-20).** Aucun achat de norme payante n'est
> engagé. L'outil reste **exploitable** sans ces documents : le critère concerné
> est rendu **VALIDÉ SOUS RÉSERVE** ou `[À VÉRIFIER]` / `NOT_DETERMINED`, jamais
> un `PASS` silencieux (règle 2 de CLAUDE.md : « missing evidence never becomes
> PASS »). À l'obtention du document, la réserve est levée et le verdict confirmé.
> Voir aussi `docs/project/REGISTRE_DEMANDES_EXTERNES.md` (côté tests SIA 4010).

## Où trouver les documents

| Document | Où l'obtenir | Déjà en main ? |
|---|---|---|
| **SN EN 14825:2018** (SEER/SCoP) | SNV (snv.ch) / normes EN — accès habituel ; relais SIA Shop | **Froid : oui** (figé, `sn-en-14825-2018.cooling-seer.json`). Chaud (SCoP) : non |
| **SIA 387/4:2023** (éclairage + protection solaire) | shop.sia.ch ; contact **Yiqiao Yang** (SIA) | **Tableau 9 protection solaire : oui** (`sia-387-4-2017.blinds.json`, éq. 18-20 confirmées). **Contenu éclairage : non** |
| **SIA 180:2014** (confort / T° opérative) | shop.sia.ch ; Yiqiao Yang | **Fig. 3 & 4 + chiffre 2.3.1 : oui**. Définition exacte T° opérative / fenêtre θrm : à confirmer |
| **SIA 2024:2021** (données d'usage, besoin de froid) | shop.sia.ch | **Catégorie 3.1 : oui**. Autres catégories : partiel |
| **SIA 2056** (refroidissement des bâtiments) | shop.sia.ch | non |
| **SIA 380:2022** (faîtière — pondération, appariement seuil) | shop.sia.ch (payant) ; `term.sia.ch/?id=1894` (facteur, payant) | **non — abandonné (pas d'achat)** |

## Réserves par critère — statut « validé sous réserve »

| Critère (outil) | Ce qui manque | Comment l'outil fait sans | Verdict rendu | Réserve à lever avec |
|---|---|---|---|---|
| **SCoP chaud** `SIA3802_HEATING_SCOP` | Équivalence saisonnière EN 14825 (chaud) | Compare le SCoP à la bande SIA (tables 8/9), avec caveat | **VALIDÉ SOUS RÉSERVE** — indicatif `[TO VERIFY]`, jamais un pass prouvé | **SN EN 14825 (partie chaud)** |
| **Contrôle éclairage** `SIA3802_LIGHTING_CONTROL` | Contenu éclairage SIA 387/4 (puissance installée + contrôle présence / lumière du jour) | Tableau 9 (protection solaire) intégré ; l'éclairage reste non clôturé | **PARTIAL** — à compléter | **SIA 387/4:2023 (partie éclairage)** |
| **§7.2.4 — classification du besoin de froid** | Règle nécessaire / souhaitable (§3.2) | Prend la `cooling_category` fournie par le relecteur ; sinon indéterminé | Verrou §7.2.4 appliqué **sous réserve** ; catégorie inconnue → `NOT_DETERMINED` | **SIA 180 / SIA 2024 / SIA 2056** |
| **§7.2.4 — appariement seuil 7/12 ↔ cas d'application** | Correspondance exacte cas ↔ seuil | Applique 7 W/m² (neuf) / 12 (existant) selon le statut relu | Seuils appliqués **sous réserve** `[À VÉRIFIER]` | **SIA 380 faîtière** (abandonnée) |
| **Confort d'été SIA 180** `SIA3802_SUMMER_COMFORT_*` | Définition exacte T° opérative + fenêtre θrm | Calcul depuis θrm 48 h et Fig. 3/4 figées | Bloquant si surchauffe **avérée** ; sinon réserve — **sous réserve** de la définition | **SIA 180:2014 (T° opérative)** → norm-analyst |
| **SEER froid** `SIA3802_COOLING_EER_SEER` | — (rien : SN EN 14825 froid figé) | Compare le SEER déclaré à la bande Table 5/6 | **VALIDÉ (pass propre)** ✅ | *(réserve levée)* |

## En pratique
- Un rapport peut donc **conclure** (COMPLIANT / NOT_DETERMINED / NOT_COMPLIANT) sans
  ces documents ; les lignes ci-dessus restent **explicitement réservées** dans les
  livrables (caveats `[TO VERIFY]` / notes `outstanding`).
- À réception d'un document, mettre à jour la référence figée correspondante
  (via son script `scripts/…`) et lever la réserve dans ce tableau + dans le code
  (retrait du caveat concerné), avec un test de non-régression.
- **Ne jamais** convertir une de ces réserves en `PASS` sans le document ou une
  attestation relecteur.
