from __future__ import annotations

import re
from pathlib import Path

from ..c_utils import (
    evaluate_c_numeric_expr,
    extract_string_initializer,
    find_matching,
    flatten_local_includes,
    parse_named_initializers,
    preprocess_conditionals,
    project_include_roots,
    read_project_text,
    read_text,
    resolve_conditional_value,
    split_top_level_csv,
    strip_comments,
)

STAT_FIELDS = ['baseHP', 'baseAttack', 'baseDefense', 'baseSpeed', 'baseSpAttack', 'baseSpDefense', 'height', 'weight']
GRAPHIC_FIELDS = ['frontPic', 'frontPicFemale', 'backPic', 'backPicFemale', 'palette', 'paletteFemale', 'shinyPalette', 'shinyPaletteFemale', 'iconSprite', 'iconSpriteFemale', 'iconPalIndex', 'iconPalIndexFemale']


def _collect_numeric_macros(text: str, defines: dict[str, int] | None = None) -> dict[str, int]:
    defines = dict(defines or {})
    raw: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^\s*#define\s+([A-Z][A-Z0-9_]*)(?!\()\b\s+(.+?)\s*$', line)
        if not m:
            i += 1
            continue
        name = m.group(1)
        value = m.group(2).rstrip()
        while value.endswith('\\') and i + 1 < len(lines):
            value = value[:-1].rstrip() + ' ' + lines[i + 1].strip()
            i += 1
        raw[name] = value.strip()
        i += 1

    resolved = dict(defines)
    pending = dict(raw)
    for _ in range(20):
        progressed = False
        for name, value in list(pending.items()):
            resolved_value = resolve_conditional_value(value, resolved) or value
            resolved_value = resolved_value.strip()
            if not resolved_value:
                del pending[name]
                progressed = True
                continue
            if re.fullmatch(r'[-+]?((0x[0-9A-Fa-f]+)|\d+)', resolved_value):
                resolved[name] = int(resolved_value, 0)
                del pending[name]
                progressed = True
                continue
            if re.fullmatch(r'[A-Z][A-Z0-9_]*', resolved_value):
                if resolved_value in resolved:
                    resolved[name] = resolved[resolved_value]
                    del pending[name]
                    progressed = True
                continue
            identifiers = set(re.findall(r'\b[A-Z][A-Z0-9_]*\b', resolved_value))
            unresolved_ids = {tok for tok in identifiers if tok not in resolved and tok not in {'TRUE', 'FALSE'}}
            if unresolved_ids:
                continue
            maybe = evaluate_c_numeric_expr(resolved_value, resolved)
            if maybe != 0 or re.search(r'[0-9]|GEN_|TRUE|FALSE|>=|<=|==|!=|\?|:|[+\-*/%()]', resolved_value):
                resolved[name] = maybe
                del pending[name]
                progressed = True
        if not progressed:
            break
    return {k: v for k, v in resolved.items() if k not in (defines or {}) or resolved[k] != (defines or {}).get(k)}


def _resolve_scalar_token(value: str | None, defines: dict[str, int] | None = None, preserve_identifiers: bool = False) -> str | None:
    if value is None:
        return None
    text = (resolve_conditional_value(value, defines) or str(value)).strip()
    if preserve_identifiers and re.fullmatch(r'[A-Z][A-Z0-9_]*', text):
        return text
    if re.fullmatch(r'[A-Z][A-Z0-9_]*', text) and defines and text in defines:
        return str(defines[text])
    return text


def _extract_list_token(field_value: str, defines: dict[str, int] | None = None) -> list[str]:
    field_value = (field_value or '').strip()
    if not field_value:
        return []
    macro = re.match(r'[A-Z0-9_]+\((.*)\)$', field_value, re.S)
    if macro:
        field_value = '{' + macro.group(1) + '}'
    if field_value.startswith('{') and field_value.endswith('}'):
        inner = field_value[1:-1]
        values = []
        for t in split_top_level_csv(inner):
            t = (resolve_conditional_value(t.strip(), defines) or t.strip()).strip()
            if t and t not in {'0', 'NULL'}:
                values.append(t)
        return values
    return [(resolve_conditional_value(field_value, defines) or field_value).strip()]


