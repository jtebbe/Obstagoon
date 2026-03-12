from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ..c_utils import build_file_index

RASTER_SUFFIXES = ('.png', '.webp', '.jpg', '.jpeg', '.gif')
PALETTE_SUFFIXES = ('.pal',)
TILE_SUFFIXES = ('.4bpp.lz', '.4bpp', '.lz')
ASSET_SUFFIXES = RASTER_SUFFIXES + PALETTE_SUFFIXES + TILE_SUFFIXES


GENERIC_PATH_TOKENS = {
    'graphics', 'pokemon', 'front', 'back', 'icon', 'icons', 'palette', 'palettes', 'shiny', 'female', 'male',
    'normal', 'species', 'form', 'forms', 'anim', 'animation', 'footprint', 'mini', 'small', 'large', 'gmax', 'world',
}

FORM_HINT_TOKENS = {
    'gmax', 'mega', 'megax', 'megay', 'alola', 'galar', 'hisui', 'paldea', 'origin', 'therian', 'sky', 'ash',
    'totem', 'eternamax', 'white', 'black', 'sunny', 'rainy', 'snowy', 'attack', 'defense', 'speed', 'complete',
    '10', '10percent', '50', '50percent', '100', 'unbound', 'school', 'solo', 'busted', 'disguised', 'crowned',
    'hero', 'blade', 'shield', 'ice', 'shadow', 'dusk', 'dawn', 'midday', 'midnight', 'starter', 'lowkey', 'amped',
    'small', 'large', 'super', 'ultra', 'ruby', 'vanilla', 'mint', 'lemon', 'matcha', 'salted', 'cream', 'swirl',
    'heart', 'star', 'berry', 'clover', 'flower', 'ribbon', 'love', 'cosplay', 'phd', 'libre', 'belle', 'pop', 'rock', 'star',
}

def _species_specific_tokens(species_id: str) -> set[str]:
    slug = _species_slug(species_id)
    return {bit for bit in re.split(r'[^a-z0-9]+', slug) if bit}


def _extra_form_penalty(path_tokens: set[str], species_id: str) -> int:
    species_tokens = _species_specific_tokens(species_id)
    extras = {tok for tok in path_tokens if tok not in species_tokens and tok in FORM_HINT_TOKENS}
    if not extras:
        return 0
    if species_tokens & extras:
        return 0
    return -18 * len(extras)


def _segment_tokens(path: str) -> list[set[str]]:
    parts = [part for part in path.replace('\\', '/').lower().split('/') if part]
    return [_tokenize_pathish(part) for part in parts]




def _graphics_species_dir_bonus(rel: str, species_id: str) -> int:
    species_tokens = _species_specific_tokens(species_id)
    parts = [part for part in rel.replace('\\', '/').lower().split('/') if part]
    if len(parts) >= 3 and parts[0] == 'graphics' and parts[1] == 'pokemon':
        seg_tokens = _tokenize_pathish(parts[2])
        if seg_tokens == species_tokens:
            return 24
        if species_tokens and species_tokens.issubset(seg_tokens):
            return 10
    return 0
def _exact_species_segment_bonus(rel: str, species_id: str) -> int:
    species_tokens = _species_specific_tokens(species_id)
    if not species_tokens:
        return 0
    best = 0
    for seg_tokens in _segment_tokens(rel):
        if not seg_tokens:
            continue
        if seg_tokens == species_tokens:
            best = max(best, 24)
        elif species_tokens.issubset(seg_tokens):
            best = max(best, 12)
    return best


