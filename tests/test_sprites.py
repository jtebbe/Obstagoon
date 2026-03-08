from pathlib import Path

from obstagoon.extract.parsers.sprites import parse_sprite_assets


def test_kind_aware_sprite_resolution(tmp_path: Path) -> None:
    (tmp_path / 'graphics/pokemon/pikachu').mkdir(parents=True)
    (tmp_path / 'graphics/pokemon/icon').mkdir(parents=True)
    for rel in ['graphics/pokemon/pikachu/front.png', 'graphics/pokemon/pikachu/back.png', 'graphics/pokemon/pikachu/normal.pal', 'graphics/pokemon/pikachu/shiny.pal', 'graphics/pokemon/icon/pikachu.png']:
        (tmp_path / rel).write_bytes(b'x')

    species = {
        'SPECIES_PIKACHU': {
            'graphics': {
                'frontPic': 'gMonFrontPic_Pikachu',
                'backPic': 'gMonBackPic_Pikachu',
                'palette': 'gMonPalette_Pikachu',
                'shinyPalette': 'gMonShinyPalette_Pikachu',
                'iconSprite': 'gMonIcon_Pikachu',
            }
        }
    }
    assets = parse_sprite_assets(tmp_path, species)
    assert assets['SPECIES_PIKACHU']['frontPic'].endswith('graphics/pokemon/pikachu/front.png')
    assert assets['SPECIES_PIKACHU']['backPic'].endswith('graphics/pokemon/pikachu/back.png')
    assert assets['SPECIES_PIKACHU']['palette'].endswith('graphics/pokemon/pikachu/normal.pal')
    assert assets['SPECIES_PIKACHU']['shinyPalette'].endswith('graphics/pokemon/pikachu/shiny.pal')
    assert assets['SPECIES_PIKACHU']['iconSprite'].endswith('graphics/pokemon/icon/pikachu.png')


def test_sprite_resolution_uses_cache_and_ascii_progress_labels(tmp_path: Path) -> None:
    (tmp_path / 'graphics/pokemon/nidoran_f').mkdir(parents=True)
    (tmp_path / 'graphics/pokemon/icon').mkdir(parents=True)
    (tmp_path / 'graphics/pokemon/nidoran_f/front.png').write_bytes(b'x')
    (tmp_path / 'graphics/pokemon/icon/nidoran_f.png').write_bytes(b'x')
    cache_dir = tmp_path / '.cache'
    species = {
        'SPECIES_NIDORAN_F': {
            'speciesName': 'Nidoran♀',
            'graphics': {
                'frontPic': 'gMonFrontPic_NidoranF',
                'iconSprite': 'gMonIcon_NidoranF',
            }
        }
    }
    assets_first = parse_sprite_assets(tmp_path, species, cache_dir=cache_dir)
    assets_second = parse_sprite_assets(tmp_path, species, cache_dir=cache_dir)
    assert assets_first == assets_second
    assert assets_second['SPECIES_NIDORAN_F']['frontPic'].endswith('graphics/pokemon/nidoran_f/front.png')
