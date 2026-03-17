from __future__ import annotations

from collections import defaultdict

from .schema import AbilityRecord, EncounterArea, EncounterSlot, Evolution, ItemLocation, ItemRecord, MoveRecord, ObstagoonModel, SpeciesRecord, SpriteAsset, TrainerPokemonRecord, TrainerRecord
from ..normalize import evolution_label, fix_mojibake, format_encounter_method, humanize_stat_key, humanize_symbol, infer_form_name, normalize_move_category, normalize_move_metric, pretty_source_label, slug_from_symbol, unique_preserve_order


PLACEHOLDER_SPECIES = {'SPECIES_NONE', 'SPECIES_EGG'}
PLACEHOLDER_MOVES = {'MOVE_NONE'}
PLACEHOLDER_ABILITIES = {'ABILITY_NONE'}
STAT_DISPLAY_ORDER = {'HP': 0, 'Atk': 1, 'Def': 2, 'SpA': 3, 'SpD': 4, 'Spe': 5}


def _normalize_species_lookup_key(value: str | None) -> str:
    text = fix_mojibake(str(value or '').strip()).lower()
    text = text.replace('’', "'")
    text = text.replace('-', '_').replace(' ', '_')
    text = text.replace("'", '')
    text = ''.join(ch for ch in text if ch.isalnum() or ch in {'_', '♀', '♂'})
    while '__' in text:
        text = text.replace('__', '_')
    return text.strip('_')


def _build_species_name_lookup(species_records: dict[str, SpeciesRecord]) -> dict[str, str]:
    lookup: dict[str, str] = {}

    def _priority(item: tuple[str, SpeciesRecord]) -> tuple[int, int, str]:
        species_id, rec = item
        is_base = 0 if not rec.base_species else 1
        form_index = rec.form_index if rec.form_index is not None else 0
        return (is_base, form_index, species_id)

    for species_id, rec in sorted(species_records.items(), key=_priority):
        keys = {
            species_id,
            rec.name,
            slug_from_symbol(species_id),
            slug_from_symbol(rec.name or ''),
            (rec.name or '').lower().replace(' ', '_'),
        }
        for key in keys:
            if not key:
                continue
            norm = _normalize_species_lookup_key(key)
            if norm:
                lookup.setdefault(norm, species_id)
    return lookup


def _resolve_trainer_species_id(entry: dict, species_lookup: dict[str, str]) -> str | None:
    for value in [entry.get('species_symbol'), entry.get('species_token'), entry.get('species_name')]:
        if not value:
            continue
        key = _normalize_species_lookup_key(value)
        if key in species_lookup:
            return species_lookup[key]
    return None






def _sort_trainer_stat_block(stats: dict[str, str] | None) -> dict[str, str]:
    if not stats:
        return {}
    return dict(sorted(stats.items(), key=lambda item: (STAT_DISPLAY_ORDER.get(str(item[0]), 999), str(item[0]))))


def _trainer_species_display_name(species_name: str, mon: dict) -> str:
    level = str(mon.get('level') or '').strip()
    if level:
        return f'{species_name} Level {level}'
    return species_name


def _use_base_species_picture_for_trainer_party(species: SpeciesRecord, mon: dict) -> bool:
    if mon.get('held_item') and 'mega' in str(mon.get('held_item')).lower():
        return True
    if not species.base_species:
        return False
    tokens = [species.species_id or '', species.form_name or '', species.name or '']
    joined = ' '.join(tokens).lower().replace('-', ' ').replace('_', ' ')
    return ' mega ' in f' {joined} ' or ' gmax ' in f' {joined} ' or ' gigantamax ' in f' {joined} '


def _trainer_party_species_for_display(species: SpeciesRecord | None, mon: dict, species_records: dict[str, SpeciesRecord]) -> SpeciesRecord | None:
    if species and _use_base_species_picture_for_trainer_party(species, mon) and species.base_species:
        return species_records.get(species.base_species) or species
    return species

def _display_trainer_name(trainer: dict) -> str:
    name = trainer.get('name') or humanize_symbol(trainer['trainer_id']) or trainer['trainer_id']
    trainer_id = str(trainer.get('trainer_id') or '')
    lowered_name = str(name).lower()
    if 'rematch' in trainer_id.lower() and 'rematch' not in lowered_name:
        name = f'{name} Rematch'
    return name


