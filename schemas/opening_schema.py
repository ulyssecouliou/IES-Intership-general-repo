"""Modèle d'une ouverture : vitrage, porte ou ouvrant de ventilation."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

# PAS de plafond à 2,0 ici, contrairement aux surfaces opaques. Un vitrage
# dépasse couramment cette valeur : celui du cas 600 d'EN ISO 52016-1
# chapitre 7 vaut U_W = 2,984 W/(m2.K) sous les résistances superficielles
# normatives (R_se = 0,04 ; R_si = 0,13). Appliquer la borne opaque aux
# ouvertures rejetterait un cas de test officiel.
U_VALUE_OPENING_MAX: float = 10.0

AreaM2 = Annotated[float, Field(gt=0.0, description="Aire de l'ouverture en m2, > 0.")]
GValue = Annotated[
    float,
    Field(ge=0.0, le=1.0, description="Facteur solaire g, sans unité, 0 <= g <= 1."),
]
UValueOpening = Annotated[
    float,
    Field(gt=0.0, le=U_VALUE_OPENING_MAX, description="Coefficient U en W/(m2.K)."),
]


class OpeningType(str, Enum):
    """Nature d'une ouverture.

    `WINDOW` et `DOOR` participent au bilan thermique ; `VENT` désigne un
    ouvrant dont le rôle est aéraulique et dont le facteur solaire n'a pas de
    sens physique.
    """

    WINDOW = "window"
    DOOR = "door"
    VENT = "vent"


class Opening(BaseModel):
    """Ouverture pratiquée dans une surface de l'enveloppe.

    Attributes:
        id: Identifiant de l'ouverture dans le modèle IESVE.
        area: Aire de l'ouverture en m2, strictement positive.
        g_value: Facteur solaire total, entre 0 et 1 inclus.
        u_value: Coefficient de transmission thermique en W/(m2.K).
        opening_type: Nature de l'ouverture.
        host_surface_id: Identifiant de la surface qui la porte, si connue.

    Example:
        >>> Opening(id="F_S1", area=6.0, g_value=0.787, u_value=2.984).u_value
        2.984
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, description="Identifiant IESVE de l'ouverture.")
    area: AreaM2
    g_value: GValue
    u_value: UValueOpening
    opening_type: OpeningType = Field(
        default=OpeningType.WINDOW, description="Nature de l'ouverture."
    )
    host_surface_id: str | None = Field(
        default=None, description="Surface porteuse, si le modèle la fournit."
    )

    @field_validator("id")
    @classmethod
    def _identifiant_non_blanc(cls, valeur: str) -> str:
        """Refuse un identifiant fait uniquement d'espaces.

        Args:
            valeur: Identifiant proposé.

        Returns:
            str: L'identifiant élagué.

        Raises:
            ValueError: Si l'identifiant est vide une fois élagué.
        """
        elague = valeur.strip()
        if not elague:
            raise ValueError("l'identifiant d'ouverture ne peut pas être vide")
        return elague

    @property
    def solar_aperture(self) -> float:
        """Surface solaire équivalente, en m2.

        Produit `area * g_value`. C'est une grandeur de commodité pour
        comparer des ouvertures entre elles ; elle ne remplace aucun calcul
        normatif d'apport solaire.

        Returns:
            float: Aire multipliée par le facteur solaire.
        """
        return self.area * self.g_value
