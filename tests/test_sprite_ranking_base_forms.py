from pathlib import Path

from obstagoon.extract.parsers.sprites import _rank_candidate


def test_base_species_front_beats_gmax(tmp_path: Path):
    base = tmp_path / "graphics" / "pokemon" / "charizard"
    gmax = base / "gmax"
    base.mkdir(parents=True)
    gmax.mkdir(parents=True)
    front = base / "front.png"
    gmax_front = gmax / "front.png"
    front.write_text("x")
    gmax_front.write_text("x")
    assert _rank_candidate(tmp_path, front, "SPECIES_CHARIZARD", "frontPic", "charizard") > _rank_candidate(tmp_path, gmax_front, "SPECIES_CHARIZARD", "frontPic", "charizard")


def test_base_species_back_beats_shiny_or_paletteish(tmp_path: Path):
    base = tmp_path / "graphics" / "pokemon" / "charizard"
    base.mkdir(parents=True)
    back = base / "back.png"
    shiny = base / "back_shiny.png"
    pal = base / "back.pal.png"
    back.write_text("x")
    shiny.write_text("x")
    pal.write_text("x")
    best = _rank_candidate(tmp_path, back, "SPECIES_CHARIZARD", "backPic", "charizard")
    assert best > _rank_candidate(tmp_path, shiny, "SPECIES_CHARIZARD", "backPic", "charizard")
    assert best > _rank_candidate(tmp_path, pal, "SPECIES_CHARIZARD", "backPic", "charizard")


def test_base_alcremie_front_beats_flavor_and_gmax(tmp_path: Path):
    base = tmp_path / "graphics" / "pokemon" / "alcremie"
    vanilla = base / "vanilla_cream" / "strawberry"
    gmax = base / "gmax"
    base.mkdir(parents=True)
    vanilla.mkdir(parents=True)
    gmax.mkdir(parents=True)
    front = base / "front.png"
    vanilla_front = vanilla / "front.png"
    gmax_front = gmax / "front.png"
    front.write_text("x")
    vanilla_front.write_text("x")
    gmax_front.write_text("x")
    best = _rank_candidate(tmp_path, front, "SPECIES_ALCREMIE", "frontPic", "alcremie")
    assert best > _rank_candidate(tmp_path, vanilla_front, "SPECIES_ALCREMIE", "frontPic", "alcremie")
    assert best > _rank_candidate(tmp_path, gmax_front, "SPECIES_ALCREMIE", "frontPic", "alcremie")
