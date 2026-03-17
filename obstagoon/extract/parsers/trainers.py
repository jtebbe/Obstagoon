from __future__ import annotations

import re
from pathlib import Path

from ..c_utils import strip_comments
from ...normalize import fix_mojibake, humanize_symbol, slug_from_symbol

TRAINER_SECTION_RE = re.compile(r'^===\s*(TRAINER_[A-Z0-9_]+)\s*===\s*$', re.MULTILINE)
TRAINER_LINE_RE = re.compile(r'^([^:]+):\s*(.*)$')
STAT_SPLIT_RE = re.compile(r'\s*/\s*')
POKEMON_HEADER_RE = re.compile(
    r'^(?:(?P<nickname>.+?)\s*\((?P<species_inner>SPECIES_[A-Z0-9_]+)\)|(?P<species_plain>SPECIES_[A-Z0-9_]+|[^@()]+?))'
    r'(?:\s*\((?P<gender>[MF])\))?'
    r'(?:\s*@\s*(?P<item>.+))?\s*$'
)

KNOWN_TRAINER_FIELDS = {
    'Name', 'Pic', 'Class', 'Gender', 'Music', 'Items', 'Battle Type', 'Double Battle', 'AI',
    'Mugshot', 'Starting Status', 'Party Pool', 'Party Size', 'Pool', 'Pool Size', 'Pool Rules',
}