def _collect_list_symbols(text: str, defines: dict[str, int] | None = None) -> dict[str, list[str]]:
    symbols: dict[str, list[str]] = {}
    pattern = re.compile(r'(?:static\s+)?(?:const\s+)?u(?:8|16|32)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\[[^\]]*\]\s*=\s*\{', re.S)
    for match in pattern.finditer(text):
        name = match.group(1)
        brace = text.find('{', match.start())
        if brace == -1:
            continue
        end = find_matching(text, brace)
        if end == -1:
            continue
        block = text[brace:end + 1]
        values = _extract_list_token(block, defines=defines)
        if values:
            symbols[name] = values
    return symbols


def _collect_list_macros(text: str, defines: dict[str, int] | None = None) -> dict[str, list[str]]:
    macros: dict[str, list[str]] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^\s*#define\s+([A-Z][A-Z0-9_]*)(?!\()\b\s+(.+?)\s*$', line)
        if not m:
            i += 1
            continue
        name = m.group(1)
        value = m.group(2).rstrip()
        while value.endswith('\\') and i + 1 < len(lines):
            value = value[:-1].rstrip() + ' ' + lines[i + 1].strip()
            i += 1
        value = (resolve_conditional_value(value, defines) or value).strip()
        if value:
            macros[name] = _extract_list_token(value, defines=defines)
        i += 1

    resolved: dict[str, list[str]] = {}
    pending = dict(macros)
    for _ in range(10):
        progressed = False
        for name, values in list(pending.items()):
            if len(values) == 1 and values[0] in resolved:
                values = resolved[values[0]]
            elif len(values) == 1 and values[0] in pending and values[0] != name:
                continue
            if values and any(v.startswith(('TYPE_', 'ABILITY_', 'EGG_GROUP_')) for v in values):
                resolved[name] = values
                del pending[name]
                progressed = True
            elif len(values) == 1 and values[0] in macros and values[0] in resolved:
                resolved[name] = resolved[values[0]]
                del pending[name]
                progressed = True
        if not progressed:
            break
    return resolved


def _resolve_list_value(field_value: str, symbol_lists: dict[str, list[str]], defines: dict[str, int] | None = None) -> list[str]:
    def expand(token: str, depth: int = 0) -> list[str]:
        token = (resolve_conditional_value(token, defines) or token).strip()
        if depth > 8:
            return [token]
        ref = symbol_lists.get(token)
        if not ref:
            return [token]
        expanded: list[str] = []
        for item in ref:
            expanded.extend(expand(item, depth + 1))
        return expanded

    values = _extract_list_token(field_value, defines=defines)
    resolved: list[str] = []
    for value in values:
        resolved.extend(expand(value))
    return resolved


def _clean_evo_token(token: str | None) -> str | None:
    if token is None:
        return None
    token = str(token)
    token = re.sub(r'/\*.*?\*/', '', token, flags=re.S)
    token = re.sub(r'//.*', '', token)
    token = re.sub(r'(?m)^\s*#.*$', '', token)
    token = token.strip()
    token = token.rstrip(')}],; ')
    token = token.strip()
    return token or None


