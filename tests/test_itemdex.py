from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from obstagoon.config import SiteConfig
from obstagoon.extract.parsers.items import parse_items
from obstagoon.generate.site import SiteGenerator
from obstagoon.model.builder import build_model


class DummyProject:
    def __init__(self, payload: dict):
        self.payload = payload

    def load_all(self) -> dict:
        return self.payload


def test_parse_items_locations_sources_and_tm_padding(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    (project / 'data/maps/Route_101').mkdir(parents=True)
    (project / 'data/maps/PetalburgCity').mkdir(parents=True)
    (project / 'src/data/items.h').write_text(
        '''const struct Item gItemsInfo[] = {
    [ITEM_POTION] = { .name = COMPOUND_STRING("Potion"), .description = COMPOUND_STRING("Heal"), .pocket = POCKET_ITEMS, .price = 300 },
    [ITEM_TM_ICE_SPINNER] = { .name = COMPOUND_STRING("TM124"), .description = COMPOUND_STRING("Teach Ice Spinner"), .pocket = POCKET_TM_HM, .price = 1000 },
    [ITEM_TM_FOCUS_PUNCH] = { .name = COMPOUND_STRING("TM01"), .description = COMPOUND_STRING("Teach Focus Punch"), .pocket = POCKET_TM_HM, .price = 1000 },
    [ITEM_ESCAPE_ROPE] = { .name = COMPOUND_STRING("Escape Rope"), .description = COMPOUND_STRING("Escape"), .pocket = POCKET_ITEMS, .price = 550 },
    [ITEM_ABOMASITE] = { .name = COMPOUND_STRING("Abomasite"), .description = COMPOUND_STRING("Mega Stone"), .pocket = POCKET_ITEMS, .price = 0 },
    [ITEM_X_ATTACK] = { .name = COMPOUND_STRING("X Attack"), .description = COMPOUND_STRING("Boost"), .pocket = POCKET_ITEMS, .price = 500 },
    [ITEM_UNUSED] = { .name = COMPOUND_STRING("Unused"), .description = COMPOUND_STRING("Unused"), .pocket = POCKET_ITEMS, .price = 0 },
};
''',
        encoding='utf-8',
    )
    (project / 'data/maps/Route_101/map.json').write_text(
        '{"events": [{"type": "object", "item": "ITEM_POTION"}, {"type": "hidden_item", "item": "ITEM_TM_ICE_SPINNER"}, {"type": "hidden_item", "item": "ITEM_X_ATTACK"}]}'
    )
    (project / 'data/maps/ShoalCave_LowTideEntranceRoom').mkdir(parents=True)
    (project / 'data/maps/ShoalCave_LowTideEntranceRoom/map.json').write_text(
        '{"object_events": [{"graphics_id": "OBJ_EVENT_GFX_MEGA_BALL", "trainer_sight_or_berry_tree_id": "ITEM_ABOMASITE", "script": "Common_EventScript_FindItem"}]}'
    )
    (project / 'data/maps/PetalburgCity/scripts.inc').write_text(
        '''PetalburgMart_Items:
    .2byte ITEM_ESCAPE_ROPE
    .2byte ITEM_X_ATTACK
    pokemartlistend

GivePotionScript::
    giveitem ITEM_POTION
''',
        encoding='utf-8',
    )
    (project / 'data/maps/MossdeepCity').mkdir(parents=True)
    (project / 'data/maps/MossdeepCity/scripts.inc').write_text(
        '''MossdeepMart_Items:
    .2byte ITEM_X_ATTACK
    pokemartlistend
''',
        encoding='utf-8',
    )

    items = parse_items(project)
    assert items['ITEM_POTION']['name'] == 'Potion'
    assert {'location': 'Route 101', 'source': 'Overworld'} in items['ITEM_POTION']['locations']
    assert {'location': 'PetalburgCity', 'source': 'NPC Event or Dialogue'} in items['ITEM_POTION']['locations']
    assert items['ITEM_TM_ICE_SPINNER']['name'] == 'TM124 Ice Spinner'
    assert items['ITEM_TM_FOCUS_PUNCH']['name'] == 'TM001 Focus Punch'
    assert items['ITEM_TM_ICE_SPINNER']['locations'] == [{'location': 'Route 101', 'source': 'Hidden Item'}]
    assert {'location': 'PetalburgCity', 'source': 'Shop'} in items['ITEM_ESCAPE_ROPE']['locations']
    assert items['ITEM_ABOMASITE']['locations'] == [{'location': 'ShoalCave LowTideEntranceRoom', 'source': 'Overworld'}]
    assert items['ITEM_UNUSED']['locations'] == []
    assert sorted(items['ITEM_X_ATTACK']['locations'], key=lambda row: (row['source'], row['location'])) == [
        {'location': 'Route 101', 'source': 'Hidden Item'},
        {'location': 'MossdeepCity', 'source': 'Shop'},
        {'location': 'PetalburgCity', 'source': 'Shop'},
    ]


def test_itemdex_page_renders_searches_and_consolidates_rows(tmp_path: Path) -> None:
    payload = {
        'species_to_national': {},
        'form_species_tables': {},
        'species': {},
        'moves': {},
        'abilities': {},
        'items': {
            'ITEM_TM_ICE_SPINNER': {'name': 'TM124 Ice Spinner', 'locations': [{'location': 'Route 101', 'source': 'Hidden Item'}]},
            'ITEM_ESCAPE_ROPE': {'name': 'Escape Rope', 'locations': [{'location': 'Petalburg City', 'source': 'Shop'}]},
            'ITEM_X_ATTACK': {
                'name': 'X Attack',
                'locations': [
                    {'location': 'Route 109', 'source': 'Hidden Item'},
                    {'location': 'Verdanturf Town Mart', 'source': 'Shop'},
                    {'location': 'MossdeepCity Mart', 'source': 'Shop'},
                    {'location': 'Slateport City', 'source': 'NPC Event or Dialogue'},
                    {'location': 'Route 110', 'source': 'Overworld'},
                ],
            },
            'ITEM_UNUSED': {'name': 'Unused', 'locations': []},
        },
        'encounters': [],
        'trainers': [],
        'types': {},
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    project_dir.mkdir()
    dist = tmp_path / 'dist'
    config = SiteConfig(project_dir=project_dir, dist_dir=dist, site_title='Test', copy_assets=False, verbose=False)
    env = Environment(loader=FileSystemLoader(str((__import__('obstagoon').__path__[0])) + '/templates'), autoescape=select_autoescape(['html', 'xml']), trim_blocks=True, lstrip_blocks=True)
    SiteGenerator(config=config, model=model, env=env).run()

    itemdex = (dist / 'itemdex/index.html').read_text(encoding='utf-8')
    index_html = (dist / 'index.html').read_text(encoding='utf-8')
    assert 'Itemdex' in itemdex
    assert 'TM124 Ice Spinner' in itemdex
    assert 'Route 101' in itemdex
    assert 'Hidden Item' in itemdex
    assert 'data-filter-input' in itemdex
    assert 'Unused' not in itemdex
    assert 'itemdex/index.html' in index_html

    x_attack_start = itemdex.index('X Attack')
    x_attack_block = itemdex[x_attack_start:]
    assert x_attack_block.index('MossdeepCity Mart') < x_attack_block.index('Verdanturf Town Mart')
    assert x_attack_block.index('Verdanturf Town Mart') < x_attack_block.index('Slateport City')
    assert x_attack_block.index('Slateport City') < x_attack_block.index('Route 110')
    assert x_attack_block.index('Route 110') < x_attack_block.index('Route 109')
    assert x_attack_block.count('<td>X Attack</td>') == 1
    assert x_attack_block.count('<td>Shop</td>') == 1
    assert x_attack_block.count('<td>NPC Event or Dialogue</td>') == 1
    assert x_attack_block.count('<td>Overworld</td>') == 1
    assert x_attack_block.count('<td>Hidden Item</td>') == 1

def test_shop_block_does_not_swallow_prior_npc_item_lines(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    (project / 'data/maps/SlateportCity').mkdir(parents=True)
    (project / 'src/data/items.h').write_text(
        '''const struct Item gItemsInfo[] = {
    [ITEM_BURGLARY_KIT] = { .name = COMPOUND_STRING("Burglary Kit"), .description = COMPOUND_STRING("Custom"), .pocket = POCKET_KEY_ITEMS, .price = 0 },
    [ITEM_POTION] = { .name = COMPOUND_STRING("Potion"), .description = COMPOUND_STRING("Heal"), .pocket = POCKET_ITEMS, .price = 300 },
};
''',
        encoding='utf-8',
    )
    (project / 'data/maps/SlateportCity/scripts.inc').write_text(
        '''SlateportCity_EventScript_ClerkRematch::
    giveitem ITEM_BURGLARY_KIT
    end

SlateportCityMart_Items:
    .2byte ITEM_POTION
    pokemartlistend
''',
        encoding='utf-8',
    )

    items = parse_items(project)
    assert items['ITEM_BURGLARY_KIT']['locations'] == [{'location': 'SlateportCity', 'source': 'NPC Event or Dialogue'}]
    assert items['ITEM_POTION']['locations'] == [{'location': 'SlateportCity', 'source': 'Shop'}]



def test_checkitem_does_not_count_as_item_location(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    (project / 'data/maps/Route_111').mkdir(parents=True)
    (project / 'src/data/items.h').write_text(
        '''const struct Item gItemsInfo[] = {
    [ITEM_GO_GOGGLES] = { .name = COMPOUND_STRING("Go Goggles"), .description = COMPOUND_STRING("Goggles"), .pocket = POCKET_KEY_ITEMS, .price = 0 },
    [ITEM_DEVON_GOODS] = { .name = COMPOUND_STRING("Devon Goods"), .description = COMPOUND_STRING("Goods"), .pocket = POCKET_KEY_ITEMS, .price = 0 },
};
''',
        encoding='utf-8',
    )
    (project / 'data/maps/Route_111/scripts.inc').write_text(
        '''Route111_CheckForGoggles::
    checkitem ITEM_GO_GOGGLES
    goto_if_eq VAR_RESULT, FALSE, Route111_NoGoggles
    giveitem ITEM_DEVON_GOODS
    end
''',
        encoding='utf-8',
    )

    items = parse_items(project)
    assert items['ITEM_GO_GOGGLES']['locations'] == []
    assert items['ITEM_DEVON_GOODS']['locations'] == [{'location': 'Route 111', 'source': 'NPC Event or Dialogue'}]

def test_removeitem_does_not_count_as_item_location(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    (project / 'data/maps/MeteorFalls').mkdir(parents=True)
    (project / 'src/data/items.h').write_text(
        '''const struct Item gItemsInfo[] = {
    [ITEM_METEORITE] = { .name = COMPOUND_STRING("Meteorite"), .description = COMPOUND_STRING("Rock"), .pocket = POCKET_KEY_ITEMS, .price = 0 },
    [ITEM_MAGMA_EMBLEM] = { .name = COMPOUND_STRING("Magma Emblem"), .description = COMPOUND_STRING("Emblem"), .pocket = POCKET_KEY_ITEMS, .price = 0 },
};
''',
        encoding='utf-8',
    )
    (project / 'data/maps/MeteorFalls/scripts.inc').write_text(
        '''MeteorFalls_RemoveMeteorite::
    removeitem ITEM_METEORITE
    giveitem ITEM_MAGMA_EMBLEM
    end
''',
        encoding='utf-8',
    )

    items = parse_items(project)
    assert items['ITEM_METEORITE']['locations'] == []
    assert items['ITEM_MAGMA_EMBLEM']['locations'] == [{'location': 'MeteorFalls', 'source': 'NPC Event or Dialogue'}]
