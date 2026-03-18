from __future__ import annotations

import argparse
import difflib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ComparisonResult:
    overlap: int
    only_generated: list[str]
    only_official: list[str]
    mismatches: list[str]


def parse_ts_entry_map(text: str) -> dict[str, str]:
    marker = 'export const Pokedex'
    start = text.find(marker)
    if start == -1:
        raise ValueError('Could not find export const Pokedex in file')
    body_start = text.find('{', start)
    body_end = text.rfind('};')
    if body_start == -1 or body_end == -1 or body_end <= body_start:
        raise ValueError('Could not isolate Pokedex object body')
    body = text[body_start + 1:body_end]
    entries: dict[str, str] = {}
    i = 0
    while i < len(body):
        while i < len(body) and body[i].isspace():
            i += 1
        if i >= len(body):
            break
        m = re.match(r'([A-Za-z0-9_]+)\s*:\s*{', body[i:])
        if not m:
            i += 1
            continue
        key = m.group(1)
        entry_start = i
        entry_brace = i + m.end() - 1
        depth = 0
        in_string = False
        escape = False
        entry_end = -1
        for j in range(entry_brace, len(body)):
            ch = body[j]
            if in_string:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    entry_end = j
                    break
        if entry_end < 0:
            raise ValueError(f'Unbalanced braces while parsing entry {key}')
        k = entry_end + 1
        while k < len(body) and body[k].isspace():
            k += 1
        if k < len(body) and body[k] == ',':
            k += 1
        if k < len(body) and body[k] == '\n':
            k += 1
        entries[key] = body[entry_start:k]
        i = k
    return entries


def normalize_ignored_species_fields(block: str, ignored_fields: tuple[str, ...] = IGNORED_FIELDS) -> str:
    for field in ignored_fields:
        block = re.sub(rf'^\t\t{re.escape(field)}: .*?,\n', f'\t\t{field}: __IGNORED__,\n', block, flags=re.M)
    return block


def compare_pokedex_files(generated_path: Path, official_path: Path) -> ComparisonResult:
    generated_entries = parse_ts_entry_map(generated_path.read_text(encoding='utf-8'))
    official_entries = parse_ts_entry_map(official_path.read_text(encoding='utf-8'))
    gen_keys = set(generated_entries)
    off_keys = set(official_entries)
    overlap = sorted(gen_keys & off_keys)
    mismatches = [
        key for key in overlap
        if ordered_species_fields(generated_entries[key]) != ordered_species_fields(official_entries[key])
    ]
    return ComparisonResult(
        overlap=len(overlap),
        only_generated=sorted(gen_keys - off_keys),
        only_official=sorted(off_keys - gen_keys),
        mismatches=mismatches,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description='Compare a generated pokedex.ts against official Pokémon Showdown data/pokedex.ts')
    parser.add_argument('generated')
    parser.add_argument('official')
    parser.add_argument('--show-diff', metavar='KEY', help='Print a unified diff for a specific entry key')
    args = parser.parse_args()

    generated_path = Path(args.generated)
    official_path = Path(args.official)
    result = compare_pokedex_files(generated_path, official_path)

    print(f'overlap: {result.overlap}')
    print(f'only_in_generated: {len(result.only_generated)}')
    print(f'only_in_official: {len(result.only_official)}')
    print(f'mismatches_outside_ignored_fields: {len(result.mismatches)}')
    if result.mismatches:
        print('mismatch_keys:')
        for key in result.mismatches:
            print(f'  - {key}')

    if args.show_diff:
        gen = parse_ts_entry_map(generated_path.read_text(encoding='utf-8'))
        off = parse_ts_entry_map(official_path.read_text(encoding='utf-8'))
        key = args.show_diff
        if key not in gen or key not in off:
            raise SystemExit(f'Key {key!r} not found in both files')
        diff = difflib.unified_diff(
            ordered_species_fields(off[key]),
            ordered_species_fields(gen[key]),
            fromfile='official',
            tofile='generated',
            lineterm='',
        )
        print('\n'.join(diff))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
