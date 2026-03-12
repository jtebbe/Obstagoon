from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from obstagoon.config import SiteConfig
from obstagoon.generate.site import SiteGenerator
from obstagoon.model.builder import build_model


class DummyProject:
    def __init__(self, payload: dict):
        self.payload = payload

    def load_all(self) -> dict:
        return self.payload


def _build_minimal_model() -> object:
    payload = {
        'species_to_national': {'SPECIES_ABRA': 63, 'SPECIES_ZYGARDE_10_AURA_BREAK': 718},
        'form_species_tables': {},
        'species': {
            'SPECIES_ABRA': {'speciesName': 'Abra', 'types': ['TYPE_PSYCHIC'], 'abilities': ['ABILITY_SYNCHRONIZE'], 'graphics': {'frontPic': 'graphics/pokemon/abra/front.png'}, 'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []},
            'SPECIES_ZYGARDE_10_AURA_BREAK': {'speciesName': 'Zygarde', 'types': ['TYPE_DRAGON'], 'abilities': ['ABILITY_AURA_BREAK'], 'graphics': {'frontPic': 'graphics/pokemon/zygarde/10_percent/anim_front.png'}, 'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []},
        },
        'moves': {},
        'abilities': {'ABILITY_SYNCHRONIZE': {'name': 'Synchronize'}, 'ABILITY_AURA_BREAK': {'name': 'Aura Break'}},
        'items': {},
        'encounters': [],
        'trainers': [],
        'types': {'TYPE_PSYCHIC': 'TYPE_PSYCHIC', 'TYPE_DRAGON': 'TYPE_DRAGON'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    return build_model(DummyProject(payload))


def _make_test_image(path: Path, size=(4, 4), fg=(255, 0, 0, 255), bg=(0, 255, 0, 255)) -> None:
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGBA', size, bg)
    img.putpixel((1, 1), fg)
    if size[1] > 2:
        img.putpixel((1, size[1] - 1), (0, 0, 255, 255))
    img.save(path)


def test_copy_assets_makes_png_background_transparent_for_all_matching_pixels_and_crops_anim_front(tmp_path: Path) -> None:
    model = _build_minimal_model()
    project_dir = tmp_path / 'proj'
    abra_in = project_dir / 'graphics/pokemon/abra/front.png'
    abra_in.parent.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    img = Image.new('RGBA', (5, 5), (0, 255, 0, 255))
    for x in range(1, 4):
        for y in range(1, 4):
            img.putpixel((x, y), (255, 0, 0, 255))
    img.putpixel((2, 2), (0, 255, 0, 255))
    img.save(abra_in)
    _make_test_image(project_dir / 'graphics/pokemon/zygarde/10_percent/anim_front.png', size=(4, 6))
    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    abra_out = dist / 'assets/game/graphics/pokemon/abra/front.png'
    zygarde_out = dist / 'assets/game/graphics/pokemon/zygarde/10_percent/anim_front.png'
    from PIL import Image
    with Image.open(abra_out) as img:
        rgba = img.convert('RGBA')
        assert rgba.getpixel((0, 0))[3] == 0
        assert rgba.getpixel((2, 2))[3] == 0
        assert rgba.getpixel((1, 1))[3] == 255
    with Image.open(zygarde_out) as img:
        rgba = img.convert('RGBA')
        assert rgba.size == (4, 3)
        assert rgba.getpixel((0, 0))[3] == 0


def test_copy_assets_leaves_trainer_png_unchanged(tmp_path: Path) -> None:
    payload = {
        'species_to_national': {},
        'form_species_tables': {},
        'species': {},
        'moves': {},
        'abilities': {},
        'items': {},
        'encounters': [],
        'trainers': [{
            'trainer_id': 'TRAINER_WENDY',
            'name': 'Wendy',
            'pic_path': 'graphics/trainers/front_pics/wendy.png',
            'location': 'Route123',
            'has_party_pool': False,
            'party_size': None,
            'raw_metadata': {},
            'pokemon': [],
        }],
        'types': {},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    _make_test_image(project_dir / 'graphics/trainers/front_pics/wendy.png', size=(4, 4))
    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/trainers/front_pics/wendy.png'
    from PIL import Image
    with Image.open(out) as img:
        rgba = img.convert('RGBA')
        assert rgba.getpixel((0, 0))[3] == 255
        assert rgba.getpixel((1, 1))[3] == 255


def test_copy_assets_without_pillow_transparency_copies_png_unchanged(tmp_path: Path) -> None:
    from PIL import Image
    model = _build_minimal_model()
    project_dir = tmp_path / 'proj'
    abra_in = project_dir / 'graphics/pokemon/abra/front.png'
    _make_test_image(abra_in, size=(4, 4), fg=(255, 0, 0, 255), bg=(0, 255, 0, 255))
    _make_test_image(project_dir / 'graphics/pokemon/zygarde/10_percent/anim_front.png', size=(4, 6))
    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    abra_out = dist / 'assets/game/graphics/pokemon/abra/front.png'
    zygarde_out = dist / 'assets/game/graphics/pokemon/zygarde/10_percent/anim_front.png'
    with Image.open(abra_out) as img:
        rgba = img.convert('RGBA')
        assert rgba.size == (4, 4)
        assert rgba.getpixel((0, 0))[3] == 255
    with Image.open(zygarde_out) as img:
        rgba = img.convert('RGBA')
        assert rgba.size == (4, 6)


def test_write_type_icons_sanitizes_invalid_windows_filenames(tmp_path: Path) -> None:
    payload = {
        'species_to_national': {},
        'form_species_tables': {},
        'species': {},
        'moves': {},
        'abilities': {},
        'items': {},
        'encounters': [],
        'trainers': [],
        'types': {'TYPE_QMARKS': '???'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=tmp_path / 'proj', dist_dir=dist, site_title='Test', copy_assets=False, verbose=False)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    assert (dist / 'assets/generated/types/unknown.svg').exists()
    assert not (dist / 'assets/generated/types/???.svg').exists()


def test_copy_assets_applies_form_palette_to_shared_front_sprite(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ARCEUS_DRAGON': 493},
        'form_species_tables': {},
        'species': {
            'SPECIES_ARCEUS_DRAGON': {
                'speciesName': 'Arceus',
                'types': ['TYPE_DRAGON'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/dragon/normal.pal',
                },
                'stats': {},
                'evolutions': [],
                'levelUpLearnset': [],
                'eggMoves': [],
                'teachableLearnset': [],
            },
        },
        'moves': {},
        'abilities': {'ABILITY_MULTITYPE': {'name': 'Multitype'}},
        'items': {},
        'encounters': [],
        'trainers': [],
        'types': {'TYPE_DRAGON': 'TYPE_DRAGON'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/arceus/anim_front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('P', (4, 4))
    img.putpalette([0, 0, 0, 255, 0, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.putpixel((1, 0), 1)
    img.save(sprite_path)
    palette_path = project_dir / 'graphics/pokemon/arceus/dragon/normal.pal'
    palette_path.parent.mkdir(parents=True, exist_ok=True)
    # index 0 = black, index 1 = blue in little-endian BGR555
    palette_path.write_bytes(bytes([0x00, 0x00, 0x00, 0x7C]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/arceus/dragon/anim_front.png'
    with Image.open(out) as processed:
        rgba = processed.convert('RGBA')
        assert rgba.size == (4, 2)
        assert rgba.getpixel((0, 0))[3] == 0
        assert rgba.getpixel((1, 1))[:3] == (0, 0, 255)
        assert rgba.getpixel((1, 0))[3] == 255


def test_copy_assets_palette_variants_do_not_overwrite_each_other(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ARCEUS': 493, 'SPECIES_ARCEUS_DRAGON': 493},
        'form_species_tables': {},
        'species': {
            'SPECIES_ARCEUS': {
                'speciesName': 'Arceus',
                'types': ['TYPE_NORMAL'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/normal/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
            'SPECIES_ARCEUS_DRAGON': {
                'speciesName': 'Arceus',
                'types': ['TYPE_DRAGON'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/dragon/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {},
        'abilities': {'ABILITY_MULTITYPE': {'name': 'Multitype'}},
        'items': {},
        'encounters': [],
        'trainers': [],
        'types': {'TYPE_NORMAL': 'TYPE_NORMAL', 'TYPE_DRAGON': 'TYPE_DRAGON'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/arceus/anim_front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('P', (4, 4))
    img.putpalette([0, 0, 0, 255, 0, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.save(sprite_path)
    normal_pal = project_dir / 'graphics/pokemon/arceus/normal/normal.pal'
    normal_pal.parent.mkdir(parents=True, exist_ok=True)
    normal_pal.write_bytes(bytes([0x00, 0x00, 0xE0, 0x03]))
    dragon_pal = project_dir / 'graphics/pokemon/arceus/dragon/normal.pal'
    dragon_pal.parent.mkdir(parents=True, exist_ok=True)
    dragon_pal.write_bytes(bytes([0x00, 0x00, 0x00, 0x7C]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    normal_out = dist / 'assets/game/graphics/pokemon/arceus/normal/anim_front.png'
    dragon_out = dist / 'assets/game/graphics/pokemon/arceus/dragon/anim_front.png'
    assert normal_out.exists()
    assert dragon_out.exists()
    with Image.open(normal_out) as processed:
        rgba = processed.convert('RGBA')
        assert rgba.getpixel((1, 1))[:3] == (0, 255, 0)
    with Image.open(dragon_out) as processed:
        rgba = processed.convert('RGBA')
        assert rgba.getpixel((1, 1))[:3] == (0, 0, 255)


def test_copy_assets_updates_species_front_pic_to_palette_variant_path(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ARCEUS': 493, 'SPECIES_ARCEUS_FIGHTING': 493},
        'form_species_tables': {},
        'species': {
            'SPECIES_ARCEUS': {
                'speciesName': 'Arceus',
                'types': ['TYPE_NORMAL'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/normal/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
            'SPECIES_ARCEUS_FIGHTING': {
                'speciesName': 'Arceus',
                'types': ['TYPE_FIGHTING'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/fighting/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_MULTITYPE': {'name': 'Multitype'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_NORMAL': 'TYPE_NORMAL', 'TYPE_FIGHTING': 'TYPE_FIGHTING'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/arceus/anim_front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGBA', (4, 4), (0, 0, 0, 255))
    img.putpixel((1, 1), (255, 0, 0, 255))
    img.save(sprite_path)
    normal_pal = project_dir / 'graphics/pokemon/arceus/normal/normal.pal'
    normal_pal.parent.mkdir(parents=True, exist_ok=True)
    normal_pal.write_bytes(bytes([0x00, 0x00, 0x1F, 0x00]))
    fighting_pal = project_dir / 'graphics/pokemon/arceus/fighting/normal.pal'
    fighting_pal.parent.mkdir(parents=True, exist_ok=True)
    fighting_pal.write_bytes(bytes([0x00, 0x00, 0xE0, 0x03]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    assert model.species['SPECIES_ARCEUS'].graphics['frontPic'].endswith('normal/anim_front.png')
    assert model.species['SPECIES_ARCEUS_FIGHTING'].graphics['frontPic'].endswith('fighting/anim_front.png')



def test_copy_assets_recolors_rgba_shared_sprite_using_source_and_target_palettes(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ARCEUS_FIGHTING': 493},
        'form_species_tables': {},
        'species': {
            'SPECIES_ARCEUS_FIGHTING': {
                'speciesName': 'Arceus',
                'types': ['TYPE_FIGHTING'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/fighting/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_MULTITYPE': {'name': 'Multitype'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_FIGHTING': 'TYPE_FIGHTING'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/arceus/anim_front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGBA', (4, 4), (0, 0, 0, 255))
    img.putpixel((1, 1), (255, 0, 0, 255))
    img.putpixel((1, 0), (255, 0, 0, 255))
    img.save(sprite_path)
    (project_dir / 'graphics/pokemon/arceus/normal.pal').write_bytes(bytes([0x00, 0x00, 0x1F, 0x00]))
    fighting_pal = project_dir / 'graphics/pokemon/arceus/fighting/normal.pal'
    fighting_pal.parent.mkdir(parents=True, exist_ok=True)
    fighting_pal.write_bytes(bytes([0x00, 0x00, 0xE0, 0x03]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/arceus/fighting/anim_front.png'
    with Image.open(out) as processed:
        rgba = processed.convert('RGBA')
        assert rgba.size == (4, 2)
        assert rgba.getpixel((0, 0))[3] == 0
        assert rgba.getpixel((1, 0))[:3] == (0, 255, 0)
        assert rgba.getpixel((1, 1))[:3] == (0, 255, 0)


def test_copy_assets_generates_distinct_palette_variants_for_alcremie_forms(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ALCREMIE_LEMON_CREAM_BERRY': 869, 'SPECIES_ALCREMIE_STAR_CARAMEL_SWIRL': 869},
        'form_species_tables': {},
        'species': {
            'SPECIES_ALCREMIE_LEMON_CREAM_BERRY': {
                'speciesName': 'Alcremie',
                'types': ['TYPE_FAIRY'],
                'abilities': ['ABILITY_SWEET_VEIL'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/alcremie/berry/front.png',
                    'palette': 'graphics/pokemon/alcremie/berry/lemon_cream/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
            'SPECIES_ALCREMIE_STAR_CARAMEL_SWIRL': {
                'speciesName': 'Alcremie',
                'types': ['TYPE_FAIRY'],
                'abilities': ['ABILITY_SWEET_VEIL'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/alcremie/star/front.png',
                    'palette': 'graphics/pokemon/alcremie/star/caramel_swirl/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_SWEET_VEIL': {'name': 'Sweet Veil'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_FAIRY': 'TYPE_FAIRY'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    berry_sprite = project_dir / 'graphics/pokemon/alcremie/berry/front.png'
    berry_sprite.parent.mkdir(parents=True, exist_ok=True)
    berry = Image.new('RGBA', (4, 4), (0, 0, 0, 255))
    berry.putpixel((1, 1), (255, 0, 0, 255))
    berry.save(berry_sprite)
    star_sprite = project_dir / 'graphics/pokemon/alcremie/star/front.png'
    star_sprite.parent.mkdir(parents=True, exist_ok=True)
    star = Image.new('RGBA', (4, 4), (0, 0, 0, 255))
    star.putpixel((1, 1), (255, 0, 0, 255))
    star.save(star_sprite)
    (project_dir / 'graphics/pokemon/alcremie/berry/normal.pal').write_bytes(bytes([0x00, 0x00, 0x1F, 0x00]))
    (project_dir / 'graphics/pokemon/alcremie/star/normal.pal').write_bytes(bytes([0x00, 0x00, 0x1F, 0x00]))
    lemon_pal = project_dir / 'graphics/pokemon/alcremie/berry/lemon_cream/normal.pal'
    lemon_pal.parent.mkdir(parents=True, exist_ok=True)
    lemon_pal.write_bytes(bytes([0x00, 0x00, 0xFF, 0x03]))
    caramel_pal = project_dir / 'graphics/pokemon/alcremie/star/caramel_swirl/normal.pal'
    caramel_pal.parent.mkdir(parents=True, exist_ok=True)
    caramel_pal.write_bytes(bytes([0x00, 0x00, 0x0F, 0x42]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    lemon_out = dist / 'assets/game/graphics/pokemon/alcremie/berry/lemon_cream/front.png'
    caramel_out = dist / 'assets/game/graphics/pokemon/alcremie/star/caramel_swirl/front.png'
    assert lemon_out.exists()
    assert caramel_out.exists()
    with Image.open(lemon_out) as processed:
        lemon_rgba = processed.convert('RGBA')
        lemon_pixel = lemon_rgba.getpixel((1, 1))[:3]
        assert lemon_pixel == (255, 255, 0)
    with Image.open(caramel_out) as processed:
        caramel_rgba = processed.convert('RGBA')
        caramel_pixel = caramel_rgba.getpixel((1, 1))[:3]
        assert caramel_pixel == (123, 131, 131)
        assert caramel_pixel != lemon_pixel


def test_copy_assets_prefers_palette_specific_pattern_source_for_alcremie(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ALCREMIE_FLOWER_MATCHA_CREAM': 869},
        'form_species_tables': {},
        'species': {
            'SPECIES_ALCREMIE_FLOWER_MATCHA_CREAM': {
                'speciesName': 'Alcremie',
                'types': ['TYPE_FAIRY'],
                'abilities': ['ABILITY_SWEET_VEIL'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/alcremie/front.png',
                    'palette': 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_SWEET_VEIL': {'name': 'Sweet Veil'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_FAIRY': 'TYPE_FAIRY'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'

    base_sprite = project_dir / 'graphics/pokemon/alcremie/front.png'
    base_sprite.parent.mkdir(parents=True, exist_ok=True)
    base = Image.new('P', (4, 4))
    base.putpalette([0, 0, 0, 255, 0, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            base.putpixel((x, y), 0)
    base.putpixel((1, 1), 1)
    base.save(base_sprite)

    flower_sprite = project_dir / 'graphics/pokemon/alcremie/flower/front.png'
    flower_sprite.parent.mkdir(parents=True, exist_ok=True)
    flower = Image.new('P', (4, 4))
    flower.putpalette([0, 0, 0, 255, 0, 0, 0, 255, 0] + [0] * (768 - 9))
    for x in range(4):
        for y in range(4):
            flower.putpixel((x, y), 0)
    flower.putpixel((1, 1), 1)
    flower.putpixel((2, 1), 2)
    flower.save(flower_sprite)

    source_pal = project_dir / 'graphics/pokemon/alcremie/flower/normal.pal'
    source_pal.write_bytes(bytes([0x00, 0x00, 0x1F, 0x00, 0xE0, 0x03]))
    target_pal = project_dir / 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal'
    target_pal.parent.mkdir(parents=True, exist_ok=True)
    target_pal.write_bytes(bytes([0x00, 0x00, 0x00, 0x7C, 0x00, 0x03]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/alcremie/flower/matcha_cream/front.png'
    assert out.exists()
    assert model.species['SPECIES_ALCREMIE_FLOWER_MATCHA_CREAM'].graphics['frontPic'].endswith('graphics/pokemon/alcremie/flower/matcha_cream/front.png')
    with Image.open(out) as processed:
        rgba = processed.convert('RGBA')
        assert rgba.getpixel((1, 1))[:3] == (0, 0, 255)
        assert rgba.getpixel((2, 1))[:3] == (0, 197, 0)


def test_copy_assets_reuses_base_arceus_anim_front_when_palette_folder_has_no_sprite(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ARCEUS_FIGHTING': 493},
        'form_species_tables': {},
        'species': {
            'SPECIES_ARCEUS_FIGHTING': {
                'speciesName': 'Arceus',
                'types': ['TYPE_FIGHTING'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/fighting/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_MULTITYPE': {'name': 'Multitype'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_FIGHTING': 'TYPE_FIGHTING'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/arceus/anim_front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('P', (4, 4))
    img.putpalette([0, 0, 0, 255, 0, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.save(sprite_path)
    base_pal = project_dir / 'graphics/pokemon/arceus/normal.pal'
    base_pal.write_bytes(bytes([0x00, 0x00, 0x1F, 0x00]))
    fighting_pal = project_dir / 'graphics/pokemon/arceus/fighting/normal.pal'
    fighting_pal.parent.mkdir(parents=True, exist_ok=True)
    fighting_pal.write_bytes(bytes([0x00, 0x00, 0xE0, 0x03]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/arceus/fighting/anim_front.png'
    assert out.exists()
    assert model.species['SPECIES_ARCEUS_FIGHTING'].graphics['frontPic'].endswith('graphics/pokemon/arceus/fighting/anim_front.png')



def test_copy_assets_skips_palette_application_when_form_has_own_front_png(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_VIVILLON_ICY_SNOW': 666},
        'form_species_tables': {},
        'species': {
            'SPECIES_VIVILLON_ICY_SNOW': {
                'speciesName': 'Vivillon',
                'types': ['TYPE_BUG', 'TYPE_FLYING'],
                'abilities': ['ABILITY_COMPOUND_EYES'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/vivillon/icy_snow/front.png',
                    'palette': 'graphics/pokemon/vivillon/icy_snow/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_COMPOUND_EYES': {'name': 'Compound Eyes'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_BUG': 'TYPE_BUG', 'TYPE_FLYING': 'TYPE_FLYING'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/vivillon/icy_snow/front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGBA', (4, 4), (255, 255, 255, 255))
    img.putpixel((1, 1), (32, 64, 96, 255))
    img.save(sprite_path)
    pal = project_dir / 'graphics/pokemon/vivillon/icy_snow/normal.pal'
    pal.write_bytes(bytes([0x00, 0x00, 0x00, 0x7C]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/vivillon/icy_snow/front.png'
    with Image.open(out) as processed:
        rgba = processed.convert('RGBA')
        assert rgba.getpixel((1, 1))[:3] == (32, 64, 96)
    assert model.species['SPECIES_VIVILLON_ICY_SNOW'].graphics['frontPic'].endswith('vivillon/icy_snow/front.png')


def test_copy_assets_applies_palette_when_form_reuses_shared_source_sprite(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ARCEUS_PSYCHIC': 493},
        'form_species_tables': {},
        'species': {
            'SPECIES_ARCEUS_PSYCHIC': {
                'speciesName': 'Arceus',
                'types': ['TYPE_PSYCHIC'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/psychic/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_MULTITYPE': {'name': 'Multitype'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_PSYCHIC': 'TYPE_PSYCHIC'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/arceus/anim_front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('P', (4, 4))
    img.putpalette([0, 0, 0, 255, 0, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.save(sprite_path)
    pal = project_dir / 'graphics/pokemon/arceus/psychic/normal.pal'
    pal.parent.mkdir(parents=True, exist_ok=True)
    pal.write_bytes(bytes([0x00, 0x00, 0x1F, 0x7C]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/arceus/psychic/anim_front.png'
    with Image.open(out) as processed:
        rgba = processed.convert('RGBA')
        assert rgba.getpixel((1, 1))[:3] != (255, 0, 0)
    assert model.species['SPECIES_ARCEUS_PSYCHIC'].graphics['frontPic'].endswith('arceus/psychic/anim_front.png')


def test_copy_assets_preserves_existing_paletted_indices_beyond_target_palette_length(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ARCEUS_ROCK': 493},
        'form_species_tables': {},
        'species': {
            'SPECIES_ARCEUS_ROCK': {
                'speciesName': 'Arceus',
                'types': ['TYPE_ROCK'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/rock/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_MULTITYPE': {'name': 'Multitype'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_ROCK': 'TYPE_ROCK'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/arceus/anim_front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('P', (4, 4))
    palette = [0, 0, 0, 255, 0, 0] + [0] * ((17 * 3) - 6) + [12, 34, 56]
    palette.extend([0] * (768 - len(palette)))
    img.putpalette(palette)
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.putpixel((2, 1), 17)
    img.save(sprite_path)
    rock_pal = project_dir / 'graphics/pokemon/arceus/rock/normal.pal'
    rock_pal.parent.mkdir(parents=True, exist_ok=True)
    rock_pal.write_bytes(bytes([0x00, 0x00, 0x1F, 0x00]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/arceus/rock/anim_front.png'
    assert out.exists()
    with Image.open(out) as processed:
        rgba = processed.convert('RGBA')
        assert rgba.getpixel((1, 1))[:3] == (255, 0, 0)
        assert rgba.getpixel((2, 1))[:3] == (12, 34, 56)


def test_copy_assets_remaps_paletted_source_indices_using_external_source_palette(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ARCEUS_WATER': 493},
        'form_species_tables': {},
        'species': {
            'SPECIES_ARCEUS_WATER': {
                'speciesName': 'Arceus',
                'types': ['TYPE_WATER'],
                'abilities': ['ABILITY_MULTITYPE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/arceus/anim_front.png',
                    'palette': 'graphics/pokemon/arceus/water/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_MULTITYPE': {'name': 'Multitype'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_WATER': 'TYPE_WATER'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/arceus/anim_front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new('P', (4, 4))
    # Embedded PNG palette order intentionally differs from the external normal.pal.
    # index 1 is green here, but should map to source palette slot 2 before target palette is applied.
    embedded = [0, 0, 0, 0, 255, 0, 255, 0, 0] + [0] * (768 - 9)
    img.putpalette(embedded)
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.save(sprite_path)

    # External source palette: index 1 = red, index 2 = green.
    (project_dir / 'graphics/pokemon/arceus/normal.pal').write_bytes(bytes([
        0x00, 0x00,  # black
        0x1F, 0x00,  # red
        0xE0, 0x03,  # green
    ]))
    # Target palette: index 1 = blue, index 2 = yellow.
    target_pal = project_dir / 'graphics/pokemon/arceus/water/normal.pal'
    target_pal.parent.mkdir(parents=True, exist_ok=True)
    target_pal.write_bytes(bytes([
        0x00, 0x00,  # black
        0x00, 0x7C,  # blue
        0xFF, 0x03,  # yellow
    ]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/arceus/water/anim_front.png'
    with Image.open(out) as processed:
        rgba = processed.convert('RGBA')
        # Since the embedded green should be remapped to source slot 2, it should become yellow, not blue.
        assert rgba.getpixel((1, 1))[:3] == (255, 255, 0)


def test_copy_assets_generates_alcremie_pattern_and_cream_variant_when_species_id_has_pattern_middle(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ALCREMIE_FLOWER_PATTERN_MATCHA_CREAM': 869},
        'form_species_tables': {},
        'species': {
            'SPECIES_ALCREMIE_FLOWER_PATTERN_MATCHA_CREAM': {
                'speciesName': 'Alcremie',
                'types': ['TYPE_FAIRY'],
                'abilities': ['ABILITY_SWEET_VEIL'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/alcremie/front.png',
                    'palette': 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_SWEET_VEIL': {'name': 'Sweet Veil'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_FAIRY': 'TYPE_FAIRY'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'

    base_sprite = project_dir / 'graphics/pokemon/alcremie/front.png'
    base_sprite.parent.mkdir(parents=True, exist_ok=True)
    base = Image.new('P', (4, 4))
    base.putpalette([0, 0, 0, 255, 0, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            base.putpixel((x, y), 0)
    base.putpixel((1, 1), 1)
    base.save(base_sprite)

    flower_sprite = project_dir / 'graphics/pokemon/alcremie/flower/front.png'
    flower_sprite.parent.mkdir(parents=True, exist_ok=True)
    flower = Image.new('P', (4, 4))
    flower.putpalette([0, 0, 0, 255, 0, 0, 0, 255, 0] + [0] * (768 - 9))
    for x in range(4):
        for y in range(4):
            flower.putpixel((x, y), 0)
    flower.putpixel((1, 1), 1)
    flower.putpixel((2, 1), 2)
    flower.save(flower_sprite)

    source_pal = project_dir / 'graphics/pokemon/alcremie/flower/normal.pal'
    source_pal.write_bytes(bytes([0x00, 0x00, 0x1F, 0x00, 0xE0, 0x03]))
    target_pal = project_dir / 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal'
    target_pal.parent.mkdir(parents=True, exist_ok=True)
    target_pal.write_bytes(bytes([0x00, 0x00, 0x00, 0x7C, 0x00, 0x03]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/alcremie/flower/matcha_cream/front.png'
    assert out.exists()
    assert model.species['SPECIES_ALCREMIE_FLOWER_PATTERN_MATCHA_CREAM'].graphics['frontPic'].endswith('graphics/pokemon/alcremie/flower/matcha_cream/front.png')


def test_copy_assets_generates_same_folder_palette_variants_for_alcremie_patterns(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {
            'SPECIES_ALCREMIE_STAR_DEFAULT': 869,
            'SPECIES_ALCREMIE_STAR_CARAMEL_SWIRL': 869,
            'SPECIES_ALCREMIE_STAR_MATCHA_CREAM': 869,
        },
        'form_species_tables': {},
        'species': {
            'SPECIES_ALCREMIE_STAR_DEFAULT': {
                'speciesName': 'Alcremie',
                'types': ['TYPE_FAIRY'],
                'abilities': ['ABILITY_SWEET_VEIL'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/alcremie/star/front.png',
                    'palette': 'graphics/pokemon/alcremie/star/star_default.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
            'SPECIES_ALCREMIE_STAR_CARAMEL_SWIRL': {
                'speciesName': 'Alcremie',
                'types': ['TYPE_FAIRY'],
                'abilities': ['ABILITY_SWEET_VEIL'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/alcremie/star/front.png',
                    'palette': 'graphics/pokemon/alcremie/star/star_caramel_swirl.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
            'SPECIES_ALCREMIE_STAR_MATCHA_CREAM': {
                'speciesName': 'Alcremie',
                'types': ['TYPE_FAIRY'],
                'abilities': ['ABILITY_SWEET_VEIL'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/alcremie/star/front.png',
                    'palette': 'graphics/pokemon/alcremie/star/star_matcha_cream.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_SWEET_VEIL': {'name': 'Sweet Veil'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_FAIRY': 'TYPE_FAIRY'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'

    star_sprite = project_dir / 'graphics/pokemon/alcremie/star/front.png'
    star_sprite.parent.mkdir(parents=True, exist_ok=True)
    star = Image.new('RGBA', (4, 4), (0, 0, 0, 255))
    star.putpixel((1, 1), (255, 0, 0, 255))
    star.save(star_sprite)

    default_pal = project_dir / 'graphics/pokemon/alcremie/star/star_default.pal'
    default_pal.write_bytes(bytes([0x00, 0x00, 0x1F, 0x00]))
    caramel_pal = project_dir / 'graphics/pokemon/alcremie/star/star_caramel_swirl.pal'
    caramel_pal.write_bytes(bytes([0x00, 0x00, 0x0F, 0x42]))
    matcha_pal = project_dir / 'graphics/pokemon/alcremie/star/star_matcha_cream.pal'
    matcha_pal.write_bytes(bytes([0x00, 0x00, 0xE0, 0x03]))
    shiny_pal = project_dir / 'graphics/pokemon/alcremie/star/star_shiny.pal'
    shiny_pal.write_bytes(bytes([0x00, 0x00, 0xFF, 0x7F]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    default_out = dist / 'assets/game/graphics/pokemon/alcremie/star/default/front.png'
    caramel_out = dist / 'assets/game/graphics/pokemon/alcremie/star/caramel_swirl/front.png'
    matcha_out = dist / 'assets/game/graphics/pokemon/alcremie/star/matcha_cream/front.png'
    shiny_out = dist / 'assets/game/graphics/pokemon/alcremie/star/shiny/front.png'
    assert default_out.exists()
    assert caramel_out.exists()
    assert matcha_out.exists()
    assert not shiny_out.exists()
    assert model.species['SPECIES_ALCREMIE_STAR_DEFAULT'].graphics['frontPic'].endswith('graphics/pokemon/alcremie/star/default/front.png')
    assert model.species['SPECIES_ALCREMIE_STAR_CARAMEL_SWIRL'].graphics['frontPic'].endswith('graphics/pokemon/alcremie/star/caramel_swirl/front.png')
    assert model.species['SPECIES_ALCREMIE_STAR_MATCHA_CREAM'].graphics['frontPic'].endswith('graphics/pokemon/alcremie/star/matcha_cream/front.png')


def test_copy_assets_generates_default_alcremie_variant_from_same_folder_palette(tmp_path: Path) -> None:
    from PIL import Image
    payload = {
        'species_to_national': {'SPECIES_ALCREMIE_BERRY_DEFAULT': 869},
        'form_species_tables': {},
        'species': {
            'SPECIES_ALCREMIE_BERRY_DEFAULT': {
                'speciesName': 'Alcremie',
                'types': ['TYPE_FAIRY'],
                'abilities': ['ABILITY_SWEET_VEIL'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/alcremie/berry/front.png',
                    'palette': 'graphics/pokemon/alcremie/berry/berry_default.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_SWEET_VEIL': {'name': 'Sweet Veil'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_FAIRY': 'TYPE_FAIRY'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite = project_dir / 'graphics/pokemon/alcremie/berry/front.png'
    sprite.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGBA', (4, 4), (0, 0, 0, 255))
    img.putpixel((1, 1), (255, 0, 0, 255))
    img.save(sprite)
    # In same-folder Alcremie variants, the default palette is both the target
    # palette and the correct source palette for quantization.
    (project_dir / 'graphics/pokemon/alcremie/berry/berry_default.pal').write_bytes(bytes([0x00, 0x00, 0x1F, 0x00]))

    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=True, verbose=False, pillow_transparency=True)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    config.ensure()

    SiteGenerator(config=config, model=model, env=env).run()

    out = dist / 'assets/game/graphics/pokemon/alcremie/berry/default/front.png'
    assert out.exists()
    with Image.open(out) as processed:
        rgba = processed.convert('RGBA')
        assert rgba.getpixel((1, 1))[:3] == (255, 0, 0)
