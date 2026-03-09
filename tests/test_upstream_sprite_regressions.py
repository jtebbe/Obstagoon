from pathlib import Path

from obstagoon.extract.parsers.sprites import parse_sprite_assets


def test_upstream_basculegion_alias_and_female_subdir_do_not_fall_back_to_nidoran(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'graphics/pokemon/basculegion').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/basculegion/front.png').write_text('base')
    (project / 'graphics/pokemon/basculegion/f').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/basculegion/f/front.png').write_text('female')
    (project / 'graphics/pokemon/nidoran_m').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/nidoran_m/anim_front.png').write_text('wrong-m')
    (project / 'graphics/pokemon/nidoran_f').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/nidoran_f/anim_front.png').write_text('wrong-f')

    species = {
        'SPECIES_BASCULEGION': {'graphics': {'frontPic': 'gMonFrontPic_BasculegionM'}},
        'SPECIES_BASCULEGION_F': {'graphics': {'frontPic': 'gMonFrontPic_BasculegionF'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_BASCULEGION']['frontPic'] == 'graphics/pokemon/basculegion/front.png'
    assert sprites['SPECIES_BASCULEGION_F']['frontPic'] == 'graphics/pokemon/basculegion/f/front.png'


def test_upstream_nested_form_dirs_beat_unrelated_front_sprites(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    for family, form in [('flabebe', 'red_flower'), ('floette', 'red_flower'), ('florges', 'red_flower')]:
        (project / 'graphics/pokemon' / family / form).mkdir(parents=True, exist_ok=True)
        (project / 'graphics/pokemon' / family / form / 'front.png').write_text(f'{family}-{form}')
    (project / 'graphics/pokemon/vivillon/icy_snow').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/vivillon/icy_snow/front.png').write_text('vivillon-icy-snow')

    # Unrelated generic front sprite that should never win these lookups.
    (project / 'graphics/pokemon/muk').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/muk/front.png').write_text('wrong')

    species = {
        'SPECIES_FLABEBE_RED_FLOWER': {'graphics': {'frontPic': 'gMonFrontPic_FlabebeRedFlower'}},
        'SPECIES_FLOETTE_RED_FLOWER': {'graphics': {'frontPic': 'gMonFrontPic_FloetteRedFlower'}},
        'SPECIES_FLORGES_RED_FLOWER': {'graphics': {'frontPic': 'gMonFrontPic_FlorgesRedFlower'}},
        'SPECIES_VIVILLON_ICY_SNOW_PATTERN': {'graphics': {'frontPic': 'gMonFrontPic_VivillonIcySnow'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_FLABEBE_RED_FLOWER']['frontPic'] == 'graphics/pokemon/flabebe/red_flower/front.png'
    assert sprites['SPECIES_FLOETTE_RED_FLOWER']['frontPic'] == 'graphics/pokemon/floette/red_flower/front.png'
    assert sprites['SPECIES_FLORGES_RED_FLOWER']['frontPic'] == 'graphics/pokemon/florges/red_flower/front.png'
    assert sprites['SPECIES_VIVILLON_ICY_SNOW_PATTERN']['frontPic'] == 'graphics/pokemon/vivillon/icy_snow/front.png'


def test_upstream_form_change_dirs_resolve_for_mega_and_gmax(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'graphics/pokemon/charizard').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/charizard/front.png').write_text('base')
    (project / 'graphics/pokemon/charizard/mega_x').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/charizard/mega_x/front.png').write_text('mega-x')
    (project / 'graphics/pokemon/charizard/gmax').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/charizard/gmax/front.png').write_text('gmax')
    (project / 'graphics/pokemon/charizard_mega_y').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/charizard_mega_y/front.png').write_text('mega-y')

    species = {
        'SPECIES_CHARIZARD': {'graphics': {'frontPic': 'gMonFrontPic_Charizard'}},
        'SPECIES_CHARIZARD_MEGA_X': {'graphics': {'frontPic': 'gMonFrontPic_CharizardMegaX'}},
        'SPECIES_CHARIZARD_GMAX': {'graphics': {'frontPic': 'gMonFrontPic_CharizardGmax'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_CHARIZARD']['frontPic'] == 'graphics/pokemon/charizard/front.png'
    assert sprites['SPECIES_CHARIZARD_MEGA_X']['frontPic'] == 'graphics/pokemon/charizard/mega_x/front.png'
    assert sprites['SPECIES_CHARIZARD_GMAX']['frontPic'] == 'graphics/pokemon/charizard/gmax/front.png'


def test_upstream_zygarde_10_percent_form_dir_resolves_from_species_slug_alias(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'graphics/pokemon/zygarde').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/zygarde/front.png').write_text('base')
    (project / 'graphics/pokemon/zygarde/10_percent').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/zygarde/10_percent/front.png').write_text('10-percent')

    species = {
        'SPECIES_ZYGARDE': {'graphics': {'frontPic': 'gMonFrontPic_Zygarde'}},
        'SPECIES_ZYGARDE_10': {'graphics': {'frontPic': 'gMonFrontPic_Zygarde10'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_ZYGARDE']['frontPic'] == 'graphics/pokemon/zygarde/front.png'
    assert sprites['SPECIES_ZYGARDE_10']['frontPic'] == 'graphics/pokemon/zygarde/10_percent/front.png'


def test_upstream_zygarde_10_percent_form_dir_resolves_from_token_alias(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'graphics/pokemon/zygarde').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/zygarde/10_percent').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/zygarde/10_percent/front.png').write_text('10-percent')

    species = {
        'SPECIES_ZYGARDE_10': {'graphics': {'frontPic': 'gMonFrontPic_Zygarde10Percent'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_ZYGARDE_10']['frontPic'] == 'graphics/pokemon/zygarde/10_percent/front.png'


def test_upstream_zygarde_10_power_construct_and_aura_break_use_10_percent_anim_front(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'graphics/pokemon/zygarde').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/zygarde/front.png').write_text('base')
    (project / 'graphics/pokemon/zygarde/10_percent').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/zygarde/10_percent/anim_front.png').write_text('10-percent-anim')

    species = {
        'SPECIES_ZYGARDE_10_AURA_BREAK': {'graphics': {'frontPic': 'gMonFrontPic_Zygarde10AuraBreak'}},
        'SPECIES_ZYGARDE_10_POWER_CONSTRUCT': {'graphics': {'frontPic': 'gMonFrontPic_Zygarde10PowerConstruct'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_ZYGARDE_10_AURA_BREAK']['frontPic'] == 'graphics/pokemon/zygarde/10_percent/anim_front.png'
    assert sprites['SPECIES_ZYGARDE_10_POWER_CONSTRUCT']['frontPic'] == 'graphics/pokemon/zygarde/10_percent/anim_front.png'
