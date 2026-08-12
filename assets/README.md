# assets

Images the generated reports embed. Small, versioned, and owned by whoever
issues the report.

## Le logo du bureau

`config/company_profile.json` porte `logo_path`. Le chemin peut être absolu ou
relatif à la racine du dépôt.

Contraintes réelles, lues dans `swiss_sia/company_profile.py` et non supposées :

- extensions acceptées : `.png`, `.jpg`, `.jpeg` — toute autre valeur est
  ignorée en silence et le letterhead s'imprime sans logo ;
- PNG en niveaux de gris ou RVB, **non entrelacé, sans canal alpha** : c'est la
  limite de l'encodeur PDF embarqué, pas un choix esthétique ;
- un fichier absent ou illisible **ne bloque jamais** le rapport. Le letterhead
  se dessine sans lui, et la ligne est journalisée. Un rapport ne se perd pas
  pour une image.

Format utile en pratique : environ 3:1, dans les 480 × 160 px. Le letterhead
réserve 17 mm de haut ; au-delà l'image est mise à l'échelle.

## `office_logo.placeholder.png`

Un aplat navy avec un filet bleu accent, construit à partir des tokens de
`ui/design.py`. Il n'imite aucune marque : il existe pour que le chemin
logo → letterhead → PDF soit exercé de bout en bout avant qu'un vrai fichier
arrive. Remplacez-le par celui du bureau, ou changez `logo_path`.

Rien dans le rapport ne dépend de cette image.
