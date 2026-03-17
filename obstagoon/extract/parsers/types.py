from __future__ import annotations

import re
from pathlib import Path

from ..c_utils import find_first_existing, flatten_local_includes, parse_numeric_constants, parse_named_initializers, read_text, strip_comments, find_matching, preprocess_conditionals, split_top_level_csv
from .species import _expand_species_function_macros


def parse_types(project_dir: Path) -> dict[str, str]:
    info_path = project_dir / 'src/data/types_info.h'
    if info_path.exists():
        text = strip_comments(read_text(info_path))
        result: dict[str, str] = {}
        for m in re.finditer(r'\[(TYPE_[A-Z0-9_]+)\]\s*=\s*\{', text):
            type_id = m.group(1)
            brace = text.find('{', m.start())
            end = find_matching(text, brace)
            fields = parse_named_initializers(text[brace:end + 1])
            raw = fields.get('name') or fields.get('genericName')
            if raw and '"' in raw:
                from ..c_utils import extract_string_initializer
                result[type_id] = extract_string_initializer(raw) or type_id.replace('TYPE_', '').replace('_', ' ').title()
            else:
                result[type_id] = type_id.replace('TYPE_', '').replace('_', ' ').title()
        if result:
            return result
    path = find_first_existing(project_dir, ['include/constants/battle.h'])
    if path and path.exists():
        text = read_text(path)
        enum = parse_numeric_constants(text, 'TYPE_')
        if enum:
            return {key: key.replace('TYPE_', '').replace('_', ' ').title() for key in enum}
    fallback = ['TYPE_NORMAL','TYPE_FIGHTING','TYPE_FLYING','TYPE_POISON','TYPE_GROUND','TYPE_ROCK','TYPE_BUG','TYPE_GHOST','TYPE_STEEL','TYPE_MYSTERY','TYPE_FIRE','TYPE_WATER','TYPE_GRASS','TYPE_ELECTRIC','TYPE_PSYCHIC','TYPE_ICE','TYPE_DRAGON','TYPE_DARK','TYPE_FAIRY','TYPE_STELLAR']
    return {name: name.replace('TYPE_', '').replace('_', ' ').title() for name in fallback}


def parse_species_to_national(project_dir: Path) -> dict[str, int | None]:
    species_info = project_dir / 'src/data/pokemon/species_info.h'
    if not species_info.exists():
        return {}
    roots = [project_dir / 'src/data/pokemon', project_dir / 'src/data', project_dir / 'include', project_dir]
    text = _expand_species_function_macros(strip_comments(flatten_local_includes(species_info, roots=roots)))
    result: dict[str, int | None] = {}
    dex_const_path = project_dir / 'include/constants/pokedex.h'
    dex_map: dict[str, int] = {}
    if dex_const_path.exists():
        dex_map = parse_numeric_constants(read_text(dex_const_path), 'NATIONAL_DEX_')
    for m in re.finditer(r'\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{', text):
        species = m.group(1)
        brace = text.find('{', m.start())
        end = find_matching(text, brace)
        block = text[brace:end + 1]
        dex_match = re.search(r'\.natDexNum\s*=\s*([A-Z0-9_]+)', block)
        result[species] = dex_map.get(dex_match.group(1)) if dex_match else None
    return result


def _parse_enum_symbol_order(text: str, enum_name: str, prefix: str) -> list[str]:
    m = re.search(rf'enum\s+{re.escape(enum_name)}\s*\{{', text)
    if not m:
        return []
    brace = text.find('{', m.start())
    end = find_matching(text, brace)
    block = text[brace + 1:end]
    result: list[str] = []
    for part in split_top_level_csv(block):
        token = part.strip()
        if not token:
            continue
        token = re.sub(r'=.*$', '', token).strip()
        if token.startswith(prefix):
            result.append('SPECIES_' + token[len(prefix):])
    return result


def parse_hoenn_dex_order(project_dir: Path, defines: dict[str, int] | None = None) -> list[str]:
    path = project_dir / 'include/constants/pokedex.h'
    if not path.exists():
        return []
    roots = [project_dir / 'include/constants', project_dir / 'include/config', project_dir / 'include', project_dir]
    text = _expand_species_function_macros(strip_comments(flatten_local_includes(path, roots=roots)))
    text = preprocess_conditionals(text, defines=defines)
    return _parse_enum_symbol_order(text, 'HoennDexOrder', 'HOENN_DEX_')
