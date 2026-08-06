"""Modèle d'une surface opaque de l'enveloppe ou d'une paroi intérieure."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Borne haute du U opaque. Le plafond de 2,0 W/(m2.K) n'est PAS une valeur
# normative : c'est un garde-fou de saisie, très au-dessus du pire cas de
# SIA 380/2:2022 tableau 3 (« Grenzwert »). Il intercepte les erreurs
# grossières -- unité confondue, valeur d'un vitrage saisie sur une paroi --
# sans jamais servir de critère de conformité.
U_VALUE_OPAQUE_MAX: float = 2.0

# Une surface opaque n'a pas d'orientation quand elle est horizontale ou
# intérieure ; `None` est donc une valeur légitime, distincte de 0.0 (nord).
ORIENTATION_MIN: float = 0.0
ORIENTATION_MAX: float = 360.0

AreaM2 = Annotated[float, Field(gt=0.0, description="Aire nette en m2, > 0.")]
UValue = Annotated[
    float,
    Field(
        gt=0.0,
        le=U_VALUE_OPAQUE_MAX,
        description="Coefficient U en W/(m2.K), 0 < U <= 2,0 pour un opaque.",
    ),
]


class Surface(BaseModel):
    """Surface opaque d'un local.

    Les vitrages ne sont PAS des `Surface` : leur U dépasse couramment la borne
    opaque de 2,0 (le vitrage du cas 600 d'EN ISO 52016-1 vaut U_W = 2,984).
    Ils relèvent de :class:`schemas.opening_schema.Opening`, qui ne porte pas
    ce plafond.

    Attributes:
        id: Identifiant de la surface dans le modèle IESVE.
        area: Aire nette en m2, strictement positive.
        u_value: Coefficient de transmission thermique en W/(m2.K).
        orientation: Azimut en degrés (0 = nord, 90 = est), `None` si la
            surface est horizontale ou intérieure.
        is_external: Vrai si la surface est en contact avec l'extérieur.

    Example:
        >>> Surface(id="MUR_S", area=21.6, u_value=0.17, orientation=180.0,
        ...         is_external=True).area
        21.6
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, description="Identifiant IESVE de la surface.")
    area: AreaM2
    u_value: UValue
    orientation: float | None = Field(
        default=None,
        ge=ORIENTATION_MIN,
        le=ORIENTATION_MAX,
        description="Azimut en degrés, None si horizontale ou intérieure.",
    )
    is_external: bool = Field(
        default=True, description="Vrai si la surface donne sur l'extérieur."
    )

    @field_validator("id")
    @classmethod
    def _identifiant_non_blanc(cls, valeur: str) -> str:
        """Refuse un identifiant fait uniquement d'espaces.

        Args:
            valeur: Identifiant proposé.

        Returns:
            str: L'identifiant débarrassé de ses espaces de bord.

        Raises:
            ValueError: Si l'identifiant est vide une fois élagué.
        """
        elague = valeur.strip()
        if not elague:
            raise ValueError("l'identifiant de surface ne peut pas être vide")
        return elague

    @property
    def is_horizontal(self) -> bool:
        """Indique si la surface est horizontale (aucune orientation).

        Returns:
            bool: Vrai lorsque `orientation` est `None`.
        """
        return self.orientation is None
