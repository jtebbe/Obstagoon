from __future__ import annotations

import re


MOJIBAKE_REPLACEMENTS = {
    'PokÃ©mon': 'Pokémon',
    'PokÃ©dex': 'Pokédex',
    'Ã©': 'é',
    'â': '♀',
    'â': '♂',
}

SPECIAL_SYMBOL_NAMES = {
    'SPECIES_NIDORAN_F': 'Nidoran♀',
    'SPECIES_NIDORAN_M': 'Nidoran♂',
    'NIDORAN_F': 'Nidoran♀',
    'NIDORAN_M': 'Nidoran♂',
}


EVOLUTION_METHOD_LABELS = {
    "EVO_LEVEL": "Level up",
    "EVO_ITEM": "Use item",
    "EVO_TRADE": "Trade",
    "EVO_FRIENDSHIP": "High friendship",
    "EVO_MOVE": "Knows move",
    "EVO_MOVE_TYPE": "Knows move of type",
    "EVO_LEVEL_NIGHT": "Level up at night",
    "EVO_LEVEL_DAY": "Level up during day",
    "EVO_SPECIFIC_MAP": "Level up on map",
    "EVO_SPECIFIC_MON_IN_PARTY": "With party species",
    "EVO_CRITICAL_HITS": "Land critical hits",
    "EVO_SCRIPT_TRIGGER_DMG": "Script trigger",
}

STAT_LABELS = {
    'baseHP': 'Base HP',
    'baseAttack': 'Base Attack',
    'baseDefense': 'Base Defense',
    'baseSpeed': 'Base Speed',
    'baseSpAttack': 'Base Sp. Attack',
    'baseSpDefense': 'Base Sp. Defense',
}

PREFIX_RE = re.compile(r'^(SPECIES|MOVE|ABILITY|ITEM|TYPE|MAPSEC|MAP|EGG_GROUP|GROWTH|NATURE|BATTLE_MOVE_CATEGORY|DAMAGE_CATEGORY|MOVE_CATEGORY)_')


def slug_from_symbol(symbol: str) -> str:
    symbol = symbol or "unknown"
    symbol = re.sub(r"^(SPECIES|MOVE|ABILITY|ITEM|MAP|TYPE)_", "", symbol)
    return symbol.lower().replace("_", "-")




def fix_mojibake(text: str | None) -> str | None:
    if text is None:
        return None
    value = str(text)
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        value = value.replace(bad, good)
    return value


def format_encounter_method(method: str | None) -> str | None:
    if not method:
        return None
    method = str(method).strip()
    mapping = {
        'land': 'Land',
        'water': 'Water',
        'fishing': 'Fishing',
        'rock_smash': 'Rock Smash',
        'surf': 'Surf',
        'old_rod': 'Old Rod',
        'good_rod': 'Good Rod',
        'super_rod': 'Super Rod',
    }
    return mapping.get(method.lower(), humanize_symbol(method) or method.title())

def humanize_symbol(symbol: str | None) -> str | None:
    if not symbol:
        return None
    text = fix_mojibake(str(symbol).strip())
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'(?m)^\s*#.*$', '', text)
    text = text.replace('(u16)', '').replace('&', '').strip()
    text = text.rstrip(')}],; ').strip()
    if text in SPECIAL_SYMBOL_NAMES:
        return SPECIAL_SYMBOL_NAMES[text]
    text = PREFIX_RE.sub('', text)
    text = text.replace('_', ' ').strip().title()
    text = text.replace('Sp ', 'Sp. ')
    text = fix_mojibake(text)
    return text or None


def pretty_source_label(source: str | None) -> str | None:
    if not source:
        return None
    mapping = {
        'GENERATED_HEADER': 'Teachable',
        'TEACHABLE_JSON': 'Teachable',
        'UNIVERSAL': 'Universal',
        'TMHM': 'TM/HM',
        'TUTOR': 'Tutor',
    }
    return mapping.get(source, humanize_symbol(source) or source.title())


def humanize_stat_key(key: str | None) -> str | None:
    if not key:
        return None
    return STAT_LABELS.get(key, humanize_symbol(key) or key)


def infer_form_name(species_id: str, base_species: str | None) -> str | None:
    if not base_species or base_species == species_id:
        return None
    head = base_species.replace("SPECIES_", "") + "_"
    remainder = species_id.replace("SPECIES_", "")
    if remainder.startswith(head):
        remainder = remainder[len(head):]
    pretty = humanize_symbol(remainder) if remainder else None
    return pretty or (remainder.replace("_", " ").title() if remainder else None)


def evolution_label(method: str, param: str | None) -> str:
    label = EVOLUTION_METHOD_LABELS.get(method, method.replace("EVO_", "").replace("_", " ").title())
    if param and param not in {"0", "ITEM_NONE", "MOVE_NONE", "SPECIES_NONE", "TYPE_NONE"}:
        return f"{label}: {humanize_symbol(param) or param}"
    return label


def normalize_move_category(value: str | None) -> str | None:
    if not value:
        return None
    text = humanize_symbol(value) or fix_mojibake(str(value).strip())
    if not text:
        return None
    mapping = {
        'Damage Category Physical': 'Physical',
        'Damage Category Special': 'Special',
        'Damage Category Status': 'Status',
        'Battle Move Category Physical': 'Physical',
        'Battle Move Category Special': 'Special',
        'Battle Move Category Status': 'Status',
        'Move Category Physical': 'Physical',
        'Move Category Special': 'Special',
        'Move Category Status': 'Status',
    }
    return mapping.get(text, text)


def type_badge_class(type_name: str | None) -> str:
    if not type_name:
        return 'type-badge type-unknown'
    slug = slug_from_symbol(type_name).replace('_', '-').lower()
    return f'type-badge type-{slug}'


def unique_preserve_order(values: list[str | None]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out