def _path_kind_bonus(path: Path, kind: str) -> int:
    rel = str(path).replace('\\', '/').lower()
    stem = path.name.lower()
    score = 0
    if kind.startswith('front'):
        if '/front/' in rel or 'front' in stem:
            score += 18
        if '/back/' in rel or 'back' in stem:
            score -= 28
        if '/icon' in rel or 'icon' in stem:
            score -= 24
        if '/world/' in rel or 'overworld' in stem or '/overworld' in rel:
            score -= 90
        if 'tera' in rel or 'teal' in rel:
            score -= 18
        if 'anim_front' in stem:
            score += 34
        if stem == 'front':
            score += 18
        if 'pal' in stem or '/palette' in rel:
            score -= 32
    elif kind.startswith('back'):
        if '/back/' in rel or 'back' in stem:
            score += 24
        if '/front/' in rel or 'front' in stem:
            score -= 30
        if '/icon' in rel or 'icon' in stem:
            score -= 24
        if 'pal' in stem or '/palette' in rel:
            score -= 34
    elif 'palette' in kind.lower():
        if '/palette' in rel or 'pal' in stem:
            score += 18
        if '/front/' in rel or 'front' in stem or '/back/' in rel or 'back' in stem or '/icon' in rel or 'icon' in stem:
            score -= 26
    elif kind.startswith('icon'):
        if '/icon' in rel or 'icon' in stem:
            score += 18
        if '/front/' in rel or 'front' in stem or '/back/' in rel or 'back' in stem:
            score -= 24
        if 'pal' in stem or '/palette' in rel:
            score -= 24
    if 'shiny' in rel and 'shiny' not in kind.lower():
        score -= 28
    if 'female' in rel and 'female' not in kind.lower():
        score -= 8
    return score

KIND_RULES = {
    'frontPic': {'must': ('front',), 'forbid': ('back', 'palette', 'icon', 'shiny'), 'suffixes': RASTER_SUFFIXES + TILE_SUFFIXES},
    'frontPicFemale': {'must': ('front', 'female'), 'forbid': ('back', 'palette', 'icon', 'shiny'), 'suffixes': RASTER_SUFFIXES + TILE_SUFFIXES},
    'backPic': {'must': ('back',), 'forbid': ('front', 'palette', 'icon', 'shiny'), 'suffixes': RASTER_SUFFIXES + TILE_SUFFIXES},
    'backPicFemale': {'must': ('back', 'female'), 'forbid': ('front', 'palette', 'icon', 'shiny'), 'suffixes': RASTER_SUFFIXES + TILE_SUFFIXES},
    'palette': {'must': ('palette',), 'forbid': ('front', 'back', 'icon', 'female', 'shiny'), 'suffixes': PALETTE_SUFFIXES},
    'paletteFemale': {'must': ('palette', 'female'), 'forbid': ('front', 'back', 'icon', 'shiny'), 'suffixes': PALETTE_SUFFIXES},
    'shinyPalette': {'must': ('palette', 'shiny'), 'forbid': ('front', 'back', 'icon', 'female'), 'suffixes': PALETTE_SUFFIXES},
    'shinyPaletteFemale': {'must': ('palette', 'shiny', 'female'), 'forbid': ('front', 'back', 'icon'), 'suffixes': PALETTE_SUFFIXES},
    'iconSprite': {'must': ('icon',), 'forbid': ('front', 'back', 'palette'), 'suffixes': RASTER_SUFFIXES + TILE_SUFFIXES},
    'iconSpriteFemale': {'must': ('icon', 'female'), 'forbid': ('front', 'back', 'palette'), 'suffixes': RASTER_SUFFIXES + TILE_SUFFIXES},
}


@dataclass(slots=True)
class SpriteIndex:
    files: list[Path]
    rel_lookup: dict[str, Path]
    name_lookup: dict[str, list[Path]]
    norm_lookup: dict[str, list[Path]]
    token_lookup: dict[str, list[Path]]
    dir_lookup: dict[str, list[Path]]


def _normalize_token(value: str) -> str:
    value = re.sub(r'\([^)]*\)', ' ', value)
    value = value.replace('&', ' ').replace('*', ' ')
    value = value.replace('[', ' ').replace(']', ' ')
    value = value.replace('"', ' ').replace("'", ' ')
    value = value.replace('/', ' ').replace('\\', ' ')
    value = re.sub(r'\bconst\b|\bu8\b|\bu16\b|\bu32\b', ' ', value)
    value = re.sub(r'[^a-zA-Z0-9]+', '', value).lower()
    return value


def _tokenize_pathish(value: str) -> set[str]:
    value = value.replace('\\', '/')
    value = re.sub(r'([a-z])([A-Z])', r'\1_\2', value)
    value = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', value)
    value = re.sub(r'([a-zA-Z])(\d)', r'\1_\2', value)
    value = re.sub(r'(\d)([a-zA-Z])', r'\1_\2', value)
    lowered = value.lower()
    parts = re.split(r'[^a-z0-9]+', lowered)
    tokens = {p for p in parts if p}
    # normalize common shorthand
    if 'percent' in tokens:
        if '10' in tokens:
            tokens.add('10percent')
        if '50' in tokens:
            tokens.add('50percent')
    if 'male' in tokens:
        tokens.add('m')
    if 'female' in tokens:
        tokens.add('f')
    return tokens


