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

def test_upstream_arceus_forms_do_not_pick_overworld_when_form_dir_lacks_front_sprite(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'graphics/pokemon/arceus').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/arceus/anim_front.png').write_text('base-front')
    (project / 'graphics/pokemon/arceus/psychic').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/arceus/psychic/overworld.png').write_text('wrong-overworld')
    (project / 'graphics/pokemon/arceus/psychic/normal.pal').write_text('pal')

    species = {
        'SPECIES_ARCEUS_PSYCHIC': {'graphics': {'frontPic': 'gMonFrontPic_ArceusPsychic'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_ARCEUS_PSYCHIC']['frontPic'] == 'graphics/pokemon/arceus/anim_front.png'


def test_upstream_male_and_pokeball_form_dirs_resolve_to_own_fronts(tmp_path: Path) -> None:
    from obstagoon.extract.parsers.sprites import parse_sprite_assets

    project = tmp_path
    (project / 'graphics/pokemon/indeedee/front.png').parent.mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/indeedee/front.png').write_text('base')
    (project / 'graphics/pokemon/indeedee/m/front.png').parent.mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/indeedee/m/front.png').write_text('male')

    (project / 'graphics/pokemon/oinkologne/front.png').parent.mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/oinkologne/front.png').write_text('base')
    (project / 'graphics/pokemon/oinkologne/m/front.png').parent.mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/oinkologne/m/front.png').write_text('male')

    (project / 'graphics/pokemon/vivillon/front.png').parent.mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/vivillon/front.png').write_text('base')
    (project / 'graphics/pokemon/vivillon/pokeball/front.png').parent.mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/vivillon/pokeball/front.png').write_text('pokeball')
    (project / 'graphics/pokemon/vivillon/icy_snow/front.png').parent.mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/vivillon/icy_snow/front.png').write_text('icy-snow')

    species = {
        'SPECIES_INDEEDEE_MALE': {'graphics': {'frontPic': 'gMonFrontPic_IndeedeeMale'}},
        'SPECIES_OINKOLOGNE_MALE': {'graphics': {'frontPic': 'gMonFrontPic_OinkologneMale'}},
        'SPECIES_VIVILLON_POKE_BALL_PATTERN': {'graphics': {'frontPic': 'gMonFrontPic_VivillonPokeBall'}},
        'SPECIES_VIVILLON_ICY_SNOW_PATTERN': {'graphics': {'frontPic': 'gMonFrontPic_VivillonIcySnow'}},
    }
    sprites = parse_sprite_assets(project, species, cache_dir=project / '.cache')

    assert sprites['SPECIES_INDEEDEE_MALE']['frontPic'] == 'graphics/pokemon/indeedee/m/front.png'
    assert sprites['SPECIES_OINKOLOGNE_MALE']['frontPic'] == 'graphics/pokemon/oinkologne/m/front.png'
    assert sprites['SPECIES_VIVILLON_POKE_BALL_PATTERN']['frontPic'] == 'graphics/pokemon/vivillon/pokeball/front.png'
    assert sprites['SPECIES_VIVILLON_ICY_SNOW_PATTERN']['frontPic'] == 'graphics/pokemon/vivillon/icy_snow/front.png'


def test_upstream_form_palettes_resolve_to_own_normal_pal(tmp_path: Path) -> None:
    project = tmp_path
    (project / 'graphics/pokemon/indeedee').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/indeedee/normal.pal').write_text('base-pal')
    (project / 'graphics/pokemon/indeedee/m').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/indeedee/m/front.png').write_text('male-front')
    (project / 'graphics/pokemon/indeedee/m/normal.pal').write_text('male-pal')

    (project / 'graphics/pokemon/oinkologne').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/oinkologne/normal.pal').write_text('base-pal')
    (project / 'graphics/pokemon/oinkologne/m').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/oinkologne/m/front.png').write_text('male-front')
    (project / 'graphics/pokemon/oinkologne/m/normal.pal').write_text('male-pal')

    (project / 'graphics/pokemon/vivillon').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/vivillon/normal.pal').write_text('base-pal')
    (project / 'graphics/pokemon/vivillon/icy_snow').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/vivillon/icy_snow/front.png').write_text('icy-front')
    (project / 'graphics/pokemon/vivillon/icy_snow/normal.pal').write_text('icy-pal')

    (project / 'graphics/pokemon/arceus').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/arceus/normal.pal').write_text('base-pal')
    (project / 'graphics/pokemon/arceus/rock').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/arceus/rock/normal.pal').write_text('rock-pal')

    species = {
        'SPECIES_INDEEDEE_MALE': {'graphics': {'frontPic': 'IndeedeeMale', 'palette': 'IndeedeeMale'}},
        'SPECIES_OINKOLOGNE_MALE': {'graphics': {'frontPic': 'OinkologneMale', 'palette': 'OinkologneMale'}},
        'SPECIES_VIVILLON_ICY_SNOW_PATTERN': {'graphics': {'frontPic': 'VivillonIcySnowPattern', 'palette': 'VivillonIcySnowPattern'}},
        'SPECIES_ARCEUS_ROCK': {'graphics': {'frontPic': 'ArceusRock', 'palette': 'ArceusRock'}},
    }

    sprites = parse_sprite_assets(project, species)

    assert sprites['SPECIES_INDEEDEE_MALE']['palette'] == 'graphics/pokemon/indeedee/m/normal.pal'
    assert sprites['SPECIES_OINKOLOGNE_MALE']['palette'] == 'graphics/pokemon/oinkologne/m/normal.pal'
    assert sprites['SPECIES_VIVILLON_ICY_SNOW_PATTERN']['palette'] == 'graphics/pokemon/vivillon/icy_snow/normal.pal'
    assert sprites['SPECIES_ARCEUS_ROCK']['palette'] == 'graphics/pokemon/arceus/rock/normal.pal'


def test_upstream_alcremie_pattern_and_cream_palette_resolve_separately(tmp_path: Path) -> None:
    project = tmp_path
    (project / 'graphics/pokemon/alcremie').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/alcremie/front.png').write_text('base-front')
    (project / 'graphics/pokemon/alcremie/flower').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/alcremie/flower/front.png').write_text('flower-front')
    (project / 'graphics/pokemon/alcremie/flower/normal.pal').write_text('flower-pal')
    (project / 'graphics/pokemon/alcremie/flower/matcha_cream').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal').write_text('matcha-pal')

    species = {
        'SPECIES_ALCREMIE_FLOWER_MATCHA_CREAM': {'graphics': {'frontPic': 'gMonFrontPic_AlcremieFlower', 'palette': 'gMonPalette_AlcremieFlowerMatchaCream'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_ALCREMIE_FLOWER_MATCHA_CREAM']['frontPic'] == 'graphics/pokemon/alcremie/flower/front.png'
    assert sprites['SPECIES_ALCREMIE_FLOWER_MATCHA_CREAM']['palette'] == 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal'


def test_upstream_alcremie_pattern_token_in_middle_resolves_pattern_and_cream_palette(tmp_path: Path) -> None:
    project = tmp_path
    (project / 'graphics/pokemon/alcremie').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/alcremie/front.png').write_text('base-front')
    (project / 'graphics/pokemon/alcremie/flower').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/alcremie/flower/front.png').write_text('flower-front')
    (project / 'graphics/pokemon/alcremie/flower/normal.pal').write_text('flower-pal')
    (project / 'graphics/pokemon/alcremie/flower/matcha_cream').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal').write_text('matcha-pal')

    species = {
        'SPECIES_ALCREMIE_FLOWER_PATTERN_MATCHA_CREAM': {'graphics': {'frontPic': 'gMonFrontPic_Alcremie', 'palette': 'gMonPalette_AlcremieFlowerPatternMatchaCream'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_ALCREMIE_FLOWER_PATTERN_MATCHA_CREAM']['frontPic'] == 'graphics/pokemon/alcremie/flower/front.png'
    assert sprites['SPECIES_ALCREMIE_FLOWER_PATTERN_MATCHA_CREAM']['palette'] == 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal'


def test_upstream_alcremie_same_folder_palette_files_resolve_by_form_name(tmp_path: Path) -> None:
    project = tmp_path
    (project / 'graphics/pokemon/alcremie/star').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/alcremie/star/front.png').write_text('star-front')
    (project / 'graphics/pokemon/alcremie/star/star_default.pal').write_text('default-pal')
    (project / 'graphics/pokemon/alcremie/star/star_caramel_swirl.pal').write_text('caramel-pal')
    (project / 'graphics/pokemon/alcremie/star/star_shiny.pal').write_text('shiny-pal')

    species = {
        'SPECIES_ALCREMIE_STAR_DEFAULT': {'graphics': {'frontPic': 'gMonFrontPic_AlcremieStarDefault', 'palette': 'gMonPalette_AlcremieStarDefault'}},
        'SPECIES_ALCREMIE_STAR_CARAMEL_SWIRL': {'graphics': {'frontPic': 'gMonFrontPic_AlcremieStarCaramelSwirl', 'palette': 'gMonPalette_AlcremieStarCaramelSwirl'}},
    }
    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_ALCREMIE_STAR_DEFAULT']['frontPic'] == 'graphics/pokemon/alcremie/star/front.png'
    assert sprites['SPECIES_ALCREMIE_STAR_DEFAULT']['palette'] == 'graphics/pokemon/alcremie/star/star_default.pal'
    assert sprites['SPECIES_ALCREMIE_STAR_CARAMEL_SWIRL']['frontPic'] == 'graphics/pokemon/alcremie/star/front.png'
    assert sprites['SPECIES_ALCREMIE_STAR_CARAMEL_SWIRL']['palette'] == 'graphics/pokemon/alcremie/star/star_caramel_swirl.pal'
