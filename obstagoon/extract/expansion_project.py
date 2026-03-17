from __future__ import annotations

from pathlib import Path

from ..validate import build_validation_report
from .parsers.abilities import parse_abilities
from .parsers.encounters import parse_encounters
from .parsers.forms import parse_form_species_tables
from .parsers.items import parse_items
from .parsers.learnsets import parse_learnsets
from .parsers.moves import parse_moves
from .parsers.sprites import parse_sprite_assets
from .parsers.species import parse_species
from .parsers.types import parse_hoenn_dex_order, parse_species_to_national, parse_types
from .parsers.trainers import parse_trainers
from .c_utils import discover_project_defines
from ..progress import ProgressReporter


def _resolve_hoenn_species_aliases(hoenn_dex_order: list[str], species: dict, form_species_tables: dict[str, list[str]]) -> tuple[list[str], set[str]]:
    available = set(species)
    resolved_order: list[str] = []
    aliases: set[str] = set()

    def resolve(symbol: str) -> str | None:
        if symbol in available:
            return symbol
        normal_alias = f"{symbol}_NORMAL"
        if normal_alias in available:
            aliases.add(symbol)
            return normal_alias
        for species_list in form_species_tables.values():
            if not species_list:
                continue
            base = species_list[0]
            if base == normal_alias:
                aliases.add(symbol)
                return base
        return None

    for symbol in hoenn_dex_order:
        resolved = resolve(symbol)
        if resolved and resolved not in resolved_order:
            resolved_order.append(resolved)
    return resolved_order, aliases


class ExpansionProject:
    def __init__(self, project_dir: Path, verbose: bool = False, wild_encounters_path: Path | None = None, cache_dir: Path | None = None, hoenn_dex: bool = False) -> None:
        self.project_dir = project_dir
        self.verbose = verbose
        self.wild_encounters_path = wild_encounters_path
        self.cache_dir = cache_dir
        self.hoenn_dex = hoenn_dex

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)

    def load_all(self) -> dict:
        progress = ProgressReporter(enabled=self.verbose, total_steps=13)
        defines = discover_project_defines(str(self.project_dir))
        progress.step('Parsing types')
        types = parse_types(self.project_dir)
        progress.step('Parsing dex mapping')
        species_to_national = parse_species_to_national(self.project_dir)
        hoenn_dex_order: list[str] = []
        if self.hoenn_dex:
            progress.step('Parsing Hoenn dex order')
            hoenn_dex_order = parse_hoenn_dex_order(self.project_dir, defines=defines)
        else:
            progress.step('Skipping Hoenn dex order (flag not enabled)')
        progress.step('Parsing learnsets')
        learnsets = parse_learnsets(self.project_dir, defines=defines)
        progress.step('Parsing species')
        species = parse_species(self.project_dir, species_to_national=species_to_national, learnsets=learnsets, defines=defines)
        progress.step('Parsing moves')
        moves = parse_moves(self.project_dir, defines=defines)
        progress.step('Parsing abilities')
        abilities = parse_abilities(self.project_dir, defines=defines)
        progress.step('Parsing items')
        items = parse_items(self.project_dir)
        progress.step('Parsing form tables')
        form_species_tables = parse_form_species_tables(self.project_dir, defines=defines)
        resolved_hoenn_dex_order = list(hoenn_dex_order)
        hoenn_dex_aliases: set[str] = set()
        if self.hoenn_dex and hoenn_dex_order:
            resolved_hoenn_dex_order, hoenn_dex_aliases = _resolve_hoenn_species_aliases(hoenn_dex_order, species, form_species_tables)
        progress.step('Parsing sprite assets')
        sprite_candidates = species
        if self.hoenn_dex and resolved_hoenn_dex_order:
            allowed = set(resolved_hoenn_dex_order)
            for species_list in form_species_tables.values():
                if not species_list:
                    continue
                base_species = species_list[0]
                if base_species in allowed:
                    allowed.update(species_list)
            for species_id, entry in species.items():
                base_species = entry.get('baseSpecies')
                if base_species in allowed:
                    allowed.add(species_id)
            sprite_candidates = {sid: entry for sid, entry in species.items() if sid in allowed}
        sprites, sprite_diagnostics = parse_sprite_assets(self.project_dir, sprite_candidates, progress=progress, cache_dir=self.cache_dir, return_diagnostics=True)
        for species_id, graphics in sprites.items():
            if species_id in species:
                species[species_id]['graphics'] = graphics
        progress.step('Parsing encounters')
        encounters = parse_encounters(self.project_dir, generated_json=self.wild_encounters_path)
        progress.step('Parsing trainers')
        trainers = parse_trainers(self.project_dir, defines=defines)
        progress.step('Validating assets')
        validation = build_validation_report(self.project_dir, {'species': species})
        progress.info(f"Loaded {len(species)} species, {len(moves)} moves, {len(abilities)} abilities, and {len(encounters)} encounter areas")
        return {
            'types': types,
            'species_to_national': species_to_national,
            'hoenn_dex_order': resolved_hoenn_dex_order,
            'hoenn_dex_aliases': sorted(hoenn_dex_aliases),
            'moves': moves,
            'abilities': abilities,
            'items': items,
            'learnsets': learnsets,
            'species': species,
            'form_species_tables': form_species_tables,
            'sprites': sprites,
            'encounters': encounters,
            'trainers': trainers,
            'validation': validation,
            'sprite_diagnostics': sprite_diagnostics,
        }
