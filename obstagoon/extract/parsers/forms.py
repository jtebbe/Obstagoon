from __future__ import annotations

import re
from pathlib import Path

from ..c_utils import find_matching, project_include_roots, read_project_text


def parse_form_species_tables(project_dir: Path, defines: dict[str, int] | None = None) -> dict[str, list[str]]:
    path = project_dir / 'src/data/pokemon/form_species_tables.h'
    if not path.exists():
        return {}
    text = read_project_text(path, roots=project_include_roots(project_dir, 'src/data/pokemon'), defines=defines)
    out: dict[str, list[str]] = {}
    for m in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\b\s*\[\]\s*=\s*\{', text):
        sym = m.group(1)
        if 'FormSpeciesIdTable' not in sym:
            continue
        brace = text.find('{', m.start())
        end = find_matching(text, brace)
        body = text[brace + 1:end]
        species = re.findall(r'\bSPECIES_[A-Z0-9_]+\b', body)
        if species:
            out[sym] = species
    return out
