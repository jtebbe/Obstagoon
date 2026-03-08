from __future__ import annotations

import re
from pathlib import Path

from ..c_utils import extract_string_initializer, find_matching, find_first_existing, parse_named_initializers, project_include_roots, read_project_text


def parse_items(project_dir: Path) -> dict[str, dict]:
    path = find_first_existing(project_dir, [
        'src/data/items.h',
        'src/data/item_icon_table.h',
        'src/item.c',
    ])
    if not path:
        return {}
    text = read_project_text(path, roots=project_include_roots(project_dir))
    out: dict[str, dict] = {}
    for m in re.finditer(r'\[(ITEM_[A-Z0-9_]+)\]\s*=\s*\{', text):
        item = m.group(1)
        brace = text.find('{', m.start())
        end = find_matching(text, brace)
        fields = parse_named_initializers(text[brace:end + 1])
        out[item] = {
            'name': extract_string_initializer(fields.get('name', '')),
            'description': extract_string_initializer(fields.get('description', '')),
            'pocket': fields.get('pocket'),
            'price': fields.get('price'),
        }
    return out
