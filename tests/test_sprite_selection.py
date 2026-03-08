from pathlib import Path

from obstagoon.extract.parsers.sprites import _build_lookup_index, _resolve_path


def test_base_form_front_pic_not_gmax(tmp_path: Path):
    (tmp_path / "graphics/pokemon/charizard").mkdir(parents=True)
    (tmp_path / "graphics/pokemon/charizard/front.png").write_text("x")
    (tmp_path / "graphics/pokemon/charizard-gmax").mkdir(parents=True)
    (tmp_path / "graphics/pokemon/charizard-gmax/front.png").write_text("x")
    files = [tmp_path / "graphics/pokemon/charizard/front.png", tmp_path / "graphics/pokemon/charizard-gmax/front.png"]
    idx = _build_lookup_index(tmp_path, files)
    resolved, ranked = _resolve_path(tmp_path, idx, "SPECIES_CHARIZARD", "frontPic", "gMonFrontPic_Charizard")
    assert resolved == "graphics/pokemon/charizard/front.png"


def test_back_pic_not_shiny_palette(tmp_path: Path):
    (tmp_path / "graphics/pokemon/charizard").mkdir(parents=True)
    (tmp_path / "graphics/pokemon/charizard/back.png").write_text("x")
    (tmp_path / "graphics/pokemon/charizard/shiny.pal").write_text("x")
    files = [tmp_path / "graphics/pokemon/charizard/back.png", tmp_path / "graphics/pokemon/charizard/shiny.pal"]
    idx = _build_lookup_index(tmp_path, files)
    resolved, ranked = _resolve_path(tmp_path, idx, "SPECIES_CHARIZARD", "backPic", "gMonBackPic_Charizard")
    assert resolved == "graphics/pokemon/charizard/back.png"


def test_base_species_prefers_non_form_front(tmp_path):
    project = tmp_path / 'proj'
    (project / 'graphics' / 'pokemon' / 'charizard').mkdir(parents=True)
    (project / 'graphics' / 'pokemon' / 'charizard_gmax').mkdir(parents=True)
    base = project / 'graphics' / 'pokemon' / 'charizard' / 'front.png'
    gmax = project / 'graphics' / 'pokemon' / 'charizard_gmax' / 'front.png'
    base.write_text('base')
    gmax.write_text('gmax')
    from obstagoon.extract.parsers.sprites import _build_lookup_index, _resolve_path
    idx = _build_lookup_index(project, [base, gmax])
    resolved, _ = _resolve_path(project, idx, 'SPECIES_CHARIZARD', 'frontPic', 'gMonFrontPic_Charizard')
    assert resolved == 'graphics/pokemon/charizard/front.png'


def test_back_species_prefers_non_shiny_back(tmp_path):
    project = tmp_path / 'proj'
    (project / 'graphics' / 'pokemon' / 'pidgeot' / 'back').mkdir(parents=True)
    (project / 'graphics' / 'pokemon' / 'pidgeot' / 'shiny').mkdir(parents=True)
    back = project / 'graphics' / 'pokemon' / 'pidgeot' / 'back' / 'back.png'
    shiny = project / 'graphics' / 'pokemon' / 'pidgeot' / 'shiny' / 'back.png'
    back.write_text('back')
    shiny.write_text('shiny')
    from obstagoon.extract.parsers.sprites import _build_lookup_index, _resolve_path
    idx = _build_lookup_index(project, [back, shiny])
    resolved, _ = _resolve_path(project, idx, 'SPECIES_PIDGEOT', 'backPic', 'gMonBackPic_Pidgeot')
    assert resolved == 'graphics/pokemon/pidgeot/back/back.png'


def test_pikachu_base_anim_front_beats_phd(tmp_path: Path):
    from obstagoon.extract.parsers.sprites import _build_lookup_index, _resolve_path
    base = tmp_path / 'graphics' / 'pokemon' / 'pikachu'
    phd = tmp_path / 'graphics' / 'pokemon' / 'pikachu_phd'
    base.mkdir(parents=True)
    phd.mkdir(parents=True)
    anim_front = base / 'anim_front.png'
    phd_front = phd / 'front.png'
    anim_front.write_text('x')
    phd_front.write_text('x')
    idx = _build_lookup_index(tmp_path, [anim_front, phd_front])
    resolved, _ = _resolve_path(tmp_path, idx, 'SPECIES_PIKACHU', 'frontPic', 'gMonFrontPic_Pikachu')
    assert resolved == 'graphics/pokemon/pikachu/anim_front.png'