def _build_trainers(raw_trainers: list[dict], species_records: dict[str, SpeciesRecord]) -> dict[str, TrainerRecord]:
    species_lookup = _build_species_name_lookup(species_records)
    trainers: dict[str, TrainerRecord] = {}
    for trainer in raw_trainers:
        pokemon_records: list[TrainerPokemonRecord] = []
        for mon in trainer.get('pokemon', []):
            species_id = _resolve_trainer_species_id(mon, species_lookup)
            species = species_records.get(species_id) if species_id else None
            display_species = _trainer_party_species_for_display(species, mon, species_records)
            picture = None
            types: list[str] = []
            ability = mon.get('ability')
            species_name = mon.get('species_name') or humanize_symbol(species_id) or species_id or 'Unknown'
            if species:
                species_name = species.name
            species_name = _trainer_species_display_name(species_name, mon)
            if display_species:
                picture = display_species.graphics.get('frontPic')
                types = list(display_species.types)
            if species and not ability and species.abilities:
                ability = species.abilities[0]
            pokemon_records.append(TrainerPokemonRecord(
                species_id=species_id,
                species_name=species_name,
                picture=picture,
                types=types,
                ability=ability,
                tera_type=mon.get('tera_type'),
                evs=_sort_trainer_stat_block(mon.get('evs')),
                ivs=_sort_trainer_stat_block(mon.get('ivs')),
                held_item=mon.get('held_item'),
                moves=list(mon.get('moves') or []),
                nickname=mon.get('nickname'),
                level=mon.get('level'),
            ))
        trainers[trainer['trainer_id']] = TrainerRecord(
            trainer_id=trainer['trainer_id'],
            name=_display_trainer_name(trainer),
            picture=trainer.get('pic_path'),
            location=trainer.get('location'),
            has_party_pool=bool(trainer.get('has_party_pool')),
            party_size=trainer.get('party_size'),
            pool_rules=trainer.get('pool_rules') or (trainer.get('raw_metadata') or {}).get('Pool Rules'),
            pokemon=pokemon_records,
            class_name=trainer.get('class_name'),
            raw_metadata=dict(trainer.get('raw_metadata') or {}),
        )
    return trainers


def _species_sort_key(rec: SpeciesRecord) -> tuple[int, int, str]:
    return (
        1 if rec.base_species else 0,
        rec.form_index if rec.form_index is not None else 0,
        rec.species_id,
    )


def _resolve_requested_dex_species_id(requested_species_id: str, species_records: dict[str, SpeciesRecord]) -> str | None:
    if requested_species_id in species_records:
        return requested_species_id

    normal_alias = f"{requested_species_id}_NORMAL"
    if normal_alias in species_records:
        return normal_alias

    requested_name = humanize_symbol(requested_species_id) or slug_from_symbol(requested_species_id).replace('-', ' ').title()
    requested_name = fix_mojibake(requested_name or '').strip().lower()
    candidates = [rec for rec in species_records.values() if fix_mojibake(rec.name or '').strip().lower() == requested_name]
    if not candidates:
        return None

    preferred_form_names = {'normal', 'ordinary', 'base', 'standard', 'average'}
    candidates.sort(key=lambda rec: (
        0 if not rec.base_species else 1,
        0 if (fix_mojibake(rec.form_name or '').strip().lower() in preferred_form_names or rec.form_index == 0) else 1,
        rec.form_index if rec.form_index is not None else 9999,
        rec.species_id,
    ))
    return candidates[0].species_id


def _choose_representative_species_by_dex(species_records: dict[str, SpeciesRecord]) -> dict[int, str]:
    by_dex: dict[int, list[SpeciesRecord]] = defaultdict(list)
    for rec in species_records.values():
        if rec.national_dex is None or rec.species_id in PLACEHOLDER_SPECIES:
            continue
        by_dex[rec.national_dex].append(rec)
    result: dict[int, str] = {}
    for dex, records in by_dex.items():
        best = sorted(records, key=_species_sort_key)[0]
        result[dex] = best.species_id
    return result


def _fallback_egg_moves(species_records: dict[str, SpeciesRecord]) -> None:
    incoming: dict[str, list[str]] = defaultdict(list)
    for rec in species_records.values():
        for evo in rec.evolutions:
            target_id = getattr(evo, 'target_species_id', None) or evo.target_species
            if target_id in species_records:
                incoming[target_id].append(rec.species_id)

    def find_ancestor_egg_moves(species_id: str, seen: set[str] | None = None) -> list[str]:
        seen = seen or set()
        if species_id in seen:
            return []
        seen.add(species_id)
        for prev in incoming.get(species_id, []):
            prev_rec = species_records.get(prev)
            if not prev_rec:
                continue
            if prev_rec.learnsets.egg:
                return list(prev_rec.learnsets.egg)
            inherited = find_ancestor_egg_moves(prev, seen)
            if inherited:
                return inherited
        return []

    for rec in species_records.values():
        if not rec.learnsets.egg:
            rec.learnsets.egg = find_ancestor_egg_moves(rec.species_id)