def _species_slug(species_id: str) -> str:
    return species_id.replace('SPECIES_', '').lower()


def _split_slug_tokens(value: str) -> list[str]:
    value = value.replace('\\', '/')
    value = re.sub(r'([a-z])([A-Z])', r'\1_\2', value)
    value = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', value)
    value = re.sub(r'([a-zA-Z])(\d)', r'\1_\2', value)
    value = re.sub(r'(\d)([a-zA-Z])', r'\1_\2', value)
    return [bit for bit in re.split(r'[^a-z0-9]+', value.lower()) if bit]


def _strip_form_suffix_tokens(tokens: list[str]) -> list[str]:
    trimmed = list(tokens)
    while trimmed and trimmed[-1] in {'pattern', 'form', 'mode'}:
        trimmed.pop()
    return trimmed


def _form_token_variants(tokens: list[str]) -> list[list[str]]:
    variants: list[list[str]] = []
    for candidate in (list(tokens), _strip_form_suffix_tokens(tokens), [t for t in tokens if t not in {'pattern', 'form', 'mode'}]):
        if candidate and candidate not in variants:
            variants.append(candidate)
    return variants


def _form_slug_aliases(tokens: list[str]) -> list[str]:
    if not tokens:
        return []
    candidates: list[str] = []

    def add(parts: list[str] | tuple[str, ...] | str) -> None:
        if isinstance(parts, str):
            slug = parts
        else:
            slug = '_'.join(parts)
        if slug and slug not in candidates:
            candidates.append(slug)

    add(tokens)
    if len(tokens) == 1:
        only = tokens[0]
        if only in {'10', '50'}:
            add([only, 'percent'])
        if only == '10percent':
            add(['10', 'percent'])
        if only == '50percent':
            add(['50', 'percent'])
        if only == 'male':
            add('m')
        if only == 'female':
            add('f')
        if only == 'pokeball':
            add('poke_ball')
        if only == 'm':
            add('male')
        if only == 'f':
            add('female')
    if len(tokens) == 2 and tokens[1] == 'percent' and tokens[0] in {'10', '50'}:
        add(f"{tokens[0]}percent")
    if tokens == ['poke', 'ball']:
        add('pokeball')
        add('poke_ball')
    if tokens == ['icy', 'snow']:
        add('icy_snow')
        add('icysnow')

    # Upstream form layouts sometimes keep additional qualifiers on the species symbol
    # but store the actual art under a shared percent-form directory.
    # Example: SPECIES_ZYGARDE_10_POWER_CONSTRUCT -> graphics/pokemon/zygarde/10_percent/anim_front.png
    if tokens[0] in {'10', '50', '10percent', '50percent'}:
        percent_slug = '10_percent' if tokens[0] in {'10', '10percent'} else '50_percent'
        if percent_slug not in candidates:
            candidates.append(percent_slug)
        compact_percent_slug = percent_slug.replace('_', '')
        if compact_percent_slug not in candidates:
            candidates.append(compact_percent_slug)
    return candidates




def _form_dir_path_aliases(tokens: list[str]) -> list[str]:
    if not tokens:
        return []

    candidates: list[str] = []

    def add(path: str) -> None:
        if path and path not in candidates:
            candidates.append(path)

    def walk(start: int, parts: list[str]) -> None:
        if start >= len(tokens):
            add('/'.join(parts))
            return
        for end in range(start + 1, len(tokens) + 1):
            segment = tokens[start:end]
            aliases = _form_slug_aliases(segment) or ['_'.join(segment)]
            for alias in aliases:
                walk(end, [*parts, alias])

    walk(0, [])
    return candidates

def _longest_existing_species_prefix(index: SpriteIndex, slug: str) -> tuple[str | None, list[str]]:
    tokens = _split_slug_tokens(slug)
    if not tokens:
        return None, []
    best_prefix: str | None = None
    best_remainder: list[str] = []
    for i in range(len(tokens), 0, -1):
        prefix = '_'.join(tokens[:i])
        rel = f'graphics/pokemon/{prefix}'
        if rel in index.dir_lookup:
            best_prefix = prefix
            best_remainder = tokens[i:]
            break
    return best_prefix, best_remainder


