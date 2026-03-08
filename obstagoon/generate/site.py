from __future__ import annotations

import json
import shutil
from pathlib import Path

from ..config import SiteConfig
from ..model.schema import ObstagoonModel, SpeciesRecord
from ..normalize import format_encounter_method, humanize_symbol, slug_from_symbol, type_badge_class
from ..progress import ProgressReporter


class SiteGenerator:
    def __init__(self, config: SiteConfig, model: ObstagoonModel, env) -> None:
        self.config = config
        self.model = model
        self.env = env
        self._rep_species_by_dex = {
            dex: self.model.species[sid]
            for dex, sid in self.model.national_to_species.items()
            if sid in self.model.species
        }

    def run(self) -> None:
        self.progress = ProgressReporter(enabled=self.config.verbose, total_steps=12 if self.config.copy_assets else 11)
        self.progress.step('Preparing output directories')
        self._prepare_dirs()
        self.progress.step('Writing CSS')
        self._write_css()
        if self.config.copy_assets:
            self.progress.step('Copying sprite and asset files')
            self._copy_assets()
        self.progress.step('Writing manifest')
        self._write_manifest()
        self.progress.step('Writing validation report')
        self._write_validation_report()
        self.progress.step('Rendering index')
        self._render_index()
        self.progress.step('Rendering Pokédex index')
        self._render_pokedex()
        self.progress.step('Rendering species pages')
        self._render_species_pages()
        self.progress.step('Rendering move pages')
        self._render_moves()
        self.progress.step('Rendering ability pages')
        self._render_abilities()
        self.progress.step('Rendering type and form pages')
        self._render_types()
        self._render_forms()
        self.progress.step('Rendering encounters')
        self._render_encounters()
        self.progress.info('Build complete')

    def _prepare_dirs(self) -> None:
        for rel in ['pokedex', 'moves', 'abilities', 'types', 'forms', 'encounters', 'assets']:
            (self.config.dist_dir / rel).mkdir(parents=True, exist_ok=True)

    def _ctx(self, **extra):
        return {
            'site_title': self.config.site_title,
            'site_url': self.config.site_url,
            'model': self.model,
            'humanize_symbol': humanize_symbol,
            'slug_from_symbol': slug_from_symbol,
            'type_badge_class': type_badge_class,
            **extra,
        }

    def _render(self, template_name: str, rel_path: str, **ctx) -> None:
        template = self.env.get_template(template_name)
        html = template.render(**self._ctx(**ctx))
        target = self.config.dist_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding='utf-8')

    def _write_css(self) -> None:
        css = (Path(__file__).resolve().parent.parent / 'templates' / 'style.css').read_text(encoding='utf-8')
        (self.config.dist_dir / 'assets' / 'style.css').write_text(css, encoding='utf-8')

    def _write_manifest(self) -> None:
        payload = {
            'metadata': self.model.metadata,
            'species': len(self.model.species),
            'moves': len(self.model.moves),
            'abilities': len(self.model.abilities),
            'encounters': len(self.model.encounters),
            'validation_summary': self.model.metadata.get('validation', {}).get('summary', {}),
            'sprite_diagnostics_summary': {
                'missing_species': len(self.model.metadata.get('sprite_diagnostics', {}).get('missing', {})),
                'duplicate_species': len(self.model.metadata.get('sprite_diagnostics', {}).get('duplicates', {})),
            },
        }
        (self.config.dist_dir / 'assets' / 'manifest.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')

    def _write_validation_report(self) -> None:
        payload = {
            'validation': self.model.metadata.get('validation', {}),
            'sprite_diagnostics': self.model.metadata.get('sprite_diagnostics', {}),
        }
        (self.config.dist_dir / 'assets' / 'validation.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')

    def _render_index(self) -> None:
        self._render('index.html', 'index.html')

    def _prefer_non_shiny_back_sprite(self, source: str | None) -> str | None:
        if not source:
            return source
        src = str(source).replace('\\', '/')
        if '/shiny/' not in src:
            return source
        candidate = src.replace('/shiny/', '/')
        project_candidate = self.config.project_dir / candidate
        if project_candidate.exists() and project_candidate.is_file():
            return candidate
        return source

    def _display_graphics_for_species(self, species: SpeciesRecord) -> dict[str, str]:
        graphics = dict(species.graphics)
        # For representative/base display pages, prefer this species's own base-form graphics.
        # Only inherit from base species when the current species is itself a form and the field is missing.
        if species.base_species and species.base_species in self.model.species:
            base = self.model.species[species.base_species]
            for key in ('frontPic', 'palette', 'backPic', 'iconSprite'):
                if (not graphics.get(key)) and base.graphics.get(key):
                    graphics[key] = base.graphics[key]
        for key in ('backPic', 'backPicFemale'):
            graphics[key] = self._prefer_non_shiny_back_sprite(graphics.get(key))
        return graphics


    def _encounters_for_species(self, species: SpeciesRecord) -> list[dict]:
        matches = []
        target_names = {species.name}
        target_ids = {species.species_id}
        if species.base_species:
            target_ids.add(species.base_species)
            base = self.model.species.get(species.base_species)
            if base:
                target_names.add(base.name)
        for area in self.model.encounters:
            methods = []
            for method, slots in area.encounters.items():
                relevant = []
                for slot in slots:
                    slot_species = str(slot.species or '').strip()
                    if slot_species in target_names or slot_species in target_ids:
                        relevant.append(slot)
                if relevant:
                    methods.append({'method': format_encounter_method(method) or method, 'slots': relevant})
            if methods:
                matches.append({'display_name': area.display_name, 'map_name': area.map_name, 'methods': methods})
        return matches

    def _render_pokedex(self) -> None:
        dex_entries = sorted(self._rep_species_by_dex.items(), key=lambda x: x[0])
        self._render('pokedex_index.html', 'pokedex/index.html', dex_entries=dex_entries, display_graphics=self._display_graphics_for_species)

    def _species_slug_path(self, species: SpeciesRecord) -> str:
        return f'pokedex/{slug_from_symbol(species.species_id)}.html'

    def _render_species_pages(self) -> None:
        species_values = sorted(self.model.species.values(), key=lambda s: (s.national_dex is None, s.national_dex or 99999, s.base_species is not None, s.form_index or 0, s.name))
        for species in self.progress.iter(species_values, 'species pages', every=25, detail=lambda s: s.name):
            self._render('species.html', self._species_slug_path(species), species=species, display_graphics=self._display_graphics_for_species(species), encounter_locations=self._encounters_for_species(species))
        for dex, species in self.progress.iter(sorted(self._rep_species_by_dex.items()), 'dex pages', every=25, detail=lambda item: item[1].name):
            self._render('species.html', f'pokedex/{dex}.html', species=species, display_graphics=self._display_graphics_for_species(species), encounter_locations=self._encounters_for_species(species))

    def _render_moves(self) -> None:
        moves = sorted(self.model.moves.values(), key=lambda m: m.name)
        self._render('moves_index.html', 'moves/index.html', moves=moves)
        for move in self.progress.iter(moves, 'move pages', every=100, detail=lambda m: m.name):
            self._render('move.html', f'moves/{slug_from_symbol(move.move_id)}.html', move=move)

    def _render_abilities(self) -> None:
        abilities = sorted(self.model.abilities.values(), key=lambda a: a.name)
        self._render('abilities_index.html', 'abilities/index.html', abilities=abilities)
        for ability in self.progress.iter(abilities, 'ability pages', every=50, detail=lambda a: a.name):
            self._render('ability.html', f'abilities/{slug_from_symbol(ability.ability_id)}.html', ability=ability)

    def _render_types(self) -> None:
        type_items = sorted(self.model.types.items())
        for type_id, label in self.progress.iter(type_items, 'type pages', every=10, detail=lambda item: item[1]):
            species = [s for s in self.model.species.values() if label in s.types]
            moves = [m for m in self.model.moves.values() if m.type == label]
            self._render('type.html', f'types/{slug_from_symbol(type_id)}.html', type_id=type_id, label=label, species=species, moves=moves)

    def _render_forms(self) -> None:
        form_groups = []
        for base, children in self.progress.iter(sorted(self.model.forms.items()), 'form groups', every=25, detail=lambda item: self.model.species.get(item[0]).name if self.model.species.get(item[0]) else item[0]):
            if base not in self.model.species:
                continue
            form_groups.append((self.model.species[base], [self.model.species[c] for c in children if c in self.model.species]))
        self._render('forms.html', 'forms/index.html', form_groups=form_groups)

    def _render_encounters(self) -> None:
        self._render('encounters.html', 'encounters/index.html', encounters=self.model.encounters)

    def _load_asset_cache(self) -> dict:
        path = self.config.cache_dir / 'asset_copy_cache.json'
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def _save_asset_cache(self, payload: dict) -> None:
        path = self.config.cache_dir / 'asset_copy_cache.json'
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')

    def _copy_assets(self) -> None:
        assets_root = self.config.dist_dir / 'assets' / 'game'
        assets_root.mkdir(parents=True, exist_ok=True)
        cache = self._load_asset_cache()
        copied = set()
        copied_count = 0
        skipped_count = 0
        cache_entries = cache.get('files', {}) if isinstance(cache.get('files', {}), dict) else {}
        species_values = list(self.model.species.values())
        for species in self.progress.iter(species_values, 'asset copy', every=max(1, len(species_values) // 100) if species_values else 1, detail=lambda s: getattr(s, 'name', getattr(s, 'species_id', ''))):
            copied_graphics = {}
            display_graphics = self._display_graphics_for_species(species)
            for key, source in display_graphics.items():
                source_str = str(source).replace('\\', '/')
                candidate = self.config.project_dir / source_str
                if candidate.exists() and candidate.is_file():
                    rel = Path(source_str)
                    target = assets_root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source_stat = candidate.stat()
                    sig = {'size': int(source_stat.st_size), 'mtime_ns': int(getattr(source_stat, 'st_mtime_ns', int(source_stat.st_mtime * 1_000_000_000)))}
                    cache_key = str(candidate)
                    target_exists = target.exists() and target.is_file()
                    if candidate not in copied:
                        if target_exists and cache_entries.get(cache_key) == sig:
                            skipped_count += 1
                        else:
                            shutil.copy2(candidate, target)
                            copied_count += 1
                            cache_entries[cache_key] = sig
                        copied.add(candidate)
                    copied_graphics[key] = f'../assets/game/{rel.as_posix()}'
                else:
                    copied_graphics[key] = source_str
            species.graphics = copied_graphics
        cache['files'] = cache_entries
        self._save_asset_cache(cache)
        self.progress.info(f'Asset copy complete: {copied_count} copied, {skipped_count} reused from cache')
