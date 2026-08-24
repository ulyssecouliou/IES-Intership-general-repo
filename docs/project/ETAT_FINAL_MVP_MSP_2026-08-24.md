# État de clôture MVP / MSP au 24 août 2026

## Décision de livraison

Le produit est un **MVP livrable pour revue interne et démonstration client encadrée**. Il s'exécute depuis IESVE, lit le modèle et l'APS, collecte les preuves projet, puis produit un PDF et un classeur Excel au style IES. Il ne constitue ni un certificat SIA ni une attestation SIA 4010.

Le MSP logiciel de readiness/audit est suffisamment constitué pour une remise interne, sous réserve du smoke test IESVE final. La conformité du modèle reste une décision de projet dépendant de preuves externes et d'une revue compétente.

## Dernier parcours réel connu

Dernier export fourni : `2026-08-24 17:55:03` pour `SIA_compatible_model_TEST`.

- verdict : **NOT DETERMINED** ;
- constats bloquants : **0** ;
- preuves manquantes : **4** ;
- l'écran de confort signale 1462 heures, mais la méthode normative en température opérative n'est pas encore entièrement démontrée : ce nombre ne doit donc pas devenir une non-conformité automatique ;
- la ventilation modifiée et le profil de chauffage réparé ont été simulés dans un APS annuel vérifié ;
- le rapport reste à régénérer après saisie et acceptation des preuves projet.

## Ce qui est terminé côté produit

- lancement Run-button et interface client ;
- stratégie du bâtiment saisissable par modèle ;
- éditeur guidé de six familles de preuves techniques ;
- stockage des preuves dans le projet VE actif, avec sauvegarde `.bak` ;
- validation fail-closed : une acceptation incomplète est forcée à `pending` ;
- 16/16 gabarits CSV enregistrés et préparés sans écraser les données revues ;
- extraction VE/CDB/APS et contrôles SIA 380/2 disponibles ;
- rapport PDF et Excel avec en-tête/pied de page homogènes IES ;
- evidence pack ZIP, manifestes et audit trail ;
- garde-fous de revendication SIA 4010 ;
- tests Python et porte de release locale.

## Ce qui dépend encore du projet ou d'un tiers

| Élément | Responsable | Condition de fermeture |
| --- | --- | --- |
| Statut bâtiment et climat approuvé | Responsable énergie/SIA | Source, date et signature dans l'onglet Projet et climat |
| Comparaison énergétique globale projet/référence | Responsable énergie/SIA | Calcul complet signé et valeurs projet/référence |
| Commandes ventilation et performances froid | Ingénieur HVAC | Note de calcul, fiches fabricant et confirmation des classes |
| Commandes d'éclairage | Ingénieur électricité/éclairage | Mapping SIA 387/4 signé |
| Puissance électrique de dimensionnement | Ingénieur HVAC/électricité | W/m², surface et catégorie de nécessité du froid |
| Méthode complète de confort d'été | Responsable simulation/SIA | Température opérative, occupation, seuil et période documentés |
| Validation officielle SIA 4010 | SIA / sous-commission compétente | Package officiel, résultats et attestation externe |

## Limites strictes

Le code ne peut pas inventer une donnée technique, signer à la place d'un ingénieur, choisir seul la catégorie normative de nécessité du froid, acheter ou redistribuer un standard sous licence, ni produire une attestation SIA 4010. Il ne peut pas non plus rendre conforme un modèle physique uniquement en changeant le rapport.

Le mode opératoire utilisateur est décrit dans `docs/user/WORKFLOW_CLIENT_SIA3802_FR.md` et la checklist de remise dans `docs/project/RELEASE_ACCEPTANCE_CHECKLIST.md`.