def _raw_token_slug_variants(token: str) -> list[str]:
    variants: list[str] = []
    for cand in _candidate_tokens(token):
        toks = _split_slug_tokens(cand.replace('/', '_'))
        if toks:
            variants.append('_'.join(toks))
    deduped: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        if variant not in seen:
            seen.add(variant)
            deduped.append(variant)
    return deduped


def _exact_dir_candidates(index: SpriteIndex, species_id: str, token: str) -> list[str]:
    candidates: list[str] = []
    fallback_dirs: list[str] = []

    def add(rel_dir: str | None, *, fallback: bool = False) -> None:
        if not rel_dir or rel_dir not in index.dir_lookup:
            return
        target = fallback_dirs if fallback else candidates
        if rel_dir not in candidates and rel_dir not in fallback_dirs:
            target.append(rel_dir)

    slug = _species_slug(species_id)

    prefix, remainder = _longest_existing_species_prefix(index, slug)
    if prefix:
        for remainder_variant in _form_token_variants(remainder):
            if remainder_variant:
                for form_path in _form_dir_path_aliases(remainder_variant):
                    add(f'graphics/pokemon/{prefix}/{form_path}')
                for form_slug in _form_slug_aliases(remainder_variant):
                    add(f'graphics/pokemon/{prefix}_{form_slug}')
                    add(f'graphics/pokemon/{prefix}-{form_slug}')
                for i in range(1, len(remainder_variant)):
                    prefix_variant = remainder_variant[:i]
                    for form_path in _form_dir_path_aliases(prefix_variant):
                        add(f'graphics/pokemon/{prefix}/{form_path}', fallback=True)
                    for form_slug in _form_slug_aliases(prefix_variant):
                        add(f'graphics/pokemon/{prefix}_{form_slug}', fallback=True)
                        add(f'graphics/pokemon/{prefix}-{form_slug}', fallback=True)
        add(f'graphics/pokemon/{prefix}', fallback=True)

    for raw_slug in _raw_token_slug_variants(token):
        add(f'graphics/pokemon/{raw_slug}')
        raw_prefix, raw_remainder = _longest_existing_species_prefix(index, raw_slug)
        if raw_prefix:
            for raw_variant in _form_token_variants(raw_remainder):
                if raw_variant:
                    for form_path in _form_dir_path_aliases(raw_variant):
                        add(f'graphics/pokemon/{raw_prefix}/{form_path}')
                    for form_slug in _form_slug_aliases(raw_variant):
                        add(f'graphics/pokemon/{raw_prefix}_{form_slug}')
                        add(f'graphics/pokemon/{raw_prefix}-{form_slug}')
                    for i in range(1, len(raw_variant)):
                        prefix_variant = raw_variant[:i]
                        for form_path in _form_dir_path_aliases(prefix_variant):
                            add(f'graphics/pokemon/{raw_prefix}/{form_path}', fallback=True)
                        for form_slug in _form_slug_aliases(prefix_variant):
                            add(f'graphics/pokemon/{raw_prefix}_{form_slug}', fallback=True)
                            add(f'graphics/pokemon/{raw_prefix}-{form_slug}', fallback=True)
            add(f'graphics/pokemon/{raw_prefix}', fallback=True)

    add(f'graphics/pokemon/{slug}', fallback=True)
    return candidates + fallback_dirs


def _explicit_kind_candidates(candidates: list[Path], kind: str) -> list[Path]:
    if not candidates:
        return []
    wanted = None
    if kind.startswith('front'):
        wanted = 'front'
    elif kind.startswith('back'):
        wanted = 'back'
    elif kind.startswith('icon'):
        wanted = 'icon'
    elif 'palette' in kind.lower():
        wanted = 'pal'
    if wanted is None:
        return candidates

    filtered: list[Path] = []
    for path in candidates:
        rel = str(path).replace('\\', '/').lower()
        stem = path.stem.lower()
        toks = _tokenize_pathish(rel)
        if wanted == 'front':
            if 'front' in toks or 'anim_front' in stem or stem == 'front':
                filtered.append(path)
        elif wanted == 'back':
            if 'back' in toks or stem == 'back':
                filtered.append(path)
        elif wanted == 'icon':
            if 'icon' in toks or stem in {'icon', 'iconsprite'}:
                filtered.append(path)
        elif wanted == 'pal':
            if 'pal' in stem or 'palette' in toks:
                filtered.append(path)
    return filtered