def _parse_evolutions(field_value: str) -> list[dict[str, str | None]]:
    field_value = (field_value or '').strip()
    out: list[dict[str, str | None]] = []
    if not field_value:
        return out
    field_value = re.sub(r'/\*.*?\*/', '', field_value, flags=re.S)
    field_value = re.sub(r'//.*', '', field_value)
    field_value = re.sub(r'(?m)^\s*#.*$', '', field_value)
    macro = re.match(r'EVOLUTION\((.*)\)$', field_value, re.S)
    inner = macro.group(1) if macro else (field_value[1:-1].strip() if field_value.startswith('{') and field_value.endswith('}') else '')
    if not inner:
        return out
    for item in split_top_level_csv(inner):
        item = item.strip()
        if not item.startswith('{'):
            continue
        bits = [_clean_evo_token(b) for b in split_top_level_csv(item[1:-1])]
        bits = [b for b in bits if b]
        if len(bits) >= 3:
            param = bits[1] if bits[1] not in {'0', 'ITEM_NONE', 'MOVE_NONE', 'SPECIES_NONE', 'TYPE_NONE'} else None
            out.append({'method': bits[0], 'param': param, 'target_species': bits[2]})
    return out





def _looks_like_species_macro(body: str) -> bool:
    markers = ('.speciesName', '.baseHP', '.types', '.abilities', '.natDexNum', '.frontPic', '.levelUpLearnset', '.description')
    return any(marker in body for marker in markers)


def _collect_function_macros(text: str) -> dict[str, tuple[list[str], str]]:
    macros: dict[str, tuple[list[str], str]] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^\s*#define\s+([A-Z][A-Z0-9_]*)\(([^)]*)\)\s+(.+?)\s*$', line)
        if not m:
            i += 1
            continue
        name = m.group(1)
        params = [p.strip() for p in m.group(2).split(',') if p.strip()]
        body = m.group(3).rstrip()
        while body.endswith('\\') and i + 1 < len(lines):
            body = body[:-1].rstrip() + '\n' + lines[i + 1].rstrip()
            i += 1
        if _looks_like_species_macro(body):
            macros[name] = (params, body)
        i += 1
    return macros


def _collect_object_macros(text: str) -> dict[str, str]:
    macros: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^\s*#define\s+([A-Z][A-Z0-9_]*)(?!\()\b\s+(.+?)\s*$', line)
        if not m:
            i += 1
            continue
        name = m.group(1)
        body = m.group(2).rstrip()
        while body.endswith('\\') and i + 1 < len(lines):
            body = body[:-1].rstrip() + '\n' + lines[i + 1].rstrip()
            i += 1
        if _looks_like_species_macro(body):
            macros[name] = body
        i += 1
    return macros


def _substitute_macro_body(body: str, params: list[str], args: list[str]) -> str:
    out = body
    for param, arg in zip(params, args):
        arg = arg.strip()
        token_arg = re.sub(r'\s+', '', arg)
        out = re.sub(rf'([A-Za-z0-9_]+)\s*##\s*{re.escape(param)}\b', lambda m: m.group(1) + token_arg, out)
        out = re.sub(rf'\b{re.escape(param)}\s*##\s*([A-Za-z0-9_]+)', lambda m: token_arg + m.group(1), out)
        out = re.sub(rf'##\s*{re.escape(param)}\b', token_arg, out)
        out = re.sub(rf'\b{re.escape(param)}\b', arg, out)
    out = out.replace('##', '')
    return out


