from __future__ import annotations

import re
from pathlib import Path

from ..c_utils import extract_string_initializer, find_matching, find_first_existing, parse_named_initializers, project_include_roots, read_project_text, resolve_conditional_value


def parse_abilities(project_dir: Path, defines: dict[str, int] | None = None) -> dict[str, dict]:
    path = find_first_existing(project_dir, [
        'src/data/abilities.h',
        'src/data/ability_descriptions.h',
    ])
    if not path:
        return {}
    text = read_project_text(path, roots=project_include_roots(project_dir), defines=defines)
    out: dict[str, dict] = {}
    for m in re.finditer(r'\[(ABILITY_[A-Z0-9_]+)\]\s*=\s*\{', text):
        ability = m.group(1)
        brace = text.find('{', m.start())
        end = find_matching(text, brace)
        fields = {k: resolve_conditional_value(v, defines) or v for k, v in parse_named_initializers(text[brace:end + 1]).items()}
        out[ability] = {
            'name': extract_string_initializer(fields.get('name', '')),
            'description': extract_string_initializer(fields.get('description', '')),
        }
    return out
