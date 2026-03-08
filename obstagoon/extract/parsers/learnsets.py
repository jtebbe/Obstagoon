from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from ..c_utils import (
    find_files,
    find_matching,
    flatten_local_includes,
    parse_named_initializers,
    preprocess_conditionals,
    read_text,
    resolve_conditional_value,
    split_top_level_csv,
    strip_comments,
)


def _parse_level_up_array(body: str | None) -> list[dict[str, str]]:
    if not body:
        return []
    result: list[dict[str, str]] = []
    for item in split_top_level_csv(body):
        level_match = re.search(r'LEVEL_UP_MOVE\(([^,]+),\s*([^)]+)\)', item)
        if level_match:
            result.append({'level': level_match.group(1).strip(), 'move': level_match.group(2).strip()})
            continue
        pair_match = re.search(r'\{\s*\.level\s*=\s*([^,]+),\s*\.move\s*=\s*([^}]+)\}', item)
        if pair_match:
            result.append({'level': pair_match.group(1).strip(), 'move': pair_match.group(2).strip()})
    return result


def _parse_symbol_list_array(body: str | None, prefixes: tuple[str, ...], stop_tokens: set[str] | None = None) -> list[str]:
    if not body:
        return []
    out: list[str] = []
    stop_tokens = stop_tokens or set()
    for item in split_top_level_csv(body):
        token = item.strip().replace('(u16)', '').strip()
        if not token or token in stop_tokens or token == '0':
            continue
        if token.startswith(prefixes):
            out.append(token)
    return out


def _load_teachables_from_json(project_dir: Path) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    learnables = project_dir / 'src/data/pokemon/all_learnables.json'
    if not learnables.exists():
        return out
    with learnables.open(encoding='utf-8') as f:
        data = json.load(f)
    for key, moves in data.items():
        species = key if key.startswith('SPECIES_') else f'SPECIES_{key}'
        out[species] = [{'source': 'Teachable', 'value': move} for move in moves]
    special = project_dir / 'src/data/pokemon/special_movesets.json'
    if special.exists():
        with special.open(encoding='utf-8') as f:
            data = json.load(f)
        universal = data.get('universalMoves', [])
        signature = set(data.get('signatureTeachables', []))
        for species, items in list(out.items()):
            seen = {x['value'] for x in items}
            for move in universal:
                if move not in seen:
                    items.append({'source': 'Universal', 'value': move})
            out[species] = items
        for items in out.values():
            for item in items:
                if item['value'] in signature:
                    item['special'] = 'signatureTeachables'
    return out


def parse_learnsets(project_dir: Path, defines: dict[str, int] | None = None) -> dict[str, dict]:
    species_info_path = project_dir / 'src/data/pokemon/species_info.h'
    roots = [project_dir / 'src/data/pokemon', project_dir / 'src/data', project_dir / 'include', project_dir]
    species_text = strip_comments(preprocess_conditionals(flatten_local_includes(species_info_path, roots=roots), defines)) if species_info_path.exists() else ''
    if species_info_path.exists() and '[SPECIES_' not in species_text:
        species_text = strip_comments(flatten_local_includes(species_info_path, roots=roots))

    source_files = find_files(
        project_dir,
        '/pokemon/level_up_learnsets',
        '/pokemon/egg_moves',
        '/pokemon/tmhm_learnsets',
        '/pokemon/tutor_learnsets',
        '/pokemon/learnsets',
        '/pokemon/teachable_learnsets',
    )
    texts = {path: strip_comments(preprocess_conditionals(read_text(path), defines)) for path in source_files}

    symbol_to_body: dict[str, str] = {}
    for text in texts.values():
        for m in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\b\s*\[\]\s*=\s*\{', text):
            symbol = m.group(1)
            brace = text.find('{', m.start())
            end = find_matching(text, brace)
            symbol_to_body[symbol] = text[brace + 1:end]

    results = defaultdict(lambda: {'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': []})
    json_teachables = _load_teachables_from_json(project_dir)

    for m in re.finditer(r'\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{', species_text):
        species = m.group(1)
        brace = species_text.find('{', m.start())
        end = find_matching(species_text, brace)
        block = species_text[brace:end + 1]
        fields = {k: resolve_conditional_value(v, defines) or v for k, v in parse_named_initializers(block).items()}

        level_sym = fields.get('levelUpLearnset')
        egg_sym = fields.get('eggMoveLearnset') or fields.get('eggMoves')
        teachable_sym = fields.get('teachableLearnset') or fields.get('tmhmLearnset')

        if level_sym:
            results[species]['levelUpLearnset'] = _parse_level_up_array(symbol_to_body.get(level_sym.strip('& ')))
        if egg_sym:
            results[species]['eggMoves'] = _parse_symbol_list_array(
                symbol_to_body.get(egg_sym.strip('& ')),
                ('MOVE_',),
                stop_tokens={'MOVE_UNAVAILABLE', 'MOVE_NONE'},
            )
        if teachable_sym and teachable_sym.strip('& ') in symbol_to_body:
            body = symbol_to_body.get(teachable_sym.strip('& '))
            results[species]['teachableLearnset'] = [
                {'source': 'Teachable', 'value': t}
                for t in _parse_symbol_list_array(
                    body,
                    ('MOVE_', 'ITEM_'),
                    stop_tokens={'MOVE_UNAVAILABLE', 'MOVE_NONE', 'TEACHABLE_LEARNSET_END', '0xFFFF', 'FFFF'},
                )
            ]
        elif species in json_teachables:
            results[species]['teachableLearnset'] = json_teachables[species]

    return dict(results)