def _expand_species_macros(text: str) -> str:
    funcs = _collect_function_macros(text)
    objs = _collect_object_macros(text)
    if not funcs and not objs:
        return text

    def expand_in_block(block: str) -> str:
        changed = True
        rounds = 0
        while changed and rounds < 20:
            changed = False
            rounds += 1
            # function-like macros
            for name, (params, body) in funcs.items():
                pos = 0
                pieces: list[str] = []
                local = False
                marker = name + '('
                while True:
                    idx = block.find(marker, pos)
                    if idx == -1:
                        pieces.append(block[pos:])
                        break
                    # avoid partial identifier matches
                    if idx > 0 and re.match(r'[A-Za-z0-9_]', block[idx - 1]):
                        pieces.append(block[pos:idx + len(name)])
                        pos = idx + len(name)
                        continue
                    open_idx = idx + len(name)
                    close_idx = find_matching(block, open_idx, '(', ')')
                    args = split_top_level_csv(block[open_idx + 1:close_idx])
                    expanded = _substitute_macro_body(body, params, args)
                    pieces.append(block[pos:idx])
                    pieces.append(expanded)
                    pos = close_idx + 1
                    local = True
                if local:
                    block = ''.join(pieces)
                    changed = True
            for name, body in objs.items():
                pat = re.compile(rf'(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])')
                new_block, count = pat.subn(body, block)
                if count:
                    block = new_block
                    changed = True
        return block

    out = []
    pos = 0
    pat = re.compile(r'\[(SPECIES_[A-Z0-9_]+)\]\s*=')
    while True:
        m = pat.search(text, pos)
        if not m:
            out.append(text[pos:])
            break
        out.append(text[pos:m.end()])
        i = m.end()
        while i < len(text) and text[i].isspace():
            out.append(text[i])
            i += 1
        if i >= len(text):
            pos = i
            continue
        if text[i] == '{':
            end = find_matching(text, i)
            block = text[i:end + 1]
            out.append(expand_in_block(block))
            pos = end + 1
            continue
        # macro invocation or object macro until next top-level comma
        j = i
        paren = brace = bracket = 0
        in_string = False
        prev = ''
        while j < len(text):
            ch = text[j]
            if ch == '"' and prev != '\\':
                in_string = not in_string
            elif not in_string:
                if ch == '(':
                    paren += 1
                elif ch == ')':
                    paren -= 1
                elif ch == '{':
                    brace += 1
                elif ch == '}':
                    brace -= 1
                elif ch == '[':
                    bracket += 1
                elif ch == ']':
                    bracket -= 1
                elif ch == ',' and paren == brace == bracket == 0:
                    break
            prev = ch
            j += 1
        expr = text[i:j].strip()
        expanded = expand_in_block(expr)
        out.append(expanded)
        pos = j
    return ''.join(out)



def _expand_species_function_macros(text: str) -> str:
    return _expand_species_macros(text)
def _parse_species_text(text: str, species_to_national: dict[str, int | None], learnsets: dict[str, dict], defines: dict[str, int] | None = None) -> dict[str, dict]:
    text = _expand_species_macros(text)
    result: dict[str, dict] = {}
    local_defines = dict(defines or {})
    local_defines.update(_collect_numeric_macros(text, defines=local_defines))
    symbol_lists = _collect_list_symbols(text, defines=local_defines)
    symbol_lists.update(_collect_list_macros(text, defines=local_defines))
    for match in re.finditer(r'\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{', text):
        species = match.group(1)
        brace = text.find('{', match.start())
        end = find_matching(text, brace)
        block = text[brace:end + 1]
        raw_fields = parse_named_initializers(block)
        fields = {k: _resolve_scalar_token(v, local_defines) or v for k, v in raw_fields.items()}
        for key in ('baseSpecies', 'formSpeciesIdTable', 'formChangeTable'):
            if key in raw_fields:
                fields[key] = _resolve_scalar_token(raw_fields.get(key), local_defines, preserve_identifiers=True) or raw_fields.get(key)
        entry: dict = {
            'speciesName': extract_string_initializer(fields.get('speciesName', '')),
            'categoryName': extract_string_initializer(fields.get('categoryName', '')),
            'description': extract_string_initializer(fields.get('description', '')),
            'types': _resolve_list_value(fields.get('types', ''), symbol_lists, defines=local_defines)[:2],
            'abilities': _resolve_list_value(fields.get('abilities', ''), symbol_lists, defines=local_defines)[:3],
            'eggGroups': _resolve_list_value(fields.get('eggGroups', ''), symbol_lists, defines=local_defines)[:2],
            'catchRate': fields.get('catchRate'),
            'expYield': fields.get('expYield'),
            'genderRatio': fields.get('genderRatio'),
            'growthRate': fields.get('growthRate'),
            'natDexNum': species_to_national.get(species),
            'evolutions': _parse_evolutions(fields.get('evolutions', '{}')),
            'baseSpecies': fields.get('baseSpecies'),
            'formSpeciesIdTable': _resolve_scalar_token(fields.get('formSpeciesIdTable'), defines, preserve_identifiers=True),
            'formChangeTable': _resolve_scalar_token(fields.get('formChangeTable'), defines, preserve_identifiers=True),
        }
        form_idx = fields.get('formSpeciesIdTableIndex')
        entry['formSpeciesIdTableIndex'] = int(form_idx) if form_idx and form_idx.isdigit() else None
        stats = {field: (_resolve_scalar_token(fields[field], local_defines) or fields[field]) for field in STAT_FIELDS if field in fields}
        entry['stats'] = stats
        graphics = {field: fields[field] for field in GRAPHIC_FIELDS if field in fields}
        entry['graphics'] = graphics
        entry.update(learnsets.get(species, {}))
        result[species] = entry
    return result




