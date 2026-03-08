from __future__ import annotations

import re
from pathlib import Path

from ..c_utils import extract_string_initializer, find_matching, find_first_existing, flatten_local_includes, parse_named_initializers, project_include_roots, read_project_text, resolve_conditional_value, split_top_level_csv, strip_comments


def _parse_moves_text(text: str, defines: dict[str, int] | None = None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for m in re.finditer(r'\[(MOVE_[A-Z0-9_]+)\]\s*=\s*\{', text):
        move = m.group(1)
        brace = text.find('{', m.start())
        end = find_matching(text, brace)
        fields = {k: resolve_conditional_value(v, defines) or v for k, v in parse_named_initializers(text[brace:end + 1]).items()}
        flags = []
        if 'flags' in fields and fields['flags'].startswith('{'):
            flags = [x.strip() for x in split_top_level_csv(fields['flags'][1:-1]) if x.strip()]
        out[move] = {
            'name': extract_string_initializer(fields.get('name', '')),
            'description': extract_string_initializer(fields.get('description', '')),
            'type': fields.get('type'),
            'power': fields.get('power'),
            'accuracy': fields.get('accuracy'),
            'pp': fields.get('pp'),
            'category': fields.get('split') or fields.get('category'),
            'flags': flags,
        }
    return out


def parse_moves(project_dir: Path, defines: dict[str, int] | None = None) -> dict[str, dict]:
    path = find_first_existing(project_dir, [
        'src/data/moves_info.h',
        'src/data/battle_moves.h',
        'src/data/moves.h',
    ])
    if not path:
        return {}
    roots = project_include_roots(project_dir)
    text = read_project_text(path, roots=roots, defines=defines)
    out = _parse_moves_text(text, defines=defines)
    if out:
        return out
    raw_text = strip_comments(flatten_local_includes(path, roots=roots))
    return _parse_moves_text(raw_text, defines=defines)
