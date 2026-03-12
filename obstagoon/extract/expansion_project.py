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
from .parsers.types import parse_species_to_national, parse_types
from .parsers.trainers import parse_trainers
from .c_utils import discover_project_defines
from ..progress import ProgressReporter


class ExpansionProject:
    def __init__(self, project_dir: Path, verbose: bool = False, wild_encounters_path: Path | None = None, cache_dir: Path | None = None) -> None:
        self.project_dir = project_dir
        self.verbose = verbose
        self.wild_encounters_path = wild_encounters_path
        self.cache_dir = cache_dir

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)

    def load_all(self) -> dict:
        progress = ProgressReporter(enabled=self.verbose, total_steps=12)
        defines = discover_project_defines(str(self.project_dir))
        progress.step('Parsing types')
        types = parse_types(self.project_dir)
        progress.step('Parsing dex mapping')
        species_to_national = parse_species_to_national(self.project_dir)
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
        progress.step('Parsing sprite assets')
        sprites, sprite_diagnostics = parse_sprite_assets(self.project_dir, species, progress=progress, cache_dir=self.cache_dir, return_diagnostics=True)
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