def title_case_words(text: str | None) -> str | None:
    if not text:
        return text
    value = fix_mojibake(str(text).strip()) or ''
    if not value:
        return None

    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        return token[:1].upper() + token[1:].lower()

    return re.sub(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", repl, value)


def humanize_map_dir_name(name: str) -> str:
    text = str(name or '').replace('_', ' ')
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    return re.sub(r'\s+', ' ', text).strip() or name


def normalize_trainer_pic_key(value: str | None) -> str:
    text = fix_mojibake(str(value or '').strip()) or ''
    text = Path(text.replace('\\', '/')).stem
    text = text.replace('TRAINER_PIC_', '').replace('trainer_pic_', '')
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', text)
    text = text.replace('-', '_').replace(' ', '_')
    text = re.sub(r'[^A-Za-z0-9_]+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text.lower()


def _split_sections(text: str) -> list[tuple[str, str]]:
    matches = list(TRAINER_SECTION_RE.finditer(text))
    out: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        out.append((match.group(1), text[start:end].strip()))
    return out


def _parse_trainer_metadata(lines: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in lines:
        m = TRAINER_LINE_RE.match(line)
        if not m:
            continue
        key = title_case_words(m.group(1).strip()) or m.group(1).strip()
        result[key] = m.group(2).strip()
    return result




def _resolve_battle_type(metadata: dict[str, str]) -> str | None:
    explicit = metadata.get('Battle Type')
    if explicit:
        return explicit.strip() or None
    double_battle = metadata.get('Double Battle')
    if double_battle:
        lowered = double_battle.strip().lower()
        if lowered == 'yes':
            return 'Doubles'
        if lowered == 'no':
            return 'Singles'
    return None

def _parse_stat_block(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in STAT_SPLIT_RE.split(value.strip()):
        m = re.match(r'^(\d+)\s+([A-Za-z]+)$', part.strip())
        if m:
            result[m.group(2)] = m.group(1)
    return result


def _parse_pokemon_block(block: str) -> dict | None:
    lines = [line.rstrip() for line in block.splitlines() if line.strip()]
    if not lines:
        return None
    m = POKEMON_HEADER_RE.match(lines[0].strip())
    if not m:
        return None
    species_token = (m.group('species_inner') or m.group('species_plain') or '').strip()
    result: dict = {
        'species_token': species_token,
        'species_symbol': species_token if species_token.startswith('SPECIES_') else None,
        'species_name': humanize_symbol(species_token) if species_token.startswith('SPECIES_') else title_case_words(species_token),
        'nickname': (m.group('nickname') or '').strip() or None,
        'gender': m.group('gender'),
        'held_item': (m.group('item') or '').strip() or None,
        'level': None,
        'ability': None,
        'tera_type': None,
        'evs': {},
        'ivs': {},
        'moves': [],
        'raw_fields': {},
    }
    if result['held_item']:
        result['held_item'] = humanize_symbol(result['held_item']) or title_case_words(result['held_item']) or result['held_item']
    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith('- '):
            move = stripped[2:].strip()
            result['moves'].append(humanize_symbol(move) or title_case_words(move) or move)
            continue
        m_field = TRAINER_LINE_RE.match(stripped)
        if not m_field:
            continue
        key = title_case_words(m_field.group(1).strip()) or m_field.group(1).strip()
        value = m_field.group(2).strip()
        result['raw_fields'][key] = value
        if key == 'Level':
            result['level'] = value
        elif key == 'Ability':
            result['ability'] = humanize_symbol(value) or title_case_words(value) or value
        elif key == 'Tera Type':
            result['tera_type'] = humanize_symbol(value) or title_case_words(value) or value
        elif key == 'Evs':
            result['evs'] = _parse_stat_block(value)
        elif key == 'Ivs':
            result['ivs'] = _parse_stat_block(value)
        elif key in {'Held Item', 'Item'} and not result['held_item']:
            result['held_item'] = humanize_symbol(value) or title_case_words(value) or value
    return result


def build_trainer_picture_index(project_dir: Path) -> dict[str, str]:
    root = project_dir / 'graphics/trainers/front_pics'
    index: dict[str, str] = {}
    if not root.exists():
        return index
    for path in root.rglob('*'):
        if path.is_file():
            rel = path.relative_to(project_dir).as_posix()
            key = normalize_trainer_pic_key(path.name)
            if key:
                index[key] = rel
    return index


def resolve_trainer_picture_path(value: str | None, picture_index: dict[str, str]) -> str | None:
    if not value:
        return None
    raw = str(value).strip().replace('\\', '/')
    if '/' in raw and '.' in Path(raw).name:
        return raw
    candidates = [raw]
    if raw.startswith('TRAINER_PIC_'):
        candidates.append(raw.replace('TRAINER_PIC_', '', 1))
    human = humanize_symbol(raw)
    if human:
        candidates.append(human)
    for candidate in candidates:
        key = normalize_trainer_pic_key(candidate)
        if key in picture_index:
            return picture_index[key]
    return None


def build_trainer_location_index(project_dir: Path) -> dict[str, str]:
    maps_dir = project_dir / 'data/maps'
    index: dict[str, str] = {}
    if not maps_dir.exists():
        return index
    for script in maps_dir.rglob('scripts.inc'):
        try:
            text = strip_comments(script.read_text(encoding='utf-8', errors='ignore'))
        except Exception:
            continue
        symbols = set(re.findall(r'\bTRAINER_[A-Z0-9_]+\b', text))
        if not symbols:
            continue
        location = humanize_map_dir_name(script.parent.name)
        for symbol in symbols:
            index.setdefault(symbol, location)
    return index


def parse_trainers(project_dir: Path, defines: dict[str, int] | None = None) -> list[dict]:
    trainers_path = project_dir / 'src/data/trainers.party'
    if not trainers_path.exists():
        return []
    text = strip_comments(trainers_path.read_text(encoding='utf-8', errors='ignore'))
    picture_index = build_trainer_picture_index(project_dir)
    location_index = build_trainer_location_index(project_dir)
    trainers: list[dict] = []
    for trainer_id, body in _split_sections(text):
        chunks = re.split(r'\n\s*\n+', body.strip()) if body.strip() else []
        metadata_lines: list[str] = []
        pokemon_blocks: list[str] = []
        seen_pokemon = False
        for chunk in chunks:
            lines = [line.strip() for line in chunk.splitlines() if line.strip()]
            if not lines:
                continue
            first_match = TRAINER_LINE_RE.match(lines[0])
            if not seen_pokemon and first_match:
                key = title_case_words(first_match.group(1).strip()) or first_match.group(1).strip()
                if key in KNOWN_TRAINER_FIELDS:
                    metadata_lines.extend(lines)
                    continue
            seen_pokemon = True
            pokemon_blocks.append(chunk)
        metadata = _parse_trainer_metadata(metadata_lines)
        if trainer_id not in location_index:
            continue
        pokemon = [entry for entry in (_parse_pokemon_block(block) for block in pokemon_blocks) if entry]
        party_pool_value = metadata.get('Party Pool') or metadata.get('Pool')
        party_size_value = metadata.get('Party Size') or metadata.get('Pool Size')
        has_party_pool = False
        if party_pool_value:
            lowered = party_pool_value.strip().lower()
            has_party_pool = lowered in {'yes', 'true', '1', 'pool', 'random'} or lowered.isdigit()
            if lowered.isdigit() and not party_size_value:
                party_size_value = party_pool_value.strip()
        if has_party_pool and not party_size_value and pokemon:
            party_size_value = str(min(len(pokemon), 6))
        trainers.append({
            'trainer_id': trainer_id,
            'name': title_case_words(metadata.get('Name')) or humanize_symbol(trainer_id) or trainer_id,
            'class_name': title_case_words(metadata.get('Class')),
            'pic_path': resolve_trainer_picture_path(metadata.get('Pic'), picture_index),
            'location': location_index.get(trainer_id),
            'battle_type': _resolve_battle_type(metadata),
            'has_party_pool': has_party_pool,
            'party_size': party_size_value,
            'pool_rules': title_case_words(metadata.get('Pool Rules')) or metadata.get('Pool Rules'),
            'pokemon': pokemon,
            'raw_metadata': metadata,
        })
    return trainers