def build_model(project) -> ObstagoonModel:
    raw = project.load_all()
    hoenn_mode = bool(getattr(project, 'hoenn_dex', False) or (bool(getattr(project, 'config', None).hoenn_dex) if getattr(project, 'config', None) is not None else False))
    species_to_national = raw['species_to_national']
    form_tables = raw.get('form_species_tables', {})
    base_by_species: dict[str, str] = {}
    form_index_by_species: dict[str, int] = {}
    forms_for_base: dict[str, list[str]] = defaultdict(list)
    for _, species_list in form_tables.items():
        if not species_list:
            continue
        base = species_list[0]
        for idx, sid in enumerate(species_list):
            form_index_by_species[sid] = idx
            if sid != base:
                base_by_species[sid] = base
                if sid not in forms_for_base[base]:
                    forms_for_base[base].append(sid)

    species_records: dict[str, SpeciesRecord] = {}
    sprites: list[SpriteAsset] = []
    for species_id, entry in raw['species'].items():
        if species_id in PLACEHOLDER_SPECIES:
            continue
        graphics = dict(entry.get('graphics', {}))
        raw_base_species = entry.get('baseSpecies')
        base_species = raw_base_species or base_by_species.get(species_id)
        rec = SpeciesRecord(
            species_id=species_id,
            national_dex=species_to_national.get(species_id),
            name=fix_mojibake(entry.get('speciesName')) or humanize_symbol(species_id) or slug_from_symbol(species_id).replace('-', ' ').title(),
            category=fix_mojibake(entry.get('categoryName')),
            description=fix_mojibake(entry.get('description')),
            types=unique_preserve_order([humanize_symbol(t) or t for t in entry.get('types', []) if t and t != 'TYPE_NONE']),
            abilities=unique_preserve_order([humanize_symbol(a) or a for a in entry.get('abilities', []) if a and a != 'ABILITY_NONE']),
            stats={humanize_stat_key(k) or k: (humanize_symbol(v) if isinstance(v, str) and v and not str(v).isdigit() else v) for k, v in entry.get('stats', {}).items()},
            catch_rate=entry.get('catchRate'),
            exp_yield=entry.get('expYield'),
            gender_ratio=entry.get('genderRatio'),
            growth_rate=humanize_symbol(entry.get('growthRate')),
            egg_groups=unique_preserve_order([humanize_symbol(g) or g for g in entry.get('eggGroups', []) if g and g != 'EGG_GROUP_NONE']),
            graphics=graphics,
        )
        rec.base_species = base_species if base_species and base_species != species_id else None
        if rec.base_species:
            if species_id not in forms_for_base[rec.base_species]:
                forms_for_base[rec.base_species].append(species_id)
            base_by_species.setdefault(species_id, rec.base_species)
        rec.form_name = infer_form_name(species_id, base_species)
        rec.form_index = entry.get('formSpeciesIdTableIndex') if entry.get('formSpeciesIdTableIndex') is not None else form_index_by_species.get(species_id)
        for evo in entry.get('evolutions', []):
            target_id = evo.get('target_species', 'SPECIES_NONE')
            rec.evolutions.append(Evolution(
                method=evo.get('method', 'UNKNOWN'),
                param=evo.get('param'),
                target_species=humanize_symbol(target_id) or target_id,
                method_label=evolution_label(evo.get('method', 'UNKNOWN'), evo.get('param')),
                target_species_id=target_id,
            ))
        level_up = sorted(entry.get('levelUpLearnset', []), key=lambda x: int(str(x.get('level') or '0').strip('() ') if str(x.get('level') or '0').strip('() ').isdigit() else 0))
        rec.learnsets.level_up = [{'level': item.get('level'), 'move': humanize_symbol(item.get('move')) or item.get('move')} for item in level_up]
        rec.learnsets.egg = [humanize_symbol(x) or x for x in entry.get('eggMoves', [])]
        rec.learnsets.teachable = [
            {
                'source': pretty_source_label(item.get('source')),
                'value': humanize_symbol(item.get('value')) or item.get('value'),
                'extra': humanize_symbol(item.get('extra')) if item.get('extra') else item.get('extra'),
            }
            for item in entry.get('teachableLearnset', [])
        ]
        if species_id in forms_for_base:
            rec.forms = list(dict.fromkeys(forms_for_base[species_id]))
        species_records[species_id] = rec
        for kind, source in graphics.items():
            if source:
                sprites.append(SpriteAsset(species_id=species_id, kind=kind, source=source))

    for rec in species_records.values():
        if rec.base_species and rec.base_species in species_records:
            siblings = [sid for sid, other in species_records.items() if other.base_species == rec.base_species and sid != rec.base_species]
            species_records[rec.base_species].forms = list(dict.fromkeys(species_records[rec.base_species].forms + siblings))

    _fallback_egg_moves(species_records)

    dex_label = 'National Dex #'
    dex_mode = 'national'
    raw_hoenn_order = []
    for sid in raw.get('hoenn_dex_order', []):
        resolved_sid = _resolve_requested_dex_species_id(sid, species_records)
        if resolved_sid:
            raw_hoenn_order.append(resolved_sid)
    hoenn_order: list[str] = []
    for sid in raw_hoenn_order:
        rec = species_records[sid]
        if rec.base_species:
            continue
        if sid not in hoenn_order:
            hoenn_order.append(sid)
    if hoenn_mode and hoenn_order:
        allowed = set(hoenn_order)
        allowed.update({sid for sid, rec in species_records.items() if rec.base_species in allowed})
        species_records = {sid: rec for sid, rec in species_records.items() if sid in allowed}
        sprites = [sprite for sprite in sprites if sprite.species_id in species_records]
        forms_for_base = {base: [sid for sid in children if sid in species_records] for base, children in forms_for_base.items() if base in species_records}
        national_to_species = {idx: sid for idx, sid in enumerate(hoenn_order, start=1)}
        dex_label = 'Hoenn Dex #'
        dex_mode = 'hoenn'
    else:
        national_to_species = _choose_representative_species_by_dex(species_records)

    moves = {
        move_id: MoveRecord(
            move_id=move_id,
            name=fix_mojibake(entry.get('name')) or humanize_symbol(move_id) or slug_from_symbol(move_id).replace('-', ' ').title(),
            description=fix_mojibake(entry.get('description')),
            type=humanize_symbol(entry.get('type')),
            power=normalize_move_metric(entry.get('power')),
            accuracy=normalize_move_metric(entry.get('accuracy')),
            pp=entry.get('pp'),
            category=normalize_move_category(entry.get('category')),
            flags=[humanize_symbol(flag) or flag for flag in entry.get('flags', [])],
        )
        for move_id, entry in raw['moves'].items()
        if move_id not in PLACEHOLDER_MOVES
    }
    abilities = {
        ability_id: AbilityRecord(
            ability_id=ability_id,
            name=fix_mojibake(entry.get('name')) or humanize_symbol(ability_id) or slug_from_symbol(ability_id).replace('-', ' ').title(),
            description=fix_mojibake(entry.get('description')),
        )
        for ability_id, entry in raw['abilities'].items()
        if ability_id not in PLACEHOLDER_ABILITIES
    }
    items = {
        item_id: ItemRecord(
            item_id=item_id,
            name=fix_mojibake(entry.get('name')) or humanize_symbol(item_id) or slug_from_symbol(item_id).replace('-', ' ').title(),
            description=fix_mojibake(entry.get('description')),
            pocket=humanize_symbol(entry.get('pocket')),
            price=entry.get('price'),
            locations=[ItemLocation(location=fix_mojibake(loc.get('location')) or 'Unknown', source=fix_mojibake(loc.get('source')) or 'Unknown') for loc in entry.get('locations', [])],
        )
        for item_id, entry in raw['items'].items()
    }
    encounter_areas = [EncounterArea(map_name=area.get('map'), display_name=fix_mojibake(area.get('display_name')) or slug_from_symbol(area.get('map', 'MAP_UNKNOWN')).replace('-', ' ').title(), encounters={format_encounter_method(method) or method: [EncounterSlot(species=humanize_symbol(slot.get('species')) or slot.get('species'), min_level=slot.get('min_level'), max_level=slot.get('max_level'), rate=slot.get('rate'), method=format_encounter_method(slot.get('method')) or slot.get('method')) for slot in slots] for method, slots in area.get('encounters', {}).items()}) for area in raw['encounters']]
    trainers = _build_trainers(raw.get('trainers', []), species_records)
    base_species_count = sum(1 for species_id, rec in species_records.items() if species_id not in PLACEHOLDER_SPECIES and not rec.base_species)
    metadata = {
        'project_kind': 'pokeemerald-expansion',
        'species_count': base_species_count,
        'move_count': len(moves),
        'ability_count': len(abilities),
        'item_count': len(items),
        'validation': raw.get('validation', {}),
        'representative_species_by_dex': national_to_species,
        'sprite_diagnostics': raw.get('sprite_diagnostics', {}),
        'trainer_count': len(trainers),
        'dex_label': dex_label,
        'dex_mode': dex_mode,
        'active_dex_map': {
            sid: dex
            for dex, species_id in national_to_species.items()
            for sid in [species_id, *forms_for_base.get(species_id, [])]
            if sid in species_records
        },
    }
    return ObstagoonModel(species=species_records, moves=moves, abilities=abilities, items=items, types={k: humanize_symbol(v) or v for k, v in raw['types'].items()}, encounters=encounter_areas, sprites=sprites, species_to_national=species_to_national, national_to_species=national_to_species, forms=dict(forms_for_base), trainers=trainers, metadata=metadata)