def _resolve_from_exact_dirs(project_dir: Path, index: SpriteIndex, species_id: str, kind: str, raw_token: str) -> tuple[str | None, list[dict[str, str]]]:
    best_ranked: list[dict[str, str]] = []
    for rel_dir in _exact_dir_candidates(index, species_id, raw_token):
        candidates = index.dir_lookup.get(rel_dir, [])
        strict_candidates = _explicit_kind_candidates(candidates, kind)
        if strict_candidates:
            candidates = strict_candidates
        resolved, ranked = _resolve_from_candidates(project_dir, candidates, species_id, kind, raw_token, min_score=10)
        if resolved:
            return resolved, ranked
        if ranked and not best_ranked:
            best_ranked = ranked
    return None, best_ranked


def _candidate_tokens(token: str) -> list[str]:
    stripped = token.strip().strip('{}').strip()
    if not stripped:
        return []
    bare = stripped.strip('"').replace('&', '').strip()
    candidates = [bare]
    if '/' in bare:
        candidates.append(Path(bare).name)
    for prefix in ('gMonFrontPic_', 'gMonBackPic_', 'gMonPalette_', 'gMonShinyPalette_', 'gMonIcon_', 's'):
        if bare.startswith(prefix):
            candidates.append(bare[len(prefix):])
    deduped: list[str] = []
    seen: set[str] = set()
    for cand in candidates:
        if cand not in seen:
            seen.add(cand)
            deduped.append(cand)
    return deduped


def _path_suffix_matches(path: Path, kind: str) -> bool:
    lowered = path.name.lower()
    allowed = KIND_RULES.get(kind, {}).get('suffixes', ASSET_SUFFIXES)
    return any(lowered.endswith(sfx) for sfx in allowed)


def _kind_score(rel: str, kind: str) -> int:
    tokens = _tokenize_pathish(rel)
    rules = KIND_RULES.get(kind, {})
    score = 0
    must = rules.get('must', ())
    forbid = rules.get('forbid', ())
    missing = [token for token in must if token not in tokens]
    if must:
        score += 12 if not missing else -6 * len(missing)
    if 'palette' in kind.lower() and any(rel.endswith(sfx) for sfx in PALETTE_SUFFIXES):
        if 'front' not in tokens and 'back' not in tokens and 'icon' not in tokens:
            score += 8
        if 'shiny' in kind.lower() and 'shiny' in tokens:
            score += 4
        if 'female' in kind.lower() and 'female' in tokens:
            score += 4
    for token in forbid:
        if token in tokens:
            score -= 9
    return score


def _rank_candidate(project_dir: Path, path: Path, species_id: str, kind: str, raw_token: str) -> tuple[int, int, str]:
    rel = str(path.relative_to(project_dir)).replace('\\', '/')
    rel_lower = rel.lower()
    score = 0
    if '/graphics/pokemon/' in rel_lower:
        score += 8
    score += _path_kind_bonus(path, kind)
    if _path_suffix_matches(path, kind):
        score += 10
    else:
        score -= 20
    score += _kind_score(rel_lower, kind)
    slug = _species_slug(species_id)
    path_tokens = _tokenize_pathish(rel_lower)
    slug_bits = [b for b in slug.split('_') if b]
    if slug in rel_lower or all(bit in path_tokens for bit in slug_bits):
        score += 10
    score += _graphics_species_dir_bonus(rel_lower, species_id)
    score += _exact_species_segment_bonus(rel_lower, species_id)
    score += _extra_form_penalty(path_tokens, species_id)
    if raw_token:
        raw_norm = _normalize_token(raw_token)
        rel_norm = _normalize_token(rel_lower)
        name_norm = _normalize_token(path.stem)
        if raw_norm and raw_norm == rel_norm:
            score += 14
        elif raw_norm and raw_norm == name_norm:
            score += 12
        elif raw_norm and raw_norm in rel_norm:
            score += 8
    basename = path.stem.lower()
    if kind.startswith('front') and basename == 'front':
        score += 16
    elif kind.startswith('back') and basename == 'back':
        score += 18
    elif kind.startswith('icon') and basename in {'icon', 'iconsprite'}:
        score += 16
    if path.suffix.lower() in RASTER_SUFFIXES and kind in {'frontPic', 'frontPicFemale', 'backPic', 'backPicFemale', 'iconSprite', 'iconSpriteFemale'}:
        score += 2
    return (score, -len(rel), rel)


