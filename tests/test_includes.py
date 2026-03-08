from pathlib import Path

from obstagoon.extract.parsers.abilities import parse_abilities
from obstagoon.extract.parsers.items import parse_items
from obstagoon.extract.parsers.moves import parse_moves


def test_include_flattening_for_data_parsers(tmp_path: Path) -> None:
    (tmp_path / 'src/data').mkdir(parents=True)
    (tmp_path / 'src/data/moves_info.h').write_text('#include "moves_part.h"\n', encoding='utf-8')
    (tmp_path / 'src/data/moves_part.h').write_text('[MOVE_TACKLE] = { .name = _("Tackle"), .description = _("Hit"), .type = TYPE_NORMAL, .power = 40, .accuracy = 100, .pp = 35 },', encoding='utf-8')
    (tmp_path / 'src/data/abilities.h').write_text('#include "abilities_part.h"\n', encoding='utf-8')
    (tmp_path / 'src/data/abilities_part.h').write_text('[ABILITY_STATIC] = { .name = _("Static"), .description = _("Zap") },', encoding='utf-8')
    (tmp_path / 'src/data/items.h').write_text('#include "items_part.h"\n', encoding='utf-8')
    (tmp_path / 'src/data/items_part.h').write_text('[ITEM_THUNDER_STONE] = { .name = _("Thunder Stone"), .description = _("Stone"), .pocket = POCKET_ITEMS, .price = 2100 },', encoding='utf-8')

    assert parse_moves(tmp_path)['MOVE_TACKLE']['name'] == 'Tackle'
    assert parse_abilities(tmp_path)['ABILITY_STATIC']['name'] == 'Static'
    assert parse_items(tmp_path)['ITEM_THUNDER_STONE']['name'] == 'Thunder Stone'
