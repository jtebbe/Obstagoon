from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from obstagoon.config import SiteConfig
from obstagoon.extract.parsers.trainers import parse_trainers
from obstagoon.generate.site import SiteGenerator
from obstagoon.model.builder import build_model


class DummyProject:
    def __init__(self, payload: dict):
        self.payload = payload

    def load_all(self) -> dict:
        return self.payload


def test_parse_trainers_and_locations(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    (project / 'graphics/trainers/front_pics').mkdir(parents=True)
    (project / 'data/maps/Route123').mkdir(parents=True)
    (project / 'data/maps/EverGrandeCity_PhoebesRoom').mkdir(parents=True)
    (project / 'graphics/trainers/front_pics/wendy.png').write_text('x')
    (project / 'graphics/trainers/front_pics/elite_four_phoebe.png').write_text('x')
    (project / 'data/maps/Route123/scripts.inc').write_text('trainerbattle_single TRAINER_WENDY, Text, Text')
    (project / 'data/maps/EverGrandeCity_PhoebesRoom/scripts.inc').write_text('trainerbattle_single TRAINER_PHOEBE, Text, Text')
    (project / 'src/data/trainers.party').write_text(
        '=== TRAINER_WENDY ===\n'
        'Name: WENDY\n'
        'Pic: TRAINER_PIC_WENDY\n\n'
        'Abra @ ITEM_FOCUS_SASH\n'
        'Ability: Magic Guard\n'
        'EVs: 252 SpA / 252 Spe\n'
        'IVs: 31 HP / 0 Atk\n'
        'Tera Type: Fire\n'
        '- Psychic\n\n'
        '=== TRAINER_PHOEBE ===\n'
        'Name: PHOEBE\n'
        'Pic: Elite Four Phoebe\n'
        'Party Pool: 3\n\n'
        'Duskull\n'
        '- Shadow Ball\n',
        encoding='utf-8',
    )

    trainers = parse_trainers(project)
    assert trainers[0]['name'] == 'Wendy'
    assert trainers[0]['location'] == 'Route123'
    assert trainers[0]['pic_path'] == 'graphics/trainers/front_pics/wendy.png'
    assert trainers[0]['pokemon'][0]['tera_type'] == 'Fire'
    assert trainers[1]['name'] == 'Phoebe'
    assert trainers[1]['location'] == 'Ever Grande City Phoebes Room'
    assert trainers[1]['pic_path'] == 'graphics/trainers/front_pics/elite_four_phoebe.png'
    assert trainers[1]['has_party_pool'] is True
    assert trainers[1]['party_size'] == '3'


def test_trainerdex_pages_render(tmp_path: Path) -> None:
    payload = {
        'species_to_national': {'SPECIES_ABRA': 63},
        'form_species_tables': {},
        'species': {
            'SPECIES_ABRA': {
                'speciesName': 'Abra',
                'types': ['TYPE_PSYCHIC'],
                'abilities': ['ABILITY_SYNCHRONIZE'],
                'graphics': {'frontPic': 'graphics/pokemon/abra/front.png'},
                'stats': {},
                'evolutions': [],
                'levelUpLearnset': [],
                'eggMoves': [],
                'teachableLearnset': [],
            }
        },
        'moves': {},
        'abilities': {'ABILITY_SYNCHRONIZE': {'name': 'Synchronize'}},
        'items': {'ITEM_FOCUS_SASH': {'name': 'Focus Sash'}},
        'encounters': [],
        'trainers': [{
            'trainer_id': 'TRAINER_WENDY',
            'name': 'Wendy',
            'class_name': 'Psychic',
            'pic_path': 'graphics/trainers/front_pics/wendy.png',
            'location': 'Route123',
            'has_party_pool': False,
            'party_size': None,
            'raw_metadata': {},
            'pokemon': [{
                'species_token': 'Abra',
                'species_symbol': None,
                'species_name': 'Abra',
                'nickname': None,
                'held_item': 'Focus Sash',
                'ability': 'Synchronize',
                'tera_type': 'Fire',
                'evs': {'SpA': '252'},
                'ivs': {'Atk': '0'},
                'moves': ['Psychic'],
                'level': '50',
            }],
        }],
        'types': {'TYPE_PSYCHIC': 'TYPE_PSYCHIC', 'TYPE_FIRE': 'TYPE_FIRE'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    (project_dir / 'graphics/pokemon/abra').mkdir(parents=True)
    (project_dir / 'graphics/pokemon/abra/front.png').write_text('x')
    (project_dir / 'graphics/trainers/front_pics').mkdir(parents=True)
    (project_dir / 'graphics/trainers/front_pics/wendy.png').write_text('x')
    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=False, verbose=False)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    SiteGenerator(config=config, model=model, env=env).run()

    trainerdex = (dist / 'trainerdex/index.html').read_text(encoding='utf-8')
    trainer_page = (dist / 'trainerdex/trainer-wendy.html').read_text(encoding='utf-8')
    assert 'Trainers' in trainerdex
    assert 'Route123' in trainerdex
    assert 'Party' in trainer_page
    assert '../assets/generated/types/psychic.svg' in trainer_page
    assert '../assets/generated/types/fire.svg' in trainer_page
    assert '../pokedex/abra.html' in trainer_page


def test_trainer_party_uses_base_form_image_for_mega_and_gmax(tmp_path: Path) -> None:
    payload = {
        'species_to_national': {'SPECIES_BANETTE': 354, 'SPECIES_BANETTE_MEGA': 354, 'SPECIES_GENGAR': 94, 'SPECIES_GENGAR_GMAX': 94},
        'form_species_tables': {'SPECIES_BANETTE': ['SPECIES_BANETTE', 'SPECIES_BANETTE_MEGA'], 'SPECIES_GENGAR': ['SPECIES_GENGAR', 'SPECIES_GENGAR_GMAX']},
        'species': {
            'SPECIES_BANETTE': {'speciesName': 'Banette', 'types': ['TYPE_GHOST'], 'abilities': ['ABILITY_INSOMNIA'], 'graphics': {'frontPic': 'graphics/pokemon/banette/front.png'}, 'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []},
            'SPECIES_BANETTE_MEGA': {'speciesName': 'Banette Mega', 'types': ['TYPE_GHOST'], 'abilities': ['ABILITY_PRANKSTER'], 'graphics': {'frontPic': 'graphics/pokemon/banette/mega/front.png'}, 'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []},
            'SPECIES_GENGAR': {'speciesName': 'Gengar', 'types': ['TYPE_GHOST', 'TYPE_POISON'], 'abilities': ['ABILITY_CURSED_BODY'], 'graphics': {'frontPic': 'graphics/pokemon/gengar/front.png'}, 'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []},
            'SPECIES_GENGAR_GMAX': {'speciesName': 'Gengar Gmax', 'types': ['TYPE_GHOST', 'TYPE_POISON'], 'abilities': ['ABILITY_CURSED_BODY'], 'graphics': {'frontPic': 'graphics/pokemon/gengar/gmax/front.png'}, 'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []},
        },
        'moves': {},
        'abilities': {'ABILITY_INSOMNIA': {'name': 'Insomnia'}, 'ABILITY_PRANKSTER': {'name': 'Prankster'}, 'ABILITY_CURSED_BODY': {'name': 'Cursed Body'}},
        'items': {'ITEM_BANETTITE': {'name': 'Banettite'}},
        'encounters': [],
        'trainers': [{
            'trainer_id': 'TRAINER_TEST',
            'name': 'Test',
            'pokemon': [
                {'species_symbol': 'SPECIES_BANETTE_MEGA', 'species_token': 'SPECIES_BANETTE_MEGA', 'species_name': 'Banette Mega', 'held_item': 'Banettite', 'moves': []},
                {'species_symbol': 'SPECIES_GENGAR_GMAX', 'species_token': 'SPECIES_GENGAR_GMAX', 'species_name': 'Gengar Gmax', 'moves': []},
            ],
        }],
        'types': {'TYPE_GHOST': 'TYPE_GHOST', 'TYPE_POISON': 'TYPE_POISON'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    trainer = model.trainers['TRAINER_TEST']
    assert trainer.pokemon[0].picture == 'graphics/pokemon/banette/front.png'
    assert trainer.pokemon[1].picture == 'graphics/pokemon/gengar/front.png'


def test_parse_trainer_pokemon_gender_marker_is_not_species_or_nickname(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    (project / 'graphics/trainers/front_pics').mkdir(parents=True)
    (project / 'data/maps/Route123').mkdir(parents=True)
    (project / 'graphics/trainers/front_pics/wendy.png').write_text('x')
    (project / 'data/maps/Route123/scripts.inc').write_text('trainerbattle_single TRAINER_WENDY, Text, Text')
    (project / 'src/data/trainers.party').write_text(
        '=== TRAINER_WENDY ===\n'
        'Name: WENDY\n'
        'Pic: TRAINER_PIC_WENDY\n\n'
        'Gallade (M) @ Galladite\n'
        'Ability: Justified\n'
        '- Close Combat\n',
        encoding='utf-8',
    )

    trainers = parse_trainers(project)
    assert trainers[0]['pokemon'][0]['species_name'] == 'Gallade'
    assert trainers[0]['pokemon'][0]['nickname'] is None
    assert trainers[0]['pokemon'][0]['gender'] == 'M'
    assert trainers[0]['pokemon'][0]['held_item'] == 'Galladite'


def test_parse_trainers_skips_unused_trainers_without_map_reference(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    (project / 'graphics/trainers/front_pics').mkdir(parents=True)
    (project / 'data/maps/Route123').mkdir(parents=True)
    (project / 'graphics/trainers/front_pics/wendy.png').write_text('x')
    (project / 'graphics/trainers/front_pics/unused.png').write_text('x')
    (project / 'data/maps/Route123/scripts.inc').write_text('trainerbattle_single TRAINER_WENDY, Text, Text')
    (project / 'src/data/trainers.party').write_text(
        '=== TRAINER_WENDY ===\n'
        'Name: WENDY\n'
        'Pic: TRAINER_PIC_WENDY\n\n'
        'Abra\n'
        '- Psychic\n\n'
        '=== TRAINER_UNUSED ===\n'
        'Name: UNUSED\n'
        'Pic: TRAINER_PIC_UNUSED\n\n'
        'Muk\n'
        '- Sludge Bomb\n',
        encoding='utf-8',
    )

    trainers = parse_trainers(project)
    assert [trainer['trainer_id'] for trainer in trainers] == ['TRAINER_WENDY']


def test_trainer_party_prefers_base_species_for_ambiguous_generic_name_lookup() -> None:
    payload = {
        'species_to_national': {'SPECIES_ARCEUS': 493, 'SPECIES_ARCEUS_FAIRY': 493},
        'form_species_tables': {'SPECIES_ARCEUS': ['SPECIES_ARCEUS', 'SPECIES_ARCEUS_FAIRY']},
        'species': {
            'SPECIES_ARCEUS': {'speciesName': 'Arceus', 'types': ['TYPE_NORMAL'], 'abilities': ['ABILITY_MULTITYPE'], 'graphics': {'frontPic': 'graphics/pokemon/arceus/front.png'}, 'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []},
            'SPECIES_ARCEUS_FAIRY': {'speciesName': 'Arceus', 'types': ['TYPE_FAIRY'], 'abilities': ['ABILITY_MULTITYPE'], 'graphics': {'frontPic': 'graphics/pokemon/arceus/fairy/front.png'}, 'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []},
        },
        'moves': {},
        'abilities': {'ABILITY_MULTITYPE': {'name': 'Multitype'}},
        'items': {'ITEM_BURGLARY_KIT': {'name': 'Burglary Kit'}},
        'encounters': [],
        'trainers': [{
            'trainer_id': 'TRAINER_TEST',
            'name': 'Test',
            'pokemon': [
                {'species_symbol': None, 'species_token': 'Arceus', 'species_name': 'Arceus', 'held_item': 'Burglary Kit', 'moves': []},
            ],
        }],
        'types': {'TYPE_NORMAL': 'TYPE_NORMAL', 'TYPE_FAIRY': 'TYPE_FAIRY'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    mon = model.trainers['TRAINER_TEST'].pokemon[0]
    assert mon.species_id == 'SPECIES_ARCEUS'
    assert mon.picture == 'graphics/pokemon/arceus/front.png'
    assert mon.types == ['Normal']


def test_rematch_trainers_get_rematch_suffix_in_display_name() -> None:
    payload = {
        'species_to_national': {},
        'form_species_tables': {},
        'species': {},
        'moves': {},
        'abilities': {},
        'items': {},
        'encounters': [],
        'trainers': [
            {'trainer_id': 'TRAINER_CLARK', 'name': 'Clark', 'pokemon': []},
            {'trainer_id': 'TRAINER_CLARK_REMATCH', 'name': 'Clark', 'pokemon': []},
        ],
        'types': {},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    assert model.trainers['TRAINER_CLARK'].name == 'Clark'
    assert model.trainers['TRAINER_CLARK_REMATCH'].name == 'Clark Rematch'


def test_trainer_party_appends_level_to_display_name_and_sorts_stats() -> None:
    payload = {
        'species_to_national': {'SPECIES_GALLADE': 475},
        'form_species_tables': {},
        'species': {
            'SPECIES_GALLADE': {'speciesName': 'Gallade', 'types': ['TYPE_PSYCHIC', 'TYPE_FIGHTING'], 'abilities': ['ABILITY_JUSTIFIED'], 'graphics': {'frontPic': 'graphics/pokemon/gallade/front.png'}, 'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []},
        },
        'moves': {},
        'abilities': {'ABILITY_JUSTIFIED': {'name': 'Justified'}},
        'items': {'ITEM_GALLADITE': {'name': 'Galladite'}},
        'encounters': [],
        'trainers': [{
            'trainer_id': 'TRAINER_TEST',
            'name': 'Test',
            'pokemon': [
                {'species_symbol': 'SPECIES_GALLADE', 'species_token': 'SPECIES_GALLADE', 'species_name': 'Gallade', 'held_item': 'Galladite', 'ability': 'Justified', 'level': '31', 'evs': {'Spe': '252', 'Atk': '252', 'HP': '4'}, 'ivs': {'SpD': '31', 'Atk': '0'}, 'moves': ['Protect', 'Close Combat']},
            ],
        }],
        'types': {'TYPE_PSYCHIC': 'TYPE_PSYCHIC', 'TYPE_FIGHTING': 'TYPE_FIGHTING'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    mon = model.trainers['TRAINER_TEST'].pokemon[0]
    assert mon.species_name == 'Gallade Level 31'
    assert list(mon.evs.items()) == [('HP', '4'), ('Atk', '252'), ('Spe', '252')]
    assert list(mon.ivs.items()) == [('Atk', '0'), ('SpD', '31')]


def test_trainerdex_page_renders_moves_and_sorted_stats_cleanly(tmp_path: Path) -> None:
    payload = {
        'species_to_national': {'SPECIES_GALLADE': 475},
        'form_species_tables': {},
        'species': {
            'SPECIES_GALLADE': {
                'speciesName': 'Gallade',
                'types': ['TYPE_PSYCHIC', 'TYPE_FIGHTING'],
                'abilities': ['ABILITY_JUSTIFIED'],
                'graphics': {'frontPic': 'graphics/pokemon/gallade/front.png'},
                'stats': {},
                'evolutions': [],
                'levelUpLearnset': [],
                'eggMoves': [],
                'teachableLearnset': [],
            }
        },
        'moves': {},
        'abilities': {'ABILITY_JUSTIFIED': {'name': 'Justified'}},
        'items': {'ITEM_GALLADITE': {'name': 'Galladite'}},
        'encounters': [],
        'trainers': [{
            'trainer_id': 'TRAINER_GALLADE',
            'name': 'Gallade User',
            'pic_path': None,
            'location': 'Route123',
            'has_party_pool': False,
            'party_size': None,
            'raw_metadata': {},
            'pokemon': [{
                'species_token': 'SPECIES_GALLADE',
                'species_symbol': 'SPECIES_GALLADE',
                'species_name': 'Gallade',
                'nickname': None,
                'held_item': 'Galladite',
                'ability': 'Justified',
                'tera_type': None,
                'evs': {'Spe': '252', 'Atk': '252', 'HP': '4'},
                'ivs': {'SpD': '31', 'Atk': '0'},
                'moves': ['Close Combat', 'Protect'],
                'level': '31',
            }],
        }],
        'types': {'TYPE_PSYCHIC': 'TYPE_PSYCHIC', 'TYPE_FIGHTING': 'TYPE_FIGHTING'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    (project_dir / 'graphics/pokemon/gallade').mkdir(parents=True)
    (project_dir / 'graphics/pokemon/gallade/front.png').write_text('x')
    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=False, verbose=False)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    SiteGenerator(config=config, model=model, env=env).run()

    trainer_page = (dist / 'trainerdex/trainer-gallade.html').read_text(encoding='utf-8')
    assert 'Gallade Level 31' in trainer_page
    assert trainer_page.index('4 HP') < trainer_page.index('252 Atk') < trainer_page.index('252 Spe')
    assert trainer_page.index('0 Atk') < trainer_page.index('31 SpD')
    assert 'Close Combat<br>Protect' in trainer_page


def test_trainer_page_shows_party_size_and_pool_rules(tmp_path: Path) -> None:
    payload = {
        'species_to_national': {'SPECIES_ABRA': 63},
        'form_species_tables': {},
        'species': {
            'SPECIES_ABRA': {
                'speciesName': 'Abra',
                'types': ['TYPE_PSYCHIC'],
                'abilities': ['ABILITY_SYNCHRONIZE'],
                'graphics': {'frontPic': 'graphics/pokemon/abra/front.png'},
                'stats': {},
                'evolutions': [],
                'levelUpLearnset': [],
                'eggMoves': [],
                'teachableLearnset': [],
            }
        },
        'moves': {},
        'abilities': {'ABILITY_SYNCHRONIZE': {'name': 'Synchronize'}},
        'items': {},
        'encounters': [],
        'trainers': [{
            'trainer_id': 'TRAINER_WENDY',
            'name': 'Wendy',
            'class_name': 'Psychic',
            'pic_path': 'graphics/trainers/front_pics/wendy.png',
            'location': 'Route123',
            'has_party_pool': True,
            'party_size': '6',
            'pool_rules': 'Doubles',
            'raw_metadata': {'Pool Rules': 'Doubles'},
            'pokemon': [{
                'species_token': 'Abra',
                'species_symbol': None,
                'species_name': 'Abra',
                'held_item': None,
                'ability': 'Synchronize',
                'tera_type': None,
                'evs': {},
                'ivs': {},
                'moves': ['Psychic'],
                'level': '50',
            }],
        }],
        'types': {'TYPE_PSYCHIC': 'TYPE_PSYCHIC'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    (project_dir / 'graphics/pokemon/abra').mkdir(parents=True)
    (project_dir / 'graphics/pokemon/abra/front.png').write_text('x')
    (project_dir / 'graphics/trainers/front_pics').mkdir(parents=True)
    (project_dir / 'graphics/trainers/front_pics/wendy.png').write_text('x')
    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=False, verbose=False)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    SiteGenerator(config=config, model=model, env=env).run()

    trainer_page = (dist / 'trainerdex/trainer-wendy.html').read_text(encoding='utf-8')
    assert 'Party Size:' in trainer_page
    assert '6' in trainer_page
    assert 'Pool Rules:' in trainer_page
    assert 'Doubles' in trainer_page


def test_trainer_party_resolves_species_names_with_apostrophes() -> None:
    payload = {
        'species_to_national': {'SPECIES_SIRFETCHD': 865},
        'form_species_tables': {},
        'species': {
            'SPECIES_SIRFETCHD': {
                'speciesName': "Sirfetch'd",
                'types': ['TYPE_FIGHTING'],
                'abilities': ['ABILITY_STEADFAST'],
                'graphics': {'frontPic': 'graphics/pokemon/sirfetchd/front.png'},
                'stats': {},
                'evolutions': [],
                'levelUpLearnset': [],
                'eggMoves': [],
                'teachableLearnset': [],
            }
        },
        'moves': {},
        'abilities': {'ABILITY_STEADFAST': {'name': 'Steadfast'}},
        'items': {},
        'encounters': [],
        'trainers': [{
            'trainer_id': 'TRAINER_TEST',
            'name': 'Test',
            'pokemon': [
                {'species_symbol': None, 'species_token': "Sirfetch'd", 'species_name': "Sirfetch'd", 'moves': []},
            ],
        }],
        'types': {'TYPE_FIGHTING': 'TYPE_FIGHTING'},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    trainer = model.trainers['TRAINER_TEST']
    assert trainer.pokemon[0].species_id == 'SPECIES_SIRFETCHD'
    assert trainer.pokemon[0].picture == 'graphics/pokemon/sirfetchd/front.png'


def test_parse_trainers_resolves_battle_type_old_and_new_formats(tmp_path: Path) -> None:
    project = tmp_path / 'project'
    (project / 'src/data').mkdir(parents=True)
    (project / 'graphics/trainers/front_pics').mkdir(parents=True)
    (project / 'data/maps/Route123').mkdir(parents=True)

    (project / 'graphics/trainers/front_pics/jacki.png').write_text('x')
    (project / 'graphics/trainers/front_pics/jacki2.png').write_text('x')
    (project / 'data/maps/Route123/scripts.inc').write_text('trainerbattle_single TRAINER_JACKI_1, Text, Text\ntrainerbattle_single TRAINER_JACKI_2, Text, Text')
    (project / 'src/data/trainers.party').write_text(
        '=== TRAINER_JACKI_1 ===\n'
        'Name: JACKI\n'
        'Class: Psychic\n'
        'Pic: jacki\n'
        'Gender: Female\n'
        'Music: Intense\n'
        'Battle Type: Doubles\n\n'
        'Abra\n'
        'Level: 12\n\n'
        '=== TRAINER_JACKI_2 ===\n'
        'Name: JACKI\n'
        'Class: Psychic\n'
        'Pic: jacki2\n'
        'Gender: Female\n'
        'Music: Intense\n'
        'Double Battle: No\n'
        'AI: Check Bad Move\n\n'
        'Kadabra\n'
        'Level: 24\n',
        encoding='utf-8',
    )

    trainers = parse_trainers(project)
    assert trainers[0]['battle_type'] == 'Doubles'
    assert trainers[1]['battle_type'] == 'Singles'


def test_trainer_page_renders_battle_type(tmp_path: Path) -> None:
    payload = {
        'species': {},
        'moves': {},
        'abilities': {},
        'items': {},
        'types': {},
        'encounters': [],
        'sprites': [],
        'species_to_national': {},
        'national_to_species': {},
        'forms': {},
        'trainers': [{
            'trainer_id': 'TRAINER_JACKI',
            'name': 'Jacki',
            'pic_path': 'graphics/trainers/front_pics/jacki.png',
            'location': 'Route123',
            'battle_type': 'Doubles',
            'pokemon': [],
        }],
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'project'
    dist = tmp_path / 'dist'
    (project_dir / 'graphics/trainers/front_pics').mkdir(parents=True)
    (project_dir / 'graphics/trainers/front_pics/jacki.png').write_text('x')
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=False, verbose=False)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    SiteGenerator(config=config, model=model, env=env).run()

    trainer_page = (dist / 'trainerdex/trainer-jacki.html').read_text(encoding='utf-8')
    assert 'Battle Type:' in trainer_page
    assert 'Doubles' in trainer_page
