"""Tests des dépôts d'accès aux données.

L'exigence centrale : **aucun dépôt ne doit produire une valeur plausible en
l'absence de donnée réelle.** Un fichier officiel manquant lève une erreur qui
le nomme ; un modèle VE illisible lève aussi, plutôt que de renvoyer une liste
vide qui se lirait comme « bâtiment sans locaux ».
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.repositories import (
    JsonIESVERepository,
    LiveIESVERepository,
    OfficialFileMissingError,
    SIA4010Repository,
)
from core.repositories.iesve_repository import RoomNotFoundError

INSTANTANE = {
    "rooms": [
        {
            "id": "R1",
            "volume": 30.0,
            "usage": "4.04",
            "surfaces": [{"id": "S1", "area": 12.0, "u_value": 0.17}],
            "openings": [{"id": "O1", "area": 3.0, "g_value": 0.6, "u_value": 1.1}],
        },
        {"id": "R2", "volume": 45.0, "usage": "3.01"},
    ]
}


# ---------------------------------------------------------------------------
# JsonIESVERepository
# ---------------------------------------------------------------------------


def test_charge_un_instantane_valide() -> None:
    depot = JsonIESVERepository.from_mapping(INSTANTANE)
    assert len(depot.get_rooms()) == 2
    assert depot.total_volume() == 75.0


def test_retrouve_un_local_par_identifiant() -> None:
    depot = JsonIESVERepository.from_mapping(INSTANTANE)
    assert depot.get_room("R2").volume == 45.0


def test_local_inconnu_leve_et_liste_les_disponibles() -> None:
    """Le message doit permettre de corriger sans relire le JSON."""
    depot = JsonIESVERepository.from_mapping(INSTANTANE)
    with pytest.raises(RoomNotFoundError) as capture:
        depot.get_room("R99")
    assert "R1" in str(capture.value) and "R2" in str(capture.value)


def test_filtre_par_usage() -> None:
    depot = JsonIESVERepository.from_mapping(INSTANTANE)
    assert [r.id for r in depot.get_rooms_by_usage("4.04")] == ["R1"]
    assert depot.get_rooms_by_usage("9.99") == ()


def test_instantane_sans_cle_rooms_est_refuse() -> None:
    with pytest.raises(ValueError, match="rooms"):
        JsonIESVERepository.from_mapping({"locaux": []})


def test_local_invalide_est_refuse_a_la_lecture() -> None:
    """Un volume nul doit échouer maintenant, pas au moment du calcul."""
    with pytest.raises(ValueError):
        JsonIESVERepository.from_mapping({"rooms": [{"id": "R", "volume": 0.0}]})


def test_charge_depuis_un_fichier(tmp_path: Path) -> None:
    chemin = tmp_path / "instantane.json"
    chemin.write_text(json.dumps(INSTANTANE), encoding="utf-8")
    assert JsonIESVERepository.from_path(chemin).total_volume() == 75.0


def test_fichier_absent_leve_avec_le_chemin() -> None:
    with pytest.raises(FileNotFoundError, match="introuvable"):
        JsonIESVERepository.from_path("nexiste_pas.json")


def test_depot_vide_est_licite_mais_vide() -> None:
    depot = JsonIESVERepository.from_mapping({"rooms": []})
    assert depot.get_rooms() == ()
    assert depot.total_volume() == 0.0


# ---------------------------------------------------------------------------
# LiveIESVERepository
# ---------------------------------------------------------------------------


def test_le_depot_ve_refuse_de_deviner_la_correspondance() -> None:
    """Renvoyer une liste vide ferait passer un modèle non lu pour un modèle
    sans locaux. On lève, avec le motif."""
    depot = LiveIESVERepository(model=object())
    with pytest.raises(NotImplementedError, match="correspondance"):
        depot.get_rooms()


def test_le_depot_ve_explique_labsence_du_module_iesve() -> None:
    """Hors VEScripts, le message doit orienter vers JsonIESVERepository."""
    depot = LiveIESVERepository()
    with pytest.raises((RuntimeError, NotImplementedError)) as capture:
        depot.get_rooms()
    assert "iesve" in str(capture.value) or "correspondance" in str(capture.value)


# ---------------------------------------------------------------------------
# SIA4010Repository
# ---------------------------------------------------------------------------


def test_racine_absente_ne_declare_aucun_test(tmp_path: Path) -> None:
    depot = SIA4010Repository(tmp_path / "inexistant")
    assert depot.available_tests() == ()


def test_liste_les_tests_presents(tmp_path: Path) -> None:
    (tmp_path / "test_1").mkdir()
    (tmp_path / "test_7").mkdir()
    (tmp_path / "notes.txt").write_text("ignoré", encoding="utf-8")
    assert SIA4010Repository(tmp_path).available_tests() == ("test_1", "test_7")


def test_inventaire_dun_test_incomplet(tmp_path: Path) -> None:
    dossier = tmp_path / "test_7"
    dossier.mkdir()
    (dossier / "specification.pdf").write_bytes(b"%PDF-")
    assets = SIA4010Repository(tmp_path).get_assets("test_7")
    assert assets.specification is not None
    assert assets.evaluation is None
    assert assets.is_complete is False


def test_inventaire_dun_test_complet_et_ses_extras(tmp_path: Path) -> None:
    dossier = tmp_path / "test_7"
    dossier.mkdir()
    (dossier / "specification.pdf").write_bytes(b"%PDF-")
    (dossier / "evaluation.xlsx").write_bytes(b"PK")
    (dossier / "Lastverlaeufe.xlsx").write_bytes(b"PK")
    assets = SIA4010Repository(tmp_path).get_assets("test_7")
    assert assets.is_complete is True
    assert [c.name for c in assets.extras] == ["Lastverlaeufe.xlsx"]


def test_classeur_manquant_leve_en_nommant_le_fichier(tmp_path: Path) -> None:
    """Le message doit nommer le fichier ET rappeler où l'obtenir : un dossier
    bâti sur un fichier approché serait invalidé bien plus tard."""
    with pytest.raises(OfficialFileMissingError) as capture:
        SIA4010Repository(tmp_path).require_evaluation("test_7")
    message = str(capture.value)
    assert "evaluation.xlsx" in message
    assert "sia4010" in message


def test_specification_manquante_leve_aussi(tmp_path: Path) -> None:
    with pytest.raises(OfficialFileMissingError, match="specification.pdf"):
        SIA4010Repository(tmp_path).require_specification("test_1")


def test_alias_avec_ou_sans_prefixe_designent_le_meme_dossier(tmp_path: Path) -> None:
    depot = SIA4010Repository(tmp_path)
    assert depot.test_dir("test_4") == depot.test_dir("4")
