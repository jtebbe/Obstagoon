from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..c_utils import find_files, parse_named_initializers, read_text, split_top_level_csv, strip_comments


METHOD_FIELDS = {
    'landMonsInfo': 'land',
    'waterMonsInfo': 'water',
    'rockSmashMonsInfo': 'rock-smash',
    'fishingMonsInfo': 'fishing',
}

JSON_METHODS = {
    'land_mons': 'land',
    'water_mons': 'water',
    'rock_smash_mons': 'rock-smash',
    'fishing_mons': 'fishing',
}

FISHING_GROUP_LABELS = {
    'old_rod': 'old-rod',
    'good_rod': 'good-rod',
    'super_rod': 'super-rod',
}


def _display_name(map_name: str | None, base_label: str | None = None) -> str | None:
    source = map_name or base_label
    if not source:
        return None
    cleaned = source
    for prefix in ('MAPSEC_', 'MAP_'):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    cleaned = cleaned.replace('__', '_').replace('_', ' ')
    return cleaned.title()


def _append_slot(bucket: list[dict[str, str]], entry: dict[str, Any], rate: int | None = None, method: str | None = None) -> None:
    slot = {
        'species': str(entry.get('species')),
        'min_level': str(entry.get('min_level')) if entry.get('min_level') is not None else None,
        'max_level': str(entry.get('max_level')) if entry.get('max_level') is not None else None,
        'rate': str(rate) if rate is not None else None,
        'method': method,
    }
    bucket.append(slot)


def _area_signature(area: dict[str, Any]) -> str:
    return json.dumps(area.get('encounters', {}), sort_keys=True)


def _parse_generated_json(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as f:
        payload = json.load(f)
    groups = payload.get('wild_encounter_groups', [])
    areas: list[dict] = []
    seen: set[tuple[str | None, str | None, str]] = set()
    for group in groups:
        field_meta = {field.get('type'): field for field in group.get('fields', [])}
        for encounter in group.get('encounters', []):
            map_name = encounter.get('map')
            base_label = encounter.get('base_label')
            area = {
                'map': map_name,
                'base_label': base_label,
                'display_name': _display_name(map_name, base_label),
                'encounters': {},
            }
            for json_key, label in JSON_METHODS.items():
                method_block = encounter.get(json_key)
                if not method_block:
                    continue
                rates = field_meta.get(json_key, {}).get('encounter_rates', [])
                slots: list[dict[str, str]] = []
                mons = method_block.get('mons', [])
                if json_key == 'fishing_mons':
                    groups_meta = field_meta.get(json_key, {}).get('groups', {})
                    for rod_key, indexes in groups_meta.items():
                        rod_label = FISHING_GROUP_LABELS.get(rod_key, rod_key.replace('_', '-'))
                        for idx in indexes:
                            if 0 <= idx < len(mons):
                                rate = rates[idx] if idx < len(rates) else None
                                _append_slot(slots, mons[idx], rate=rate, method=rod_label)
                else:
                    for idx, mon in enumerate(mons):
                        rate = rates[idx] if idx < len(rates) else None
                        _append_slot(slots, mon, rate=rate, method=label)
                if slots:
                    area['encounters'][label] = slots
            if area['encounters']:
                key = (map_name, base_label, _area_signature(area))
                if key not in seen:
                    seen.add(key)
                    areas.append(area)
    return areas


def _parse_slot_block(text: str) -> list[dict[str, str]]:
    slots: list[dict[str, str]] = []
    for item in split_top_level_csv(text):
        if not item.startswith('{'):
            continue
        bits = [x.strip() for x in split_top_level_csv(item[1:-1])]
        if len(bits) >= 3:
            slots.append({'min_level': bits[0], 'max_level': bits[1], 'species': bits[2]})
        elif len(bits) == 2:
            slots.append({'rate': bits[0], 'species': bits[1]})
    return slots


def _parse_c_sources(project_dir: Path) -> list[dict]:
    files = find_files(project_dir, '/wild_encounters', '/encounters')
    if not files:
        return []
    areas: list[dict] = []
    for path in files:
        if path.suffix == '.json':
            continue
        text = strip_comments(read_text(path))
        for m in re.finditer(r'\.map\s*=\s*([A-Z0-9_]+)', text):
            area_start = text.rfind('{', 0, m.start())
            if area_start == -1:
                continue
            depth = 0
            i = area_start
            while i < len(text):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            block = text[area_start:i + 1]
            fields = parse_named_initializers(block)
            area = {'map': fields.get('map'), 'encounters': {}}
            for raw_field, label in METHOD_FIELDS.items():
                raw_val = fields.get(raw_field)
                if raw_val and raw_val.startswith('&'):
                    sym = raw_val[1:].strip()
                    sym_match = re.search(rf'\b{re.escape(sym)}\b[^=;]*=\s*\{{', text)
                    if sym_match:
                        brace = text.find('{', sym_match.start())
                        depth = 0
                        j = brace
                        while j < len(text):
                            if text[j] == '{':
                                depth += 1
                            elif text[j] == '}':
                                depth -= 1
                                if depth == 0:
                                    break
                            j += 1
                        subblock = text[brace:j + 1]
                        subfields = parse_named_initializers(subblock)
                        mons = subfields.get('mons')
                        if mons and mons.startswith('{'):
                            area['encounters'][label] = _parse_slot_block(mons[1:-1])
            if area['encounters']:
                area['display_name'] = _display_name(area['map'])
                areas.append(area)
    deduped = []
    seen = set()
    for area in areas:
        key = (area['map'], _area_signature(area))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(area)
    return deduped


def parse_encounters(project_dir: Path, generated_json: Path | None = None) -> list[dict]:
    json_candidates: list[Path] = []
    if generated_json and generated_json.exists():
        json_candidates.append(generated_json)
    default_generated = project_dir / 'src/data/wild_encounters.json'
    if default_generated.exists():
        json_candidates.append(default_generated)
    for path in find_files(project_dir, '/wild_encounters', '/encounters'):
        if path.suffix == '.json':
            json_candidates.append(path)
    for candidate in json_candidates:
        try:
            data = json.loads(read_text(candidate))
        except Exception:
            continue
        if isinstance(data, dict) and 'wild_encounter_groups' in data:
            return _parse_generated_json(candidate)
    return _parse_c_sources(project_dir)
