from __future__ import annotations

from collections import defaultdict

from .schema import AbilityRecord, EncounterArea, EncounterSlot, Evolution, ItemRecord, MoveRecord, ObstagoonModel, SpeciesRecord, SpriteAsset
from ..normalize import evolution_label, fix_mojibake, format_encounter_method, humanize_stat_key, humanize_symbol, infer_form_name, normalize_move_category, pretty_source_label, slug_from_symbol, unique_preserve_order


PLACEHOLDER_SPECIES = {'SPECIES_NONE'}


def _species_sort_key(rec: SpeciesRecord) -> tuple[int, int, str]:
    return (
        1 if rec.base_species else 0,
        rec.form_index if rec.form_index is not None else 0,
        rec.species_id,
    )


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
    species_to_national = raw["species_to_national"]
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
    for species_id, entry in raw["species"].items():
        if species_id in PLACEHOLDER_SPECIES:
            continue
        graphics = dict(entry.get("graphics", {}))
        raw_base_species = entry.get("baseSpecies")
        base_species = raw_base_species or base_by_species.get(species_id)
        rec = SpeciesRecord(
            species_id=species_id,
            national_dex=species_to_national.get(species_id),
            name=fix_mojibake(entry.get("speciesName")) or humanize_symbol(species_id) or slug_from_symbol(species_id).replace("-", " ").title(),
            category=fix_mojibake(entry.get("categoryName")),
            description=fix_mojibake(entry.get("description")),
            types=unique_preserve_order([humanize_symbol(t) or t for t in entry.get("types", []) if t and t != 'TYPE_NONE']),
            abilities=unique_preserve_order([humanize_symbol(a) or a for a in entry.get("abilities", []) if a and a != 'ABILITY_NONE']),
            stats={humanize_stat_key(k) or k: (humanize_symbol(v) if isinstance(v, str) and v and not str(v).isdigit() else v) for k, v in entry.get("stats", {}).items()},
            catch_rate=entry.get("catchRate"),
            exp_yield=entry.get("expYield"),
            gender_ratio=entry.get("genderRatio"),
            growth_rate=humanize_symbol(entry.get("growthRate")),
            egg_groups=unique_preserve_order([humanize_symbol(g) or g for g in entry.get("eggGroups", []) if g and g != 'EGG_GROUP_NONE']),
            graphics=graphics,
        )
        rec.base_species = base_species if base_species and base_species != species_id else None
        if rec.base_species:
            if species_id not in forms_for_base[rec.base_species]:
                forms_for_base[rec.base_species].append(species_id)
            base_by_species.setdefault(species_id, rec.base_species)
        rec.form_name = infer_form_name(species_id, base_species)
        rec.form_index = entry.get("formSpeciesIdTableIndex") if entry.get("formSpeciesIdTableIndex") is not None else form_index_by_species.get(species_id)
        for evo in entry.get("evolutions", []):
            target_id = evo.get("target_species", "SPECIES_NONE")
            rec.evolutions.append(Evolution(
                method=evo.get("method", "UNKNOWN"),
                param=evo.get("param"),
                target_species=humanize_symbol(target_id) or target_id,
                method_label=evolution_label(evo.get("method", "UNKNOWN"), evo.get("param")),
                target_species_id=target_id,
            ))
        level_up = sorted(entry.get("levelUpLearnset", []), key=lambda x: int(str(x.get("level") or '0').strip('() ') if str(x.get('level') or '0').strip('() ').isdigit() else 0))
        rec.learnsets.level_up = [{'level': item.get('level'), 'move': humanize_symbol(item.get('move')) or item.get('move')} for item in level_up]
        rec.learnsets.egg = [humanize_symbol(x) or x for x in entry.get("eggMoves", [])]
        rec.learnsets.teachable = [
            {
                'source': pretty_source_label(item.get('source')),
                'value': humanize_symbol(item.get('value')) or item.get('value'),
                'extra': humanize_symbol(item.get('extra')) if item.get('extra') else item.get('extra'),
            }
            for item in entry.get("teachableLearnset", [])
        ]
        if species_id in forms_for_base:
            rec.forms = list(dict.fromkeys(forms_for_base[species_id]))
        species_records[species_id] = rec
        for kind, source in graphics.items():
            if source:
                sprites.append(SpriteAsset(species_id=species_id, kind=kind, source=source))

    # Second pass so baseSpecies-derived form families like Alcremie are retained even when
    # they are not exhaustively represented in form_species_tables.
    for rec in species_records.values():
        if rec.base_species and rec.base_species in species_records:
            siblings = [sid for sid, other in species_records.items() if other.base_species == rec.base_species and sid != rec.base_species]
            species_records[rec.base_species].forms = list(dict.fromkeys(species_records[rec.base_species].forms + siblings))

    _fallback_egg_moves(species_records)
    national_to_species = _choose_representative_species_by_dex(species_records)

    moves = {move_id: MoveRecord(move_id=move_id, name=fix_mojibake(entry.get("name")) or humanize_symbol(move_id) or slug_from_symbol(move_id).replace("-", " ").title(), description=fix_mojibake(entry.get("description")), type=humanize_symbol(entry.get("type")), power=entry.get("power"), accuracy=entry.get("accuracy"), pp=entry.get("pp"), category=normalize_move_category(entry.get("category")), flags=[humanize_symbol(flag) or flag for flag in entry.get("flags", [])]) for move_id, entry in raw["moves"].items()}
    abilities = {ability_id: AbilityRecord(ability_id=ability_id, name=fix_mojibake(entry.get("name")) or humanize_symbol(ability_id) or slug_from_symbol(ability_id).replace("-", " ").title(), description=fix_mojibake(entry.get("description"))) for ability_id, entry in raw["abilities"].items()}
    items = {item_id: ItemRecord(item_id=item_id, name=fix_mojibake(entry.get("name")) or humanize_symbol(item_id) or slug_from_symbol(item_id).replace("-", " ").title(), description=fix_mojibake(entry.get("description")), pocket=humanize_symbol(entry.get("pocket")), price=entry.get("price")) for item_id, entry in raw["items"].items()}
    encounter_areas = [EncounterArea(map_name=area.get("map"), display_name=fix_mojibake(area.get("display_name")) or slug_from_symbol(area.get("map", "MAP_UNKNOWN")).replace("-", " ").title(), encounters={format_encounter_method(method) or method: [EncounterSlot(species=humanize_symbol(slot.get('species')) or slot.get('species'), min_level=slot.get('min_level'), max_level=slot.get('max_level'), rate=slot.get('rate'), method=format_encounter_method(slot.get('method')) or slot.get('method')) for slot in slots] for method, slots in area.get("encounters", {}).items()}) for area in raw["encounters"]]
    metadata = {
        "project_kind": "pokeemerald-expansion",
        "species_count": len(species_records),
        "move_count": len(moves),
        "ability_count": len(abilities),
        "validation": raw.get('validation', {}),
        "representative_species_by_dex": national_to_species,
        "sprite_diagnostics": raw.get('sprite_diagnostics', {}),
    }
    return ObstagoonModel(species=species_records, moves=moves, abilities=abilities, items=items, types={k: humanize_symbol(v) or v for k, v in raw["types"].items()}, encounters=encounter_areas, sprites=sprites, species_to_national=species_to_national, national_to_species=national_to_species, forms=dict(forms_for_base), metadata=metadata)
