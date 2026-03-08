from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Any
from pathlib import Path
from typing import Iterable

INCLUDE_RE = re.compile(r'^\s*#include\s+"([^"]+)"', re.MULTILINE)
QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')


CONFIG_DEFINE_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)(?!\()\b\s+(.+?)\s*$', re.MULTILINE)
PREPROC_DIRECTIVE_RE = re.compile(r'(?<!\n)(?:\s*)(#(?:ifdef|ifndef|if|elif|else|endif|define|undef|include)\b)')


def normalize_preprocessor_layout(text: str) -> str:
    # Some expansion data headers are minified so preprocessor directives appear mid-line.
    # Put each directive on its own line so the lightweight preprocessor can interpret them.
    text = PREPROC_DIRECTIVE_RE.sub(lambda m: "\n" + m.group(1), text)
    out: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip().startswith('#'):
            out.append(line)
            continue
        stripped = line.lstrip()
        m = re.match(r'^(#(?:if|elif|ifdef|ifndef)\s+.+?)(\s+(?=[\[\.\{\}]))(.*)$', stripped)
        if m:
            out.append(m.group(1))
            if m.group(3).strip():
                out.append(m.group(3).strip())
            continue
        m = re.match(r'^(#(?:else|endif))(\s+(?=[\[\.\{\}]))(.*)$', stripped)
        if m:
            out.append(m.group(1))
            if m.group(3).strip():
                out.append(m.group(3).strip())
            continue
        out.append(line)
    return "\n".join(out)


def _replace_defined_calls(expr: str, defines: dict[str, int]) -> str:
    return re.sub(r'defined\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', lambda m: '1' if m.group(1) in defines else '0', expr)


def _strip_function_like_macros(expr: str) -> str:
    prev = None
    while prev != expr:
        prev = expr
        expr = re.sub(r'\b(?!defined\b)[A-Za-z_][A-Za-z0-9_]*\s*\([^()]*\)', '0', expr)
    return expr


def _prepare_expr(expr: str, defines: dict[str, int] | None = None) -> str:
    defines = defines or {}
    expr = strip_comments(str(expr)).strip()
    if not expr:
        return ''
    expr = _replace_defined_calls(expr, defines)
    expr = _strip_function_like_macros(expr)
    expr = expr.replace('&&', ' and ').replace('||', ' or ')
    expr = re.sub(r'!([^=])', r' not \1', expr)
    expr = expr.replace('TRUE', '1').replace('FALSE', '0')

    def repl(m: re.Match[str]) -> str:
        token = m.group(0)
        if token in {'and', 'or', 'not'}:
            return token
        return str(defines.get(token, 0))

    expr = re.sub(r'\b[A-Za-z_][A-Za-z0-9_]*\b', repl, expr)
    expr = re.sub(r'[^0-9xXa-fA-F_()<>!=&|+\-*/%?.: 	andornot]', ' ', expr)
    return expr


def evaluate_c_numeric_expr(expr: str, defines: dict[str, int] | None = None) -> int:
    expr = _prepare_expr(expr, defines)
    if not expr or re.search(r'\d+\s*\(', expr):
        return 0
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', SyntaxWarning)
            value = eval(expr, {"__builtins__": {}}, {})
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        return 0
    except Exception:
        return 0


def evaluate_c_expr(expr: str, defines: dict[str, int] | None = None) -> int:
    return 1 if bool(evaluate_c_numeric_expr(expr, defines)) else 0


def _find_top_level_char(text: str, target: str) -> int:
    paren = brace = bracket = 0
    in_string = False
    prev = ''
    for i, ch in enumerate(text):
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
            elif ch == target and paren == brace == bracket == 0:
                return i
        prev = ch
    return -1


def _find_matching_colon_for_ternary(text: str, q_idx: int) -> int:
    paren = brace = bracket = 0
    in_string = False
    prev = ''
    depth = 0
    for i in range(q_idx + 1, len(text)):
        ch = text[i]
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
            elif ch == '?' and paren == brace == bracket == 0:
                depth += 1
            elif ch == ':' and paren == brace == bracket == 0:
                if depth == 0:
                    return i
                depth -= 1
        prev = ch
    return -1




def _strip_wrapping_parens(text: str) -> str:
    text = text.strip()
    while text.startswith('(') and text.endswith(')'):
        try:
            end = find_matching(text, 0, '(', ')')
        except Exception:
            break
        if end != len(text) - 1:
            break
        text = text[1:-1].strip()
    return text

def resolve_conditional_value(value: str | None, defines: dict[str, int] | None = None) -> str | None:
    if value is None:
        return None
    defines = defines or {}
    text = _strip_wrapping_parens(str(value).strip())
    if not text:
        return text
    # unwrap ternaries recursively, including ones wrapped in parentheses
    while True:
        q_idx = _find_top_level_char(text, '?')
        if q_idx == -1:
            break
        colon_idx = _find_matching_colon_for_ternary(text, q_idx)
        if colon_idx == -1:
            break
        cond = text[:q_idx].strip()
        left = text[q_idx + 1:colon_idx].strip()
        right = text[colon_idx + 1:].strip()
        text = left if evaluate_c_expr(cond, defines) else right
        text = text.strip()
    return text


def preprocess_conditionals(text: str, defines: dict[str, int] | None = None) -> str:
    defines = defines or {}
    text = normalize_preprocessor_layout(text)
    lines = text.splitlines()
    out: list[str] = []
    stack: list[dict[str, Any]] = []

    def active() -> bool:
        return all(frame['active'] for frame in stack)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#if '):
            cond = stripped[4:].strip()
            parent_active = active()
            cond_true = bool(evaluate_c_expr(cond, defines)) if parent_active else False
            stack.append({'parent': parent_active, 'seen_true': cond_true, 'active': parent_active and cond_true})
            continue
        if stripped.startswith('#ifdef '):
            name = stripped[7:].strip()
            parent_active = active()
            cond_true = parent_active and (name in defines)
            stack.append({'parent': parent_active, 'seen_true': cond_true, 'active': cond_true})
            continue
        if stripped.startswith('#ifndef '):
            name = stripped[8:].strip()
            parent_active = active()
            cond_true = parent_active and (name not in defines)
            stack.append({'parent': parent_active, 'seen_true': cond_true, 'active': cond_true})
            continue
        if stripped.startswith('#elif '):
            if stack:
                frame = stack[-1]
                if not frame['parent'] or frame['seen_true']:
                    frame['active'] = False
                else:
                    cond_true = bool(evaluate_c_expr(stripped[6:].strip(), defines))
                    frame['active'] = cond_true
                    frame['seen_true'] = cond_true
            continue
        if re.match(r'^#else\b', stripped):
            if stack:
                frame = stack[-1]
                frame['active'] = frame['parent'] and not frame['seen_true']
                frame['seen_true'] = True
            continue
        if re.match(r'^#endif\b', stripped):
            if stack:
                stack.pop()
            continue
        if active():
            out.append(line)
    return '\n'.join(out)


def _iter_logical_lines(text: str):
    text = normalize_preprocessor_layout(text)
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        while line.rstrip().endswith('\\') and i + 1 < len(lines):
            line = line.rstrip()[:-1] + ' ' + lines[i + 1].strip()
            i += 1
        yield line
        i += 1


def _scan_defines_in_text(text: str, defines: dict[str, int], raw: dict[str, str]) -> bool:
    changed = False
    stack: list[dict[str, bool]] = []

    def active() -> bool:
        return all(frame['active'] for frame in stack)

    for line in _iter_logical_lines(text):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#if '):
            cond = stripped[4:].strip()
            parent_active = active()
            cond_true = bool(evaluate_c_expr(cond, defines)) if parent_active else False
            stack.append({'parent': parent_active, 'seen_true': cond_true, 'active': parent_active and cond_true})
            continue
        if stripped.startswith('#ifdef '):
            name = stripped[7:].strip()
            parent_active = active()
            cond_true = parent_active and (name in defines or name in raw)
            stack.append({'parent': parent_active, 'seen_true': cond_true, 'active': cond_true})
            continue
        if stripped.startswith('#ifndef '):
            name = stripped[8:].strip()
            parent_active = active()
            cond_true = parent_active and not (name in defines or name in raw)
            stack.append({'parent': parent_active, 'seen_true': cond_true, 'active': cond_true})
            continue
        if stripped.startswith('#elif '):
            if stack:
                frame = stack[-1]
                if not frame['parent'] or frame['seen_true']:
                    frame['active'] = False
                else:
                    cond_true = bool(evaluate_c_expr(stripped[6:].strip(), defines))
                    frame['active'] = cond_true
                    frame['seen_true'] = cond_true
            continue
        if re.match(r'^#else\b', stripped):
            if stack:
                frame = stack[-1]
                frame['active'] = frame['parent'] and not frame['seen_true']
                frame['seen_true'] = True
            continue
        if re.match(r'^#endif\b', stripped):
            if stack:
                stack.pop()
            continue
        if not active():
            continue
        m = re.match(r'^\s*#define\s+([A-Z0-9_]+)(?!\()\b\s+(.+?)\s*$', line)
        if not m:
            continue
        name, value = m.group(1), m.group(2).strip()
        raw[name] = value
        if any(ch in value for ch in ['{', '}', ';']):
            continue
        resolved = resolve_conditional_value(value, defines)
        if not resolved:
            continue
        if re.fullmatch(r'[-+]?((0x[0-9A-Fa-f]+)|\d+)', resolved):
            val = int(resolved, 0)
        elif re.fullmatch(r'[A-Z0-9_]+', resolved) and resolved in defines:
            val = defines[resolved]
        else:
            identifiers = set(re.findall(r'\b[A-Z][A-Z0-9_]*\b', resolved))
            unresolved_ids = {tok for tok in identifiers if tok not in defines and tok not in raw and tok not in {'TRUE', 'FALSE'}}
            if unresolved_ids:
                continue
            val = evaluate_c_numeric_expr(resolved, defines)
        if defines.get(name) != val:
            defines[name] = val
            changed = True
    return changed


@lru_cache(maxsize=None)
def discover_project_defines(project_dir: str) -> dict[str, int]:
    root = Path(project_dir)
    defines: dict[str, int] = {f'GEN_{i}': i for i in range(1, 10)}
    defines.update({'GEN_LATEST': 9, 'TRUE': 1, 'FALSE': 0})
    config_dirs = [root / 'include/config', root / 'src/config', root / 'include/constants']
    paths: list[Path] = []
    for cfg_dir in config_dirs:
        if cfg_dir.exists():
            paths.extend(sorted(cfg_dir.rglob('*.h')))

    raw: dict[str, str] = {}
    for _ in range(8):
        changed = False
        for path in paths:
            if _scan_defines_in_text(read_text(path), defines, raw):
                changed = True
        if not changed:
            break

    unresolved = {k: v for k, v in raw.items() if k not in defines}
    for _ in range(20):
        progress = False
        for name, value in list(unresolved.items()):
            resolved = resolve_conditional_value(value, defines)
            if resolved is None:
                continue
            if re.fullmatch(r'[-+]?((0x[0-9A-Fa-f]+)|\d+)', resolved):
                defines[name] = int(resolved, 0)
            elif re.fullmatch(r'[A-Z0-9_]+', resolved) and resolved in defines:
                defines[name] = defines[resolved]
            else:
                identifiers = set(re.findall(r'\b[A-Z][A-Z0-9_]*\b', resolved))
                unresolved_ids = {tok for tok in identifiers if tok not in defines and tok not in raw and tok not in {'TRUE', 'FALSE'}}
                if unresolved_ids:
                    continue
                defines[name] = evaluate_c_numeric_expr(resolved, defines)
            del unresolved[name]
            progress = True
        if not progress:
            break

    highest_gen = max((v for k, v in defines.items() if re.fullmatch(r'GEN_[0-9]+', k)), default=9)
    defines['GEN_LATEST'] = max(defines.get('GEN_LATEST', 0), highest_gen)
    return defines

DEFINE_NUMERIC_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+((?:0x[0-9A-Fa-f]+)|(?:\d+))\b', re.MULTILINE)


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def strip_comments(text: str) -> str:
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//.*', '', text)
    return text


def decode_c_string(text: str) -> str:
    parts = QUOTED_RE.findall(text)
    decoded = ''.join(bytes(p, 'utf-8').decode('unicode_escape') for p in parts)
    return decoded.replace('\r', '').replace('\f', ' ')


def find_matching(text: str, start_idx: int, open_ch: str = '{', close_ch: str = '}') -> int:
    depth = 0
    in_string = False
    i = start_idx
    while i < len(text):
        ch = text[i]
        prev = text[i - 1] if i else ''
        if ch == '"' and prev != '\\':
            in_string = not in_string
        elif not in_string:
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise ValueError(f'Unbalanced delimiter at index {start_idx}')


def split_top_level_csv(text: str) -> list[str]:
    items: list[str] = []
    buf: list[str] = []
    paren = brace = bracket = 0
    in_string = False
    prev = ''
    for ch in text:
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
                item = ''.join(buf).strip()
                if item:
                    items.append(item)
                buf = []
                prev = ch
                continue
        buf.append(ch)
        prev = ch
    tail = ''.join(buf).strip()
    if tail:
        items.append(tail)
    return items


def parse_named_initializers(block_text: str) -> dict[str, str]:
    body = block_text.strip()
    if body.startswith('{') and body.endswith('}'):
        body = body[1:-1]
    result: dict[str, str] = {}
    i = 0
    while i < len(body):
        m = re.search(r'\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*', body[i:])
        if not m:
            break
        field = m.group(1)
        value_start = i + m.end()
        j = value_start
        paren = brace = bracket = 0
        in_string = False
        prev = ''
        while j < len(body):
            ch = body[j]
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
        result[field] = body[value_start:j].strip()
        i = j + 1
    return result


def flatten_local_includes(path: Path, roots: Iterable[Path] | None = None, seen: set[Path] | None = None) -> str:
    roots = tuple(roots or [path.parent])
    seen = seen or set()
    path = path.resolve()
    if path in seen or not path.exists():
        return ''
    seen.add(path)
    text = read_text(path)

    def replace(match: re.Match[str]) -> str:
        rel = match.group(1)
        candidates = [path.parent / rel] + [root / rel for root in roots]
        for candidate in candidates:
            if candidate.exists():
                return flatten_local_includes(candidate, roots=roots, seen=seen)
        return match.group(0)

    return INCLUDE_RE.sub(replace, text)


def project_include_roots(project_dir: Path, *extra: str) -> list[Path]:
    roots = [
        project_dir / 'src/data/pokemon',
        project_dir / 'src/data',
        project_dir / 'src',
        project_dir / 'include',
        project_dir / 'constants',
        project_dir / 'graphics',
        project_dir,
    ]
    roots.extend(project_dir / rel for rel in extra)
    seen: set[Path] = set()
    ordered: list[Path] = []
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        ordered.append(root)
    return ordered


def read_project_text(path: Path, roots: Iterable[Path] | None = None, defines: dict[str, int] | None = None) -> str:
    text = flatten_local_includes(path, roots=roots or [path.parent])
    text = normalize_preprocessor_layout(text)
    text = preprocess_conditionals(text, defines)
    text = strip_comments(text)
    return text


@lru_cache(maxsize=None)
def build_file_index(project_dir: str) -> tuple[str, ...]:
    root = Path(project_dir)
    files: list[str] = []
    for sub in ('src', 'include', 'constants', 'data', 'graphics', 'docs'):
        target = root / sub
        if not target.exists():
            continue
        for cur, _, names in os.walk(target):
            for name in names:
                if name.endswith(('.h', '.c', '.inc', '.txt', '.png', '.webp', '.jpg', '.jpeg', '.gif', '.4bpp.lz', '.4bpp', '.pal', '.gbapal', '.lz', '.json', '.md')):
                    files.append(str(Path(cur) / name))
    return tuple(sorted(files))


def find_files(project_dir: Path, *patterns: str) -> list[Path]:
    out: list[Path] = []
    for p in build_file_index(str(project_dir)):
        path = Path(p)
        joined = str(path).replace('\\', '/')
        if any(pattern in joined for pattern in patterns):
            out.append(path)
    return out


def find_first_existing(project_dir: Path, candidates: list[str]) -> Path | None:
    for rel in candidates:
        p = project_dir / rel
        if p.exists():
            return p
    return None


def extract_string_initializer(value: str) -> str | None:
    if '"' in value:
        return decode_c_string(value)
    return None


def parse_numeric_enum(text: str, prefix: str) -> dict[str, int]:
    text = strip_comments(text)
    out: dict[str, int] = {}
    for enum_match in re.finditer(r'enum(?:\s+\w+)?\s*\{(.*?)\};', text, re.S):
        current = 0
        for item in split_top_level_csv(enum_match.group(1)):
            if not item:
                continue
            if '=' in item:
                name, value = [x.strip() for x in item.split('=', 1)]
                try:
                    current = int(value, 0)
                except Exception:
                    pass
            else:
                name = item.strip()
            if name.startswith(prefix):
                out[name] = current
            current += 1
    return out


def parse_numeric_defines(text: str, prefix: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for name, value in DEFINE_NUMERIC_RE.findall(strip_comments(text)):
        if name.startswith(prefix):
            out[name] = int(value, 0)
    return out


def parse_numeric_constants(text: str, prefix: str) -> dict[str, int]:
    out = parse_numeric_enum(text, prefix)
    out.update(parse_numeric_defines(text, prefix))
    return out