def _resolve_from_candidates(project_dir: Path, candidates: list[Path], species_id: str, kind: str, raw_token: str, min_score: int = 0) -> tuple[str | None, list[dict[str, str]]]:
    if not candidates:
        return None, []
    ranked = sorted(candidates, key=lambda p: _rank_candidate(project_dir, p, species_id, kind, raw_token), reverse=True)
    ranked_info = [
        {
            'path': str(path.relative_to(project_dir)).replace('\\', '/'),
            'score': str(_rank_candidate(project_dir, path, species_id, kind, raw_token)[0]),
        }
        for path in ranked[:5]
    ]
    best = ranked[0]
    best_score = _rank_candidate(project_dir, best, species_id, kind, raw_token)[0]
    if best_score < min_score:
        return None, ranked_info
    return str(best.relative_to(project_dir)).replace('\\', '/'), ranked_info


def _build_lookup_index(project_dir: Path, files: list[Path], progress=None) -> SpriteIndex:
    if progress and getattr(progress, 'enabled', False):
        progress.info(f'Building sprite lookup tables from {len(files)} files...')
    rel_lookup: dict[str, Path] = {}
    name_lookup: dict[str, list[Path]] = {}
    norm_lookup: dict[str, list[Path]] = {}
    token_lookup: dict[str, list[Path]] = {}
    dir_lookup: dict[str, list[Path]] = {}
    iterator = files
    total = len(files)
    if progress is not None and total:
        iterator = progress.iter(files, 'sprite index', total=total, every=max(1, total // 100), detail=lambda p: p.name)
    for p in iterator:
        rel = str(p.relative_to(project_dir)).replace('\\', '/')
        rel_lookup[rel] = p
        rel_lower = rel.lower()
        dir_lookup.setdefault(str(Path(rel_lower).parent).replace('\\', '/'), []).append(p)
        name_lookup.setdefault(p.name.lower(), []).append(p)
        for norm in (_normalize_token(rel), _normalize_token(p.stem)):
            if norm:
                norm_lookup.setdefault(norm, []).append(p)
        for token in _tokenize_pathish(rel_lower):
            token_lookup.setdefault(token, []).append(p)
    if progress and getattr(progress, 'enabled', False):
        progress.info('Sprite lookup tables ready')
    return SpriteIndex(files=files, rel_lookup=rel_lookup, name_lookup=name_lookup, norm_lookup=norm_lookup, token_lookup=token_lookup, dir_lookup=dir_lookup)


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _resolve_path(project_dir: Path, index: SpriteIndex, species_id: str, kind: str, token: str) -> tuple[str | None, list[dict[str, str]]]:
    if kind in {'frontPic', 'frontPicFemale', 'backPic', 'backPicFemale', 'palette', 'paletteFemale', 'shinyPalette', 'shinyPaletteFemale'}:
        resolved, ranked = _resolve_from_exact_dirs(project_dir, index, species_id, kind, token)
        if resolved:
            return resolved, ranked

    for cand in _candidate_tokens(token):
        raw_path = cand.strip('"')
        maybe = project_dir / raw_path
        if maybe.exists() and maybe.is_file() and _path_suffix_matches(maybe, kind):
            rel = str(maybe.relative_to(project_dir)).replace('\\', '/')
            return rel, [{'path': rel, 'score': 'direct'}]
        rel = raw_path.replace('\\', '/')
        if rel in index.rel_lookup and _path_suffix_matches(index.rel_lookup[rel], kind):
            return rel, [{'path': rel, 'score': 'direct'}]
        if _normalize_token(raw_path) == _normalize_token(_species_slug(species_id)):
            continue
        token_candidates: list[Path] = []
        base = Path(raw_path).name.lower()
        if base in index.name_lookup:
            token_candidates.extend(index.name_lookup[base])
        norm = _normalize_token(raw_path)
        if norm in index.norm_lookup:
            token_candidates.extend(index.norm_lookup[norm])
        for tok in _tokenize_pathish(raw_path.lower()):
            token_candidates.extend(index.token_lookup.get(tok, []))
        for suffix in ASSET_SUFFIXES:
            token_candidates.extend(index.name_lookup.get(f'{Path(base).stem}{suffix}'.lower(), []))
        token_candidates = _dedupe_paths(token_candidates)
        resolved, ranked = _resolve_from_candidates(project_dir, token_candidates, species_id, kind, raw_path, min_score=16)
        if resolved:
            return resolved, ranked

    slug = _species_slug(species_id)
    species_candidates: list[Path] = []
    for bit in [bit for bit in re.split(r'[^a-z0-9]+', slug) if bit]:
        species_candidates.extend(index.token_lookup.get(bit, []))
    if slug in index.token_lookup:
        species_candidates.extend(index.token_lookup[slug])
    species_candidates = _dedupe_paths(species_candidates) or index.files
    exact_species_candidates = []
    species_tokens = _species_specific_tokens(species_id)
    if species_tokens:
        for path in species_candidates:
            rel = str(path.relative_to(project_dir)).replace('\\', '/').lower()
            if any(seg == species_tokens for seg in _segment_tokens(rel)):
                exact_species_candidates.append(path)
    if exact_species_candidates:
        resolved, ranked = _resolve_from_candidates(project_dir, exact_species_candidates, species_id, kind, token, min_score=10)
        if resolved:
            return resolved, ranked
    return _resolve_from_candidates(project_dir, species_candidates, species_id, kind, token)


def validate_graphics(project_dir: Path, species_id: str, graphics: dict[str, str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for kind, rel in graphics.items():
        if not rel:
            findings.append({'severity': 'warning', 'kind': kind, 'message': 'missing graphic path'})
            continue
        candidate = project_dir / rel
        if not candidate.exists() or not candidate.is_file():
            findings.append({'severity': 'error', 'kind': kind, 'message': f'unresolved graphic path: {rel}'})
            continue
        if not _path_suffix_matches(candidate, kind):
            findings.append({'severity': 'warning', 'kind': kind, 'message': f'path extension looks wrong for {kind}: {rel}'})
        score = _kind_score(str(candidate.relative_to(project_dir)).replace('\\', '/').lower(), kind)
        if score < 0:
            findings.append({'severity': 'warning', 'kind': kind, 'message': f'path tokens look suspicious for {kind}: {rel}'})
    return findings


def _cache_signature(project_dir: Path) -> dict[str, int]:
    sig: dict[str, int] = {}
    for rel in ('graphics', 'src/data/pokemon/species_info.h', 'src/data/pokemon', 'include/constants'):
        p = project_dir / rel
        if p.exists():
            stat = p.stat()
            sig[rel] = int(getattr(stat, 'st_mtime_ns', int(stat.st_mtime * 1_000_000_000)))
    return sig


def _load_cache(cache_dir: Path | None, project_dir: Path) -> dict:
    if cache_dir is None:
        return {}
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / 'sprite_resolution_cache.json'
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
        if payload.get('project_dir') != str(project_dir):
            return {}
        if payload.get('signature') != _cache_signature(project_dir):
            return {}
        return payload
    except Exception:
        return {}


def _save_cache(cache_dir: Path | None, project_dir: Path, payload: dict) -> None:
    if cache_dir is None:
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload['project_dir'] = str(project_dir)
    payload['signature'] = _cache_signature(project_dir)
    (cache_dir / 'sprite_resolution_cache.json').write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')


def _graphics_index_signature(graphics_files: list[Path], project_dir: Path) -> dict[str, int | str]:
    newest = 0
    for p in graphics_files:
        try:
            stat = p.stat()
            newest = max(newest, int(getattr(stat, 'st_mtime_ns', int(stat.st_mtime * 1_000_000_000))))
        except OSError:
            pass
    return {'count': len(graphics_files), 'newest': newest, 'project_dir': str(project_dir)}


def _build_graphics_index(project_dir: Path, cache_dir: Path | None, progress=None) -> list[Path]:
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        index_path = cache_dir / 'graphics_file_index.json'
        current_sig = _cache_signature(project_dir)
        if index_path.exists():
            try:
                payload = json.loads(index_path.read_text(encoding='utf-8'))
                if payload.get('project_dir') == str(project_dir) and payload.get('signature') == current_sig:
                    files = [Path(p) for p in payload.get('files', [])]
                    if progress and getattr(progress, 'enabled', False):
                        progress.info(f'Using cached graphics index ({len(files)} files)')
                    return files
            except Exception:
                pass
    file_index = [Path(p) for p in build_file_index(str(project_dir))]
    graphics_files = [p for p in file_index if any(str(p).lower().endswith(s) for s in ASSET_SUFFIXES)]
    if cache_dir is not None:
        payload = {'project_dir': str(project_dir), 'signature': _cache_signature(project_dir), 'files': [str(p) for p in graphics_files]}
        (cache_dir / 'graphics_file_index.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return graphics_files


def _safe_progress_label(item: tuple[str, dict]) -> str:
    species_id, entry = item
    name = entry.get('speciesName') or species_id
    if not isinstance(name, str):
        name = str(name)
    return name.encode('ascii', errors='replace').decode('ascii')


def parse_sprite_assets(project_dir: Path, species_data: dict[str, dict], progress=None, cache_dir: Path | None = None, return_diagnostics: bool = False):
    graphics_files = _build_graphics_index(project_dir, cache_dir=cache_dir, progress=progress)
    sprite_index = _build_lookup_index(project_dir, graphics_files, progress=progress)
    result: dict[str, dict[str, str]] = {}
    diagnostics: dict[str, dict[str, list[dict[str, str]]]] = {'missing': {}, 'duplicates': {}}

    cache = _load_cache(cache_dir, project_dir)
    cached_species: dict[str, dict] = cache.get('species', {}) if cache else {}
    current_index_sig = _graphics_index_signature(graphics_files, project_dir)
    species_items = list(species_data.items())
    total = len(species_items)

    if progress and getattr(progress, 'enabled', False):
        progress.info(f'Resolving sprite assets for {total} species/forms across {len(graphics_files)} candidate files')

    iterator = species_items
    if progress is not None:
        iterator = progress.iter(species_items, 'sprite resolution', total=total, every=max(1, total // 100) if total else 1, detail=_safe_progress_label, per_item=True)

    changed = False
    for species_id, entry in iterator:
        graphics = dict(entry.get('graphics', {}))
        cache_key = json.dumps(graphics, sort_keys=True)
        cached = cached_species.get(species_id)
        if cached and cached.get('graphics_key') == cache_key and cached.get('index_signature') == current_index_sig:
            result[species_id] = dict(cached.get('resolved', {}))
            continue

        resolved: dict[str, str] = {}
        missing_for_species: list[dict[str, str]] = []
        duplicates_for_species: list[dict[str, str]] = []
        for key, token in graphics.items():
            if not token:
                continue
            resolved_path, ranked = _resolve_path(project_dir, sprite_index, species_id, key, str(token))
            resolved[key] = resolved_path or ''
            if not resolved_path:
                missing_for_species.append({'kind': key, 'token': str(token)})
            elif len(ranked) > 1:
                try:
                    top = int(ranked[0]['score'])
                    second = int(ranked[1]['score'])
                except Exception:
                    top = second = 0
                if top - second <= 2:
                    duplicates_for_species.append({'kind': key, 'chosen': ranked[0]['path'], 'alternatives': ', '.join(x['path'] for x in ranked[1:3])})
        result[species_id] = resolved
        if missing_for_species:
            diagnostics['missing'][species_id] = missing_for_species
        if duplicates_for_species:
            diagnostics['duplicates'][species_id] = duplicates_for_species
        cached_species[species_id] = {'graphics_key': cache_key, 'index_signature': current_index_sig, 'resolved': resolved}
        changed = True

    if changed or not cache:
        _save_cache(cache_dir, project_dir, {'species': cached_species})

    if progress and getattr(progress, 'enabled', False):
        missing_count = sum(len(v) for v in diagnostics['missing'].values())
        dup_count = sum(len(v) for v in diagnostics['duplicates'].values())
        progress.info(f'Sprite diagnostics: {missing_count} missing bindings, {dup_count} ambiguous bindings')
        for species_id, items in list(diagnostics['missing'].items())[:20]:
            for item in items:
                progress.info(f"WARNING missing sprite: {species_id} {item['kind']} ({item['token']})")
        for species_id, items in list(diagnostics['duplicates'].items())[:20]:
            for item in items:
                progress.info(f"WARNING ambiguous sprite: {species_id} {item['kind']} -> {item['chosen']} | alternates: {item['alternatives']}")

    return (result, diagnostics) if return_diagnostics else result