def _parse_form_change_tables(project_dir: Path, defines: dict[str, int] | None = None) -> dict[str, list[dict[str, str | None]]]:
    path = project_dir / 'src/data/pokemon/form_change_tables.h'
    if not path.exists():
        return {}
    roots = project_include_roots(project_dir)
    text = read_project_text(path, roots=roots, defines=defines)
    result: dict[str, list[dict[str, str | None]]] = {}
    pattern = re.compile(r'static\s+const\s+struct\s+FormChange\s+([A-Za-z_][A-Za-z0-9_]*)\s*\[\]\s*=\s*\{', re.S)
    for match in pattern.finditer(text):
        name = match.group(1)
        brace = text.find('{', match.end() - 1)
        if brace == -1:
            continue
        end = find_matching(text, brace)
        if end == -1:
            continue
        block = text[brace + 1:end]
        changes: list[dict[str, str | None]] = []
        for entry_match in re.finditer(r'\{([^{}]+)\}', block, re.S):
            inner = entry_match.group(1).strip()
            if not inner or 'FORM_CHANGE_TERMINATOR' in inner:
                continue
            parts = [(_resolve_scalar_token(part.strip(), defines) or part.strip()) for part in split_top_level_csv(inner)]
            if not parts:
                continue
            method = parts[0]
            target_species = parts[1] if len(parts) > 1 else None
            item = parts[2] if len(parts) > 2 else None
            changes.append({'method': method, 'target_species': target_species, 'item': item})
        if changes:
            result[name] = changes
    return result

def parse_species(project_dir: Path, species_to_national: dict[str, int | None], learnsets: dict[str, dict], defines: dict[str, int] | None = None) -> dict[str, dict]:
    species_path = project_dir / 'src/data/pokemon/species_info.h'
    if not species_path.exists():
        return {}
    roots = project_include_roots(project_dir)
    text = read_project_text(species_path, roots=roots, defines=defines)

    cfg_path = project_dir / 'include/config/pokemon.h'
    if cfg_path.exists():
        cfg_text = preprocess_conditionals(read_text(cfg_path), defines)
        text = cfg_text + "\n" + text

    result = _parse_species_text(text, species_to_national, learnsets, defines=defines)
    form_change_tables = _parse_form_change_tables(project_dir, defines=defines)
    if result:
        for entry in result.values():
            table = entry.get('formChangeTable')
            entry['formChanges'] = form_change_tables.get(table, [])
        return result
    raw_text = strip_comments(flatten_local_includes(species_path, roots=roots))
    if cfg_path.exists():
        cfg_text = strip_comments(preprocess_conditionals(read_text(cfg_path), defines))
        raw_text = cfg_text + "\n" + raw_text
    result = _parse_species_text(raw_text, species_to_national, learnsets, defines=defines)
    for entry in result.values():
        table = entry.get('formChangeTable')
        entry['formChanges'] = form_change_tables.get(table, [])
    return result
