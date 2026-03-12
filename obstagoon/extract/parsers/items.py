from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from ..c_utils import extract_string_initializer, find_matching, find_first_existing, parse_named_initializers, project_include_roots, read_project_text


def _humanize_map_dirname(name: str) -> str:
    return str(name or '').replace('_', ' ').strip()


def _normalize_tm_base_name(base_name: str | None, tm_width: int) -> str | None:
    if not base_name or tm_width < 3:
        return base_name
    match = re.fullmatch(r'TM\s*(\d+)', base_name.strip(), flags=re.IGNORECASE)
    if not match:
        return base_name
    return f'TM{int(match.group(1)):0{tm_width}d}'


def _tm_display_name(item_id: str, base_name: str | None, tm_width: int) -> str | None:
    normalized_base_name = _normalize_tm_base_name(base_name, tm_width)
    if not item_id.startswith('ITEM_TM_'):
        return normalized_base_name
    suffix = item_id.removeprefix('ITEM_TM_').replace('_', ' ').title()
    if normalized_base_name and suffix:
        return f'{normalized_base_name} {suffix}'
    return normalized_base_name or suffix or None


def _extract_items_from_map_json(path: Path) -> list[tuple[str, str]]:
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return []

    found: list[tuple[str, str]] = []

    def walk(node):
        if isinstance(node, dict):
            item = node.get('item')
            if isinstance(item, str) and item.startswith('ITEM_'):
                source = 'Hidden Item' if node.get('type') == 'hidden_item' else 'Overworld'
                found.append((item, source))

            object_event_item = node.get('trainer_sight_or_berry_tree_id')
            script = str(node.get('script') or '')
            graphics_id = str(node.get('graphics_id') or '')
            if (
                isinstance(object_event_item, str)
                and object_event_item.startswith('ITEM_')
                and ('FindItem' in script or 'ITEM_BALL' in graphics_id or 'MEGA_BALL' in graphics_id)
            ):
                found.append((object_event_item, 'Overworld'))

            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    return found


def _extract_items_from_scripts(path: Path) -> list[tuple[str, str]]:
    try:
        text = path.read_text(encoding='utf-8')
    except Exception:
        return []

    results: list[tuple[str, str]] = []
    mart_ranges: list[tuple[int, int]] = []

    mart_blocks = re.finditer(
        r'(?ms)^[A-Za-z0-9_]+:\s*\n((?:\s*\.2byte\s+ITEM_[A-Z0-9_]+\s*\n)+)\s*pokemartlistend\b',
        text,
    )
    for block in mart_blocks:
        mart_ranges.append((block.start(), block.end()))
        for item in re.findall(r'\bITEM_[A-Z0-9_]+\b', block.group(1)):
            results.append((item, 'Shop'))

    def in_mart_block(pos: int) -> bool:
        return any(start <= pos < end for start, end in mart_ranges)

    for match in re.finditer(r'^.*\bITEM_[A-Z0-9_]+\b.*$', text, flags=re.MULTILINE):
        if in_mart_block(match.start()):
            continue
        stripped = match.group(0).strip()
        if not stripped or '.2byte' in stripped:
            continue
        if stripped.startswith('checkitem '):
            continue
        if stripped.startswith('removeitem '):
            continue
        for item in re.findall(r'\bITEM_[A-Z0-9_]+\b', stripped):
            results.append((item, 'NPC Event or Dialogue'))

    return results


def _parse_item_locations(project_dir: Path) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    maps_dir = project_dir / 'data' / 'maps'
    if not maps_dir.exists():
        return {}

    for map_dir in sorted(p for p in maps_dir.iterdir() if p.is_dir()):
        location = _humanize_map_dirname(map_dir.name)
        seen: set[tuple[str, str]] = set()

        map_json = map_dir / 'map.json'
        if map_json.exists():
            for item, source in _extract_items_from_map_json(map_json):
                key = (item, source)
                if key in seen:
                    continue
                seen.add(key)
                out[item].append({'location': location, 'source': source})

        scripts = map_dir / 'scripts.inc'
        if scripts.exists():
            for item, source in _extract_items_from_scripts(scripts):
                key = (item, source)
                if key in seen:
                    continue
                seen.add(key)
                out[item].append({'location': location, 'source': source})

    return dict(out)


def _tm_number_width(base_names: list[str | None]) -> int:
    max_number = 0
    for base_name in base_names:
        if not base_name:
            continue
        match = re.fullmatch(r'TM\s*(\d+)', base_name.strip(), flags=re.IGNORECASE)
        if not match:
            continue
        max_number = max(max_number, int(match.group(1)))
    return len(str(max_number)) if max_number >= 100 else 0


def parse_items(project_dir: Path) -> dict[str, dict]:
    path = find_first_existing(project_dir, [
        'src/data/items.h',
        'src/data/item_icon_table.h',
        'src/item.c',
    ])
    if not path:
        return {}
    text = read_project_text(path, roots=project_include_roots(project_dir))
    item_locations = _parse_item_locations(project_dir)
    item_rows: list[tuple[str, dict, str | None]] = []
    for m in re.finditer(r'\[(ITEM_[A-Z0-9_]+)\]\s*=\s*\{', text):
        item = m.group(1)
        brace = text.find('{', m.start())
        end = find_matching(text, brace)
        fields = parse_named_initializers(text[brace:end + 1])
        base_name = extract_string_initializer(fields.get('name', ''))
        item_rows.append((item, fields, base_name))

    tm_width = _tm_number_width([base_name for _, _, base_name in item_rows])
    out: dict[str, dict] = {}
    for item, fields, base_name in item_rows:
        out[item] = {
            'name': _tm_display_name(item, base_name, tm_width),
            'description': extract_string_initializer(fields.get('description', '')),
            'pocket': fields.get('pocket'),
            'price': fields.get('price'),
            'locations': item_locations.get(item, []),
        }
    return out
