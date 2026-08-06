"""Noyau applicatif : accès aux données, fabriques et stratégies de validation.

Trois couches, volontairement séparées :

* ``core.repositories`` — d'où viennent les données (IESVE, fichiers SIA).
* ``core.factories``   — comment on instancie un checker sans le nommer en dur.
* ``core.strategies``  — selon quel algorithme on valide (PDF ou officiel).

Règle transverse : **aucun module de ce paquet n'importe ``iesve`` au niveau
module**. L'import est différé dans les implémentations qui en ont besoin, de
sorte que la totalité de ``core`` reste importable en intégration continue,
sans licence VE.
"""
