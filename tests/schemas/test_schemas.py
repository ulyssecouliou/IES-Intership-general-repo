"""Tests des schémas Pydantic du domaine SIA 4010.

Les tests les plus importants ne vérifient pas qu'un modèle valide passe : ils
vérifient qu'un modèle **invalide échoue**. Une borne qui n'arrête rien est
pire qu'une absence de borne, parce qu'elle rassure.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas import (
    Opening,
    OpeningType,
    Room,
    Surface,
    TestResult,
    TestStatus,
    ValidationClass,
    ValidationClassStatus,
)

# ---------------------------------------------------------------------------
# Surface
# ---------------------------------------------------------------------------


def test_surface_valide() -> None:
    surface = Surface(id="MUR_S", area=21.6, u_value=0.17, orientation=180.0)
    assert surface.area == 21.6
    assert surface.is_external is True
    assert surface.is_horizontal is False


@pytest.mark.parametrize("aire", [0.0, -1.0])
def test_surface_refuse_une_aire_non_positive(aire: float) -> None:
    with pytest.raises(ValidationError):
        Surface(id="S", area=aire, u_value=0.2)


@pytest.mark.parametrize("u", [0.0, -0.1, 2.0001, 50.0])
def test_surface_refuse_un_u_hors_plage(u: float) -> None:
    with pytest.raises(ValidationError):
        Surface(id="S", area=1.0, u_value=u)


def test_surface_accepte_la_borne_haute_exacte() -> None:
    """La borne est inclusive : 2,0 doit passer, 2,0001 non."""
    assert Surface(id="S", area=1.0, u_value=2.0).u_value == 2.0


def test_surface_sans_orientation_est_horizontale() -> None:
    assert Surface(id="TOIT", area=100.0, u_value=0.15).is_horizontal is True


def test_surface_refuse_un_identifiant_blanc() -> None:
    with pytest.raises(ValidationError):
        Surface(id="   ", area=1.0, u_value=0.2)


def test_surface_refuse_un_champ_inconnu() -> None:
    """`extra="forbid"` : une faute de frappe ne doit pas être avalée."""
    with pytest.raises(ValidationError):
        Surface(id="S", area=1.0, u_value=0.2, u_valeu=0.3)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Opening
# ---------------------------------------------------------------------------


def test_opening_accepte_le_vitrage_du_cas_600() -> None:
    """Cas réel : U_W = 2,984 pour le vitrage du cas 600 d'EN ISO 52016-1
    chapitre 7, sous R_se = 0,04 et R_si = 0,13.

    Appliquer aux ouvertures la borne opaque de 2,0 rejetterait un cas de test
    officiel. Ce test verrouille la distinction.
    """
    fenetre = Opening(id="F1", area=6.0, g_value=0.787, u_value=2.984)
    assert fenetre.u_value == 2.984
    with pytest.raises(ValidationError):
        Surface(id="S1", area=6.0, u_value=2.984)


@pytest.mark.parametrize("g", [-0.01, 1.01])
def test_opening_refuse_un_g_hors_plage(g: float) -> None:
    with pytest.raises(ValidationError):
        Opening(id="F", area=1.0, g_value=g, u_value=1.0)


@pytest.mark.parametrize("g", [0.0, 1.0])
def test_opening_accepte_les_bornes_de_g(g: float) -> None:
    """0 et 1 sont inclus : un store totalement opaque et un trou béant."""
    assert Opening(id="F", area=1.0, g_value=g, u_value=1.0).g_value == g


def test_opening_surface_solaire_equivalente() -> None:
    fenetre = Opening(id="F", area=6.0, g_value=0.5, u_value=1.2)
    assert fenetre.solar_aperture == 3.0


def test_opening_type_par_defaut_est_une_fenetre() -> None:
    assert Opening(id="F", area=1.0, g_value=0.5, u_value=1.0).opening_type is (
        OpeningType.WINDOW
    )


# ---------------------------------------------------------------------------
# Room
# ---------------------------------------------------------------------------


def test_room_agrege_ses_aires() -> None:
    local = Room(
        id="R1",
        volume=30.0,
        surfaces=(
            Surface(id="S1", area=10.0, u_value=0.2),
            Surface(id="S2", area=5.0, u_value=0.3, is_external=False),
        ),
        openings=(Opening(id="O1", area=2.0, g_value=0.6, u_value=1.1),),
    )
    assert local.opaque_area == 15.0
    assert local.opening_area == 2.0
    assert [s.id for s in local.external_surfaces] == ["S1"]


@pytest.mark.parametrize("volume", [0.0, -5.0])
def test_room_refuse_un_volume_non_positif(volume: float) -> None:
    with pytest.raises(ValidationError):
        Room(id="R", volume=volume)


def test_room_refuse_des_identifiants_de_surface_en_doublon() -> None:
    """Un doublon ferait disparaître silencieusement une surface au moindre
    regroupement par clé."""
    with pytest.raises(ValidationError, match="doublon"):
        Room(
            id="R",
            volume=10.0,
            surfaces=(
                Surface(id="S", area=1.0, u_value=0.2),
                Surface(id="S", area=2.0, u_value=0.3),
            ),
        )


def test_room_refuse_des_identifiants_douverture_en_doublon() -> None:
    with pytest.raises(ValidationError, match="doublon"):
        Room(
            id="R",
            volume=10.0,
            openings=(
                Opening(id="O", area=1.0, g_value=0.5, u_value=1.0),
                Opening(id="O", area=2.0, g_value=0.5, u_value=1.0),
            ),
        )


def test_room_usage_est_libre_et_non_enumere() -> None:
    """Les codes SIA 2024 ne sont pas tous en notre possession : figer une
    liste partielle rejetterait des usages valides."""
    assert Room(id="R", volume=10.0, usage="12.09").usage == "12.09"


# ---------------------------------------------------------------------------
# TestResult
# ---------------------------------------------------------------------------


def test_result_defaut_est_non_evaluable() -> None:
    """Jamais de succès par défaut."""
    resultat = TestResult(test_name="test_7", criterion_source="classeur SIA")
    assert resultat.status is TestStatus.NOT_CHECKABLE
    assert resultat.is_passing is False


def test_result_succes_sous_reserve_compte_comme_un_succes() -> None:
    """Le comparer au seul PASS le transformerait en échec silencieux."""
    resultat = TestResult(
        test_name="t",
        status=TestStatus.PASS_WITH_RESERVATION,
        criterion_source="classeur SIA",
    )
    assert resultat.is_passing is True


def test_result_echec_sans_motif_est_refuse() -> None:
    with pytest.raises(ValidationError, match="motif"):
        TestResult(test_name="t", status=TestStatus.FAIL, criterion_source="x")


def test_result_echec_motive_est_accepte() -> None:
    resultat = TestResult(
        test_name="t",
        status=TestStatus.FAIL,
        errors=("hors bande",),
        criterion_source="x",
    )
    assert resultat.errors == ("hors bande",)


def test_result_exige_une_source_de_critere() -> None:
    """Aucun verdict ne doit circuler sans son article."""
    with pytest.raises(ValidationError):
        TestResult(test_name="t")  # type: ignore[call-arg]


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_result_refuse_un_score_hors_plage(score: float) -> None:
    with pytest.raises(ValidationError):
        TestResult(test_name="t", criterion_source="x", score=score)


# ---------------------------------------------------------------------------
# ValidationClass
# ---------------------------------------------------------------------------


def _ok(nom: str) -> TestResult:
    return TestResult(test_name=nom, status=TestStatus.PASS, criterion_source="x")


def _echec(nom: str) -> TestResult:
    return TestResult(
        test_name=nom, status=TestStatus.FAIL, errors=("motif",), criterion_source="x"
    )


def test_classe_validee_quand_tous_les_tests_exiges_passent() -> None:
    classe = ValidationClass(
        class_name="5", required_tests=("test_7",), results={"test_7": _ok("test_7")}
    )
    assert classe.status is ValidationClassStatus.VALIDATED
    assert classe.is_validated is True


def test_classe_incomplete_si_un_test_exige_manque() -> None:
    """Cœur du sujet : un test vert ne suffit pas si un autre est absent."""
    classe = ValidationClass(
        class_name="4A",
        required_tests=("test_1", "test_7"),
        results={"test_7": _ok("test_7")},
    )
    assert classe.status is ValidationClassStatus.INCOMPLETE
    assert classe.is_validated is False
    assert classe.missing_tests == ("test_1",)
    assert classe.covered_tests == ("test_7",)


def test_un_echec_prime_sur_une_absence() -> None:
    """Un échec avéré est plus grave qu'une absence et ne doit pas disparaître
    derrière « incomplète »."""
    classe = ValidationClass(
        class_name="4A",
        required_tests=("test_1", "test_7"),
        results={"test_7": _echec("test_7")},
    )
    assert classe.status is ValidationClassStatus.FAILED


def test_classe_non_concluante_si_un_test_present_nest_pas_evaluable() -> None:
    inconnu = TestResult(test_name="test_7", criterion_source="x")
    classe = ValidationClass(
        class_name="5", required_tests=("test_7",), results={"test_7": inconnu}
    )
    assert classe.status is ValidationClassStatus.NOT_CONCLUSIVE


def test_classe_refuse_une_cle_incoherente_avec_le_nom_du_test() -> None:
    """Une clé qui ne correspond pas fausserait le calcul de couverture."""
    with pytest.raises(ValidationError, match="incohérente"):
        ValidationClass(
            class_name="5",
            required_tests=("test_7",),
            results={"test_1": _ok("test_7")},
        )


def test_classe_exige_au_moins_un_test() -> None:
    with pytest.raises(ValidationError):
        ValidationClass(class_name="X", required_tests=())


def test_classe_sans_aucun_resultat_est_incomplete() -> None:
    classe = ValidationClass(class_name="5", required_tests=("test_7",))
    assert classe.status is ValidationClassStatus.INCOMPLETE
    assert classe.missing_tests == ("test_7",)
