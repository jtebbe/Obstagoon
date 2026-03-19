from __future__ import annotations

import io
import json
import mimetypes
import re
import shutil
import struct
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PIL import Image
from xml.sax.saxutils import escape

from ..config import SiteConfig
from ..model.schema import ObstagoonModel, SpeciesRecord, TrainerRecord
from ..normalize import format_encounter_method, humanize_symbol, slug_from_symbol, safe_filename_slug, type_badge_class
from ..progress import ProgressReporter




def _load_pillow_image_module():
    try:
        from PIL import Image as PILImage
    except ImportError as exc:
        raise RuntimeError(
            "--pillow-transparency was requested, but Pillow is not installed. Install it with 'python3 -m pip install Pillow' or omit --pillow-transparency."
        ) from exc
    return PILImage

TYPE_ICON_COLORS = {
    'normal': '#8f8a81',
    'fire': '#e76f51',
    'water': '#4d90fe',
    'electric': '#f4c430',
    'grass': '#43aa57',
    'ice': '#58c4dd',
    'fighting': '#c65b3d',
    'poison': '#9c6ade',
    'ground': '#c59b55',
    'flying': '#7c8cff',
    'psychic': '#ff5d8f',
    'bug': '#93b125',
    'rock': '#b49b55',
    'ghost': '#6f62b5',
    'dragon': '#5a64ea',
    'dark': '#705848',
    'steel': '#8aa1b1',
    'fairy': '#e98ad7',
    'stellar': '#8b5cf6',
    'unknown': '#6b7280',
}


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
        self.progress = ProgressReporter(enabled=self.config.verbose, total_steps=15 if self.config.copy_assets else 14)
        self.progress.step('Preparing output directories')
        self._prepare_dirs()
        self.progress.step('Writing CSS')
        self._write_css()
        self.progress.step('Writing generated type icons')
        self._write_type_icons()
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
        self.progress.step('Rendering itemdex')
        self._render_itemdex()
        self.progress.step('Rendering trainerdex')
        self._render_trainerdex()
        self.progress.info('Build complete')

    def _prepare_dirs(self) -> None:
        for rel in ['pokedex', 'moves', 'abilities', 'types', 'forms', 'encounters', 'itemdex', 'trainerdex', 'assets', 'assets/generated/types']:
            (self.config.dist_dir / rel).mkdir(parents=True, exist_ok=True)

    def _ctx(self, **extra):
        return {
            'site_title': self.config.site_title,
            'site_url': self.config.site_url,
            'model': self.model,
            'humanize_symbol': humanize_symbol,
            'slug_from_symbol': slug_from_symbol,
            'type_badge_class': type_badge_class,
            'type_icon_path': self._type_icon_path,
            'trainer_slug_path': self._trainer_slug_path,
            'species_slug_path': self._species_slug_path,
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

    def _type_icon_path(self, type_name: str | None) -> str:
        slug = safe_filename_slug(type_name or 'unknown')
        return f'../assets/generated/types/{slug}.svg'

    def _write_type_icons(self) -> None:
        out_dir = self.config.dist_dir / 'assets' / 'generated' / 'types'
        out_dir.mkdir(parents=True, exist_ok=True)
        labels: dict[str, str] = {safe_filename_slug(label): label.replace('-', ' ').title() for label in TYPE_ICON_COLORS}
        for raw_value in self.model.types.values():
            display_title = humanize_symbol(raw_value) or str(raw_value or 'Unknown').replace('-', ' ').title()
            labels[safe_filename_slug(raw_value)] = display_title
        for slug, title in sorted(labels.items()):
            color = TYPE_ICON_COLORS.get(slug, TYPE_ICON_COLORS['unknown'])
            fg = '#111827' if slug in {'electric', 'ground', 'bug', 'ice', 'steel', 'fairy'} else '#f9fafb'
            svg = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="76" height="24" viewBox="0 0 76 24" role="img" aria-label="{escape(title)} type">'
                f'<rect x="0.5" y="0.5" rx="12" ry="12" width="75" height="23" fill="{color}" stroke="rgba(255,255,255,0.18)"/>'
                f'<text x="38" y="15" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" font-weight="700" fill="{fg}">{escape(title.upper())}</text>'
                '</svg>'
            )
            (out_dir / f'{slug}.svg').write_text(svg, encoding='utf-8')

    def _write_manifest(self) -> None:
        payload = {
            'metadata': self.model.metadata,
            'species': len(self.model.species),
            'moves': len(self.model.moves),
            'abilities': len(self.model.abilities),
            'encounters': len(self.model.encounters),
            'trainers': len(self.model.trainers),
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


    def trainer_editor_species_display_name(self, species: SpeciesRecord) -> str:
        species_id = str(getattr(species, 'species_id', '') or '').strip()
        label = humanize_symbol(species_id.replace('SPECIES_', '')) if species_id else ''
        label = str(label or '').strip()
        if label:
            return label.replace(' ', '-')
        name = str(getattr(species, 'name', '') or '').strip()
        return name.replace(' ', '-') if name else 'Unknown'

    def _normalize_trainer_editor_palette_rel(self, palette_rel: str | None) -> str | None:
        if not palette_rel:
            return None
        rel = Path(str(palette_rel).replace('\\', '/'))
        suffix = rel.suffix.lower()
        if suffix == '.gbapal':
            pal_rel = rel.with_suffix('.pal')
            pal_candidate = self.config.project_dir / pal_rel
            if pal_candidate.exists() and pal_candidate.is_file():
                return pal_rel.as_posix()
            return None
        if suffix != '.pal':
            return None
        return rel.as_posix()

    def _fallback_shiny_palette_rel(self, normal_palette_rel: str | None) -> str | None:
        normalized = self._normalize_trainer_editor_palette_rel(normal_palette_rel)
        if not normalized:
            return None
        normal_path = Path(normalized)
        candidates: list[Path] = []
        parent_name = normal_path.parent.name.lower()
        stem = normal_path.stem.lower()
        if stem in {'normal', 'palette'}:
            candidates.append(normal_path.with_name('shiny.pal'))
        if parent_name:
            candidates.append(normal_path.with_name(f"{parent_name}_shiny.pal"))
        candidates.append(normal_path.with_name(f"{normal_path.stem}_shiny.pal"))
        for candidate_rel in candidates:
            candidate = self.config.project_dir / candidate_rel
            if candidate.exists() and candidate.is_file() and candidate.suffix.lower() == '.pal':
                return candidate_rel.as_posix()
        return None

    def _apply_palette_to_png_with_source_palette(self, image: 'Image.Image', palette_path: Path | None, source_path: Path | None = None, source_palette_path: Path | None = None) -> 'Image.Image':
        if palette_path is None or not palette_path.exists() or not palette_path.is_file():
            return image
        target_palette = self._load_binary_palette(palette_path)
        if not target_palette:
            return image
        resolved_source_palette = source_palette_path
        if resolved_source_palette is None and source_path is not None:
            resolved_source_palette = self._find_source_palette_for_sprite(source_path, palette_path)
        source_palette = self._load_binary_palette(resolved_source_palette) if resolved_source_palette else None
        if image.mode == 'P':
            pal_image = image.copy()
            current_palette = self._padded_palette(list(pal_image.getpalette() or []))
            replacement = self._padded_palette(target_palette)
            replace_len = min(len(target_palette), len(current_palette))
            current_palette[:replace_len] = replacement[:replace_len]
            pal_image.putpalette(current_palette[:768])
            transparency = pal_image.info.get('transparency', image.info.get('transparency'))
            if transparency is not None:
                pal_image.info['transparency'] = transparency
            return pal_image
        if source_palette:
            return self._recolor_rgba_with_palettes(image, source_palette, target_palette)
        return image

    def _trainer_editor_species_asset_slugs(self, species: SpeciesRecord) -> list[str]:
        slugs: list[str] = []
        seen: set[str] = set()

        def add(value: str | None) -> None:
            if not value:
                return
            cleaned = value.replace('SPECIES_', '').strip().lower()
            cleaned = cleaned.replace('♀', 'f').replace('♂', 'm')
            cleaned = cleaned.replace("'", '')
            cleaned = re.sub(r'[^a-z0-9]+', '_', cleaned).strip('_')
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                slugs.append(cleaned)

        add(species.species_id)
        add(species.name)
        if species.base_species:
            add(species.base_species)
            base = self.model.species.get(species.base_species)
            if base:
                add(base.name)
                if species.form_name:
                    add(f'{base.name}_{species.form_name}')
                    add(f'{base.species_id.replace("SPECIES_", "")}_{species.form_name}')
        if species.form_name:
            add(species.form_name)
        return slugs

    def _resolve_trainer_editor_preview_source(self, species: SpeciesRecord, source_rel: str | None, palette_path: Path | None = None) -> Path | None:
        front_names = ('front.png', 'anim_front.png')

        def raster_front_in(directory: Path | None) -> Path | None:
            if directory is None:
                return None
            directory = directory.resolve()
            for name in front_names:
                candidate = directory / name
                if candidate.exists() and candidate.is_file():
                    return candidate
            return None

        source_dir: Path | None = None
        if source_rel:
            rel = Path(str(source_rel).replace('\\', '/'))
            source_dir = (self.config.project_dir / rel).parent

        candidate_dirs: list[Path] = []
        seen: set[Path] = set()

        def add_dir(path: Path | None) -> None:
            if path is None:
                return
            resolved = path.resolve()
            if resolved in seen:
                return
            seen.add(resolved)
            candidate_dirs.append(resolved)

        if palette_path is not None and palette_path.exists() and palette_path.is_file() and palette_path.suffix.lower() == '.pal':
            add_dir(palette_path.parent)
        add_dir(source_dir)
        if species.base_species and species.base_species in self.model.species:
            base = self.model.species[species.base_species]
            base_graphics = self._display_graphics_for_species(base)
            base_front = base_graphics.get('frontPicFemale') or base_graphics.get('frontPic')
            if base_front:
                add_dir((self.config.project_dir / Path(str(base_front).replace('\\', '/'))).parent)
        for slug in self._trainer_editor_species_asset_slugs(species):
            add_dir(self.config.project_dir / 'graphics' / 'pokemon' / slug)

        for directory in candidate_dirs:
            front = raster_front_in(directory)
            if front is not None:
                return front
        return None

    def trainer_editor_render_species_preview(self, species: SpeciesRecord, *, shiny: bool = False) -> tuple[bytes, str] | None:
        graphics = self._display_graphics_for_species(species)
        normal_palette_rel = self._normalize_trainer_editor_palette_rel(graphics.get('paletteFemale') or graphics.get('palette'))
        normal_palette_path = self.config.project_dir / str(normal_palette_rel).replace('\\', '/') if normal_palette_rel else None
        shiny_palette_rel = self._normalize_trainer_editor_palette_rel(
            graphics.get('shinyPaletteFemale') or graphics.get('shinyPalette') or self._fallback_shiny_palette_rel(normal_palette_rel)
        )
        shiny_palette_path = self.config.project_dir / str(shiny_palette_rel).replace('\\', '/') if shiny_palette_rel else None
        front_rel = graphics.get('frontPicFemale') or graphics.get('frontPic')

        source_path: Path | None = None
        if front_rel:
            candidate = self.config.project_dir / str(front_rel).replace('\\', '/')
            if candidate.exists() and candidate.is_file():
                source_path = candidate

        palette_for_resolution = shiny_palette_path if (shiny and shiny_palette_path is not None) else normal_palette_path
        resolved_source: Path | None = None
        if source_path is not None:
            resolved_source = self._resolve_palette_sprite_source(source_path, palette_for_resolution)
            if (
                resolved_source is None
                or not resolved_source.exists()
                or not resolved_source.is_file()
                or resolved_source.suffix.lower() != '.png'
                or resolved_source.name.lower() not in {'front.png', 'anim_front.png'}
            ):
                resolved_source = None

        if resolved_source is None:
            resolved_source = self._resolve_trainer_editor_preview_source(species, front_rel, palette_for_resolution)
        if (
            resolved_source is None
            or resolved_source.suffix.lower() != '.png'
            or resolved_source.name.lower() not in {'front.png', 'anim_front.png'}
        ):
            return None
        try:
            Image = _load_pillow_image_module()
            with Image.open(resolved_source) as opened:
                img = opened.copy()
            try:
                resolved_rel = resolved_source.relative_to(self.config.project_dir)
            except ValueError:
                resolved_rel = Path(resolved_source.name)

            # Non-shiny preview should mirror documentation asset processing.
            apply_normal_palette = False
            if normal_palette_path and normal_palette_path.exists() and normal_palette_path.is_file() and normal_palette_rel:
                apply_normal_palette = self._should_apply_palette_variant(resolved_rel, normal_palette_rel)
            if apply_normal_palette and normal_palette_rel:
                img = self._apply_palette_to_png(img, self.config.project_dir / normal_palette_rel, resolved_source)

            # Shiny recolor is trainer-editor-only and layered on the same resolved preview source.
            if shiny and shiny_palette_path and shiny_palette_path.exists() and shiny_palette_path.is_file():
                img = self._apply_palette_to_png_with_source_palette(
                    img,
                    shiny_palette_path,
                    resolved_source,
                    source_palette_path=normal_palette_path,
                )

            if self._should_crop_top_half(resolved_rel):
                crop_h = max(1, img.height // 2)
                img = img.crop((0, 0, img.width, crop_h))
            if self._should_process_transparent_sprite(resolved_rel):
                img = self._make_png_background_transparent(img)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue(), 'image/png'
        except Exception:
            mime = mimetypes.guess_type(resolved_source.name)[0] or 'application/octet-stream'
            return resolved_source.read_bytes(), mime

    def _display_graphics_for_species(self, species: SpeciesRecord) -> dict[str, str]:
        graphics = dict(species.graphics)
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
        self._render('pokedex_index.html', 'pokedex/index.html', dex_entries=dex_entries, dex_label=self.model.metadata.get('dex_label', 'National Dex #'), display_graphics=self._display_graphics_for_species)

    def _species_slug_path(self, species: SpeciesRecord) -> str:
        return f'pokedex/{slug_from_symbol(species.species_id)}.html'

    def _trainer_slug_path(self, trainer: TrainerRecord) -> str:
        return f'trainerdex/{slug_from_symbol(trainer.trainer_id)}.html'

    def _render_species_pages(self) -> None:
        active_dex_map = self.model.metadata.get('active_dex_map', {})
        species_values = sorted(self.model.species.values(), key=lambda s: (active_dex_map.get(s.species_id) is None, active_dex_map.get(s.species_id) or s.national_dex or 99999, s.base_species is not None, s.form_index or 0, s.name))
        for species in self.progress.iter(species_values, 'species pages', every=25, detail=lambda s: s.name):
            self._render('species.html', self._species_slug_path(species), species=species, display_graphics=self._display_graphics_for_species(species), encounter_locations=self._encounters_for_species(species), dex_label=self.model.metadata.get('dex_label', 'National Dex #'), active_dex_number=self.model.metadata.get('active_dex_map', {}).get(species.species_id))
        for dex, species in self.progress.iter(sorted(self._rep_species_by_dex.items()), 'dex pages', every=25, detail=lambda item: item[1].name):
            self._render('species.html', f'pokedex/{dex}.html', species=species, display_graphics=self._display_graphics_for_species(species), encounter_locations=self._encounters_for_species(species), dex_label=self.model.metadata.get('dex_label', 'National Dex #'), active_dex_number=dex)

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


    def _render_itemdex(self) -> None:
        source_order = {'Shop': 0, 'NPC Event or Dialogue': 1, 'Overworld': 2, 'Hidden Item': 3}
        rows = []
        for item in sorted(self.model.items.values(), key=lambda i: i.name):
            if not item.locations:
                continue
            ordered_locations = sorted(
                item.locations,
                key=lambda loc: (source_order.get(loc.source, 999), loc.location),
            )
            previous_source = None
            for index, loc in enumerate(ordered_locations):
                rows.append({
                    'name': item.name if index == 0 else '',
                    'location': loc.location,
                    'source': loc.source if loc.source != previous_source else '',
                    'item_id': item.item_id,
                    'search_name': item.name,
                    'search_source': loc.source,
                })
                previous_source = loc.source
        self._render('itemdex_index.html', 'itemdex/index.html', items=rows)

    def _render_trainerdex(self) -> None:
        trainers = sorted(self.model.trainers.values(), key=lambda t: t.name)
        self._render('trainerdex_index.html', 'trainerdex/index.html', trainers=trainers)
        for trainer in self.progress.iter(trainers, 'trainer pages', every=25, detail=lambda t: t.name):
            self._render('trainer.html', self._trainer_slug_path(trainer), trainer=trainer)

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

    def _should_process_transparent_sprite(self, rel: Path) -> bool:
        rel_posix = rel.as_posix().lower()
        if not rel_posix.endswith('.png'):
            return False
        return rel_posix.startswith('graphics/pokemon/')

    def _should_crop_top_half(self, rel: Path) -> bool:
        rel_posix = rel.as_posix().lower()
        if not rel_posix.endswith('.png'):
            return False
        if not rel_posix.startswith('graphics/pokemon/'):
            return False
        name = rel.name.lower()
        return name in {'anim_front.png', 'front_anim.png'}

    def _load_binary_palette(self, palette_path: Path) -> list[int] | None:
        suffix = palette_path.suffix.lower()
        if suffix != '.pal':
            return None
        data = palette_path.read_bytes()
        if not data:
            return None
        if data.startswith(b'JASC-PAL'):
            lines = [line.strip() for line in data.decode('utf-8', errors='ignore').splitlines() if line.strip()]
            try:
                count = int(lines[2])
                entries = [tuple(map(int, line.split()[:3])) for line in lines[3:3 + count]]
            except Exception:
                return None
            flat: list[int] = []
            for r, g, b in entries:
                flat.extend((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
            return flat
        if len(data) % 2 != 0:
            return None
        flat: list[int] = []
        for i in range(0, len(data), 2):
            value = struct.unpack_from('<H', data, i)[0]
            r = (value & 0x1F) * 255 // 31
            g = ((value >> 5) & 0x1F) * 255 // 31
            b = ((value >> 10) & 0x1F) * 255 // 31
            flat.extend((r, g, b))
        return flat

    def _find_source_palette_for_sprite(self, source_path: Path, target_palette_path: Path | None) -> Path | None:
        candidates: list[Path] = []
        seen: set[Path] = set()
        target_resolved = target_palette_path.resolve() if target_palette_path is not None else None

        def add(path: Path | None, *, allow_target: bool = False) -> None:
            if path is None:
                return
            path = path.resolve()
            if not allow_target and target_resolved is not None and path == target_resolved:
                return
            if path in seen:
                return
            seen.add(path)
            candidates.append(path)

        source_parent = source_path.parent.resolve()
        if target_palette_path is not None:
            target_parent = target_palette_path.parent.resolve()
            if source_parent == target_parent:
                prefix = f"{source_parent.name.lower()}_"
                target_stem = target_palette_path.stem.lower()
                if target_stem.startswith(prefix):
                    add(source_parent / f"{source_parent.name.lower()}_default.pal")
                    add(source_parent / f"{source_parent.name.lower()}_normal.pal")
                    # Same-folder variant palettes (notably Alcremie) still need a source
                    # palette for RGBA quantization. For *_default targets, the target
                    # palette itself is the correct source reference.
                    if target_stem.endswith('_default'):
                        add(target_palette_path, allow_target=True)

        for directory in (source_path.parent, *source_path.parent.parents):
            for name in ('normal.pal', 'palette.pal'):
                add(directory / name)
            if directory.name == 'graphics':
                break

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
        return None

    def _palette_image_from_flat(self, palette: list[int]) -> 'Image.Image':
        Image = _load_pillow_image_module()
        pal_img = Image.new('P', (1, 1))
        padded = list(palette[:768])
        if len(padded) < 768:
            padded.extend([0] * (768 - len(padded)))
        pal_img.putpalette(padded)
        return pal_img

    def _padded_palette(self, palette: list[int] | None) -> list[int]:
        padded = list((palette or [])[:768])
        if len(padded) < 768:
            padded.extend([0] * (768 - len(padded)))
        return padded

    def _palette_triplets(self, palette: list[int] | None) -> list[tuple[int, int, int]]:
        padded = self._padded_palette(palette)
        return [tuple(padded[i:i + 3]) for i in range(0, 768, 3)]

    def _remap_paletted_image_to_source_palette(self, image: 'Image.Image', source_palette: list[int]) -> 'Image.Image':
        current_palette = self._padded_palette(list(image.getpalette() or []))
        current_triplets = [tuple(current_palette[i:i + 3]) for i in range(0, 768, 3)]
        source_triplets = self._palette_triplets(source_palette)
        source_entry_count = max(1, min(256, len(source_palette) // 3))

        exact_index: dict[tuple[int, int, int], int] = {}
        for idx, color in enumerate(source_triplets[:source_entry_count]):
            exact_index.setdefault(color, idx)

        mapping: list[int] = []
        for idx, color in enumerate(current_triplets):
            if idx >= source_entry_count:
                mapping.append(idx)
                continue
            if color in exact_index:
                mapping.append(exact_index[color])
                continue
            best_idx = idx
            best_dist = None
            for src_idx, candidate in enumerate(source_triplets[:source_entry_count]):
                dist = ((color[0] - candidate[0]) ** 2) + ((color[1] - candidate[1]) ** 2) + ((color[2] - candidate[2]) ** 2)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_idx = src_idx
            mapping.append(best_idx)

        pal_image = image.copy()
        pixel_data = list(pal_image.getdata())
        remapped_data = [mapping[pixel] if 0 <= pixel < len(mapping) else pixel for pixel in pixel_data]
        pal_image.putdata(remapped_data)
        merged_palette = current_palette[:]
        source_padded = self._padded_palette(source_palette)
        replace_len = min(len(source_palette), len(merged_palette))
        merged_palette[:replace_len] = source_padded[:replace_len]
        pal_image.putpalette(merged_palette)
        transparency = image.info.get('transparency')
        if transparency is not None:
            if isinstance(transparency, (bytes, bytearray)):
                pal_image.info['transparency'] = transparency
            elif isinstance(transparency, int):
                pal_image.info['transparency'] = mapping[transparency] if 0 <= transparency < len(mapping) else transparency
        return pal_image

    def _recolor_rgba_with_palettes(self, image: 'Image.Image', source_palette: list[int], target_palette: list[int]) -> 'Image.Image':
        rgba = image.convert('RGBA')
        alpha = rgba.getchannel('A')
        source_pal_img = self._palette_image_from_flat(source_palette)
        indexed = rgba.convert('RGB').quantize(palette=source_pal_img, dither=0)
        target_pal_img = indexed.copy()
        padded = list(target_palette[:768])
        if len(padded) < 768:
            padded.extend([0] * (768 - len(padded)))
        target_pal_img.putpalette(padded)
        recolored = target_pal_img.convert('RGBA')
        recolored.putalpha(alpha)
        return recolored

    def _apply_palette_to_png(self, image: 'Image.Image', palette_path: Path | None, source_path: Path | None = None) -> 'Image.Image':
        if palette_path is None or not palette_path.exists() or not palette_path.is_file():
            return image
        target_palette = self._load_binary_palette(palette_path)
        if not target_palette:
            return image

        source_palette_path = self._find_source_palette_for_sprite(source_path or palette_path, palette_path) if source_path else None
        source_palette = self._load_binary_palette(source_palette_path) if source_palette_path else None

        if image.mode == 'P':
            pal_image = image.copy()
            if source_palette:
                pal_image = self._remap_paletted_image_to_source_palette(pal_image, source_palette)
            current_palette = self._padded_palette(list(pal_image.getpalette() or []))
            replacement = self._padded_palette(target_palette)
            replace_len = min(len(target_palette), len(current_palette))
            current_palette[:replace_len] = replacement[:replace_len]
            pal_image.putpalette(current_palette[:768])
            transparency = pal_image.info.get('transparency', image.info.get('transparency'))
            if transparency is not None:
                pal_image.info['transparency'] = transparency
            return pal_image

        if source_palette:
            return self._recolor_rgba_with_palettes(image, source_palette, target_palette)
        return image

    def _make_png_background_transparent(self, image: 'Image.Image') -> 'Image.Image':
        rgba = image.convert('RGBA')
        width, height = rgba.size
        if width <= 0 or height <= 0:
            return rgba
        bg = rgba.getpixel((0, 0))
        px = rgba.load()
        for y in range(height):
            for x in range(width):
                cur = px[x, y]
                if cur[:3] == bg[:3]:
                    px[x, y] = (cur[0], cur[1], cur[2], 0)
        return rgba

    def _palette_variant_rel(self, rel: Path, palette_source: str | None) -> Path:
        if not palette_source:
            return rel
        palette_rel = Path(str(palette_source).replace('\\', '/'))
        rel_posix = rel.as_posix().lower()
        palette_parent = palette_rel.parent
        if rel_posix.startswith('graphics/pokemon/') and palette_parent.as_posix().lower().startswith('graphics/pokemon/'):
            if palette_parent != rel.parent:
                return palette_parent / rel.name
            palette_stem = palette_rel.stem.lower()
            parent_name = rel.parent.name.lower()
            prefix = f"{parent_name}_"
            if palette_stem.startswith(prefix):
                variant_slug = re.sub(r'[^a-z0-9_]+', '_', palette_stem[len(prefix):].lower()).strip('_') or 'variant'
                return rel.parent / variant_slug / rel.name
        palette_key = safe_filename_slug(palette_rel.with_suffix('').as_posix()) or 'palette'
        return rel.with_name(f"{rel.stem}__pal__{palette_key}{rel.suffix}")

    def _should_apply_palette_variant(self, resolved_rel: Path, palette_rel: str | None) -> bool:
        if not palette_rel:
            return False
        rel_posix = resolved_rel.as_posix().lower()
        if not rel_posix.startswith('graphics/pokemon/') or not rel_posix.endswith('.png'):
            return False
        palette_path = Path(str(palette_rel).replace('\\', '/'))
        if palette_path.suffix.lower() != '.pal':
            return False
        stem = palette_path.stem.lower()
        if 'shiny' in stem or 'shiny' in palette_path.as_posix().lower():
            return False
        if any(tok in stem for tok in ('4bpp', '1bpp', 'smol')) or any(tok in palette_path.as_posix().lower() for tok in ('4bpp', '1bpp', 'smol', '.gbapal')):
            return False
        # Shared-source recolors: palette lives in a different folder than the chosen sprite.
        if palette_path.parent != resolved_rel.parent:
            return True
        # Same-folder generated variants like Alcremie's pattern_default.pal / pattern_matcha_cream.pal.
        parent_name = resolved_rel.parent.name.lower()
        return stem.startswith(f"{parent_name}_")

    def _resolve_palette_sprite_source(self, source: Path, palette_path: Path | None) -> Path:
        if palette_path is None or not palette_path.exists() or not source.exists():
            return source
        if source.suffix.lower() != '.png':
            return source
        try:
            source_rel = source.relative_to(self.config.project_dir)
            palette_rel = palette_path.relative_to(self.config.project_dir)
        except ValueError:
            return source
        if not source_rel.as_posix().lower().startswith('graphics/pokemon/'):
            return source
        if not palette_rel.as_posix().lower().startswith('graphics/pokemon/'):
            return source

        preferred_names = [source.name]
        if source.name == 'anim_front.png':
            preferred_names.append('front.png')
        elif source.name == 'front.png':
            preferred_names.append('anim_front.png')

        seen: set[Path] = set()
        for directory in (palette_path.parent, *palette_path.parent.parents):
            if directory in seen:
                continue
            seen.add(directory)
            for filename in preferred_names:
                candidate = directory / filename
                if candidate.exists() and candidate.is_file():
                    return candidate
            if directory == self.config.project_dir:
                break
        return source

    def _process_png_asset(self, source: Path, rel: Path, target: Path, palette_source: str | None = None, *, apply_palette: bool = True) -> None:
        Image = _load_pillow_image_module()
        with Image.open(source) as img:
            processed = img.copy()
            if apply_palette and palette_source:
                palette_candidate = self.config.project_dir / str(palette_source).replace('\\', '/')
                processed = self._apply_palette_to_png(processed, palette_candidate, source)
            if self._should_crop_top_half(rel):
                crop_h = max(1, processed.height // 2)
                processed = processed.crop((0, 0, processed.width, crop_h))
            if self._should_process_transparent_sprite(rel):
                processed = self._make_png_background_transparent(processed)
            processed.save(target)

    def _copy_assets(self) -> None:
        assets_root = self.config.dist_dir / 'assets' / 'game'
        assets_root.mkdir(parents=True, exist_ok=True)
        cache = self._load_asset_cache()
        copied = set()
        copied_count = 0
        skipped_count = 0
        cache_entries = cache.get('files', {}) if isinstance(cache.get('files', {}), dict) else {}

        def copy_source_path(source: str | None, *, palette_source: str | None = None) -> str | None:
            nonlocal copied_count, skipped_count
            if not source:
                return source
            source_str = str(source).replace('\\', '/')
            candidate = self.config.project_dir / source_str
            if not candidate.exists() or not candidate.is_file():
                return source_str
            rel = Path(source_str)
            palette_rel = str(palette_source).replace('\\', '/') if palette_source else None
            palette_candidate = self.config.project_dir / palette_rel if palette_rel else None
            resolved_candidate = self._resolve_palette_sprite_source(candidate, palette_candidate) if (self.config.pillow_transparency and palette_rel) else candidate
            try:
                resolved_rel = resolved_candidate.relative_to(self.config.project_dir)
            except ValueError:
                resolved_rel = rel
            rel_posix = resolved_rel.as_posix().lower()
            source_palette_path = self._find_source_palette_for_sprite(resolved_candidate, palette_candidate) if (self.config.pillow_transparency and palette_candidate is not None and palette_candidate.exists() and palette_candidate.is_file()) else None
            should_apply_palette = bool(
                self.config.pillow_transparency
                and palette_candidate is not None
                and palette_candidate.exists()
                and palette_candidate.is_file()
                and self._should_apply_palette_variant(resolved_rel, palette_rel)
            )
            effective_rel = resolved_rel
            if should_apply_palette:
                effective_rel = self._palette_variant_rel(resolved_rel, palette_rel)
            target = assets_root / effective_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            source_stat = resolved_candidate.stat()
            palette_sig: dict[str, int | str | bool | None] = {'palette_source': palette_rel, 'resolved_source': resolved_rel.as_posix()}
            if palette_candidate and palette_candidate.exists() and palette_candidate.is_file():
                palette_stat = palette_candidate.stat()
                palette_sig.update({
                    'palette_size': int(palette_stat.st_size),
                    'palette_mtime_ns': int(getattr(palette_stat, 'st_mtime_ns', int(palette_stat.st_mtime * 1_000_000_000))),
                })
            transform_flags = {
                'pillow_transparency_enabled': bool(self.config.pillow_transparency),
                'png_transparency': bool(self.config.pillow_transparency and self._should_process_transparent_sprite(resolved_rel)),
                'crop_top_half': bool(self.config.pillow_transparency and self._should_crop_top_half(resolved_rel)),
                'palette_applied': bool(should_apply_palette),
                'transform_version': 7,
            }
            sig = {'size': int(source_stat.st_size), 'mtime_ns': int(getattr(source_stat, 'st_mtime_ns', int(source_stat.st_mtime * 1_000_000_000))), **transform_flags, **palette_sig}
            cache_key = f"{resolved_candidate}|{palette_rel or ''}"
            target_exists = target.exists() and target.is_file()
            if cache_key not in copied:
                if target_exists and cache_entries.get(cache_key) == sig:
                    skipped_count += 1
                else:
                    if self.config.pillow_transparency and rel_posix.endswith('.png') and (transform_flags['png_transparency'] or transform_flags['crop_top_half'] or transform_flags['palette_applied']):
                        self._process_png_asset(resolved_candidate, resolved_rel, target, palette_source=palette_rel, apply_palette=should_apply_palette)
                    else:
                        shutil.copy2(resolved_candidate, target)
                    copied_count += 1
                    cache_entries[cache_key] = sig
                copied.add(cache_key)
            return f'../assets/game/{effective_rel.as_posix()}'

        species_values = list(self.model.species.values())
        for species in self.progress.iter(species_values, 'asset copy', every=max(1, len(species_values) // 100) if species_values else 1, detail=lambda s: getattr(s, 'name', getattr(s, 'species_id', ''))):
            copied_graphics = {}
            display_graphics = self._display_graphics_for_species(species)
            for key, source in display_graphics.items():
                palette_source = display_graphics.get('palette') if key == 'frontPic' else None
                copied_graphics[key] = copy_source_path(source, palette_source=palette_source)
            species.graphics = copied_graphics

        for trainer in self.model.trainers.values():
            trainer.picture = copy_source_path(trainer.picture)
            for mon in trainer.pokemon:
                palette_source = None
                if mon.species_id and mon.species_id in self.model.species:
                    palette_source = self._display_graphics_for_species(self.model.species[mon.species_id]).get('palette')
                mon.picture = copy_source_path(mon.picture, palette_source=palette_source)

        cache['files'] = cache_entries
        self._save_asset_cache(cache)
        self.progress.info(f'Asset copy complete: {copied_count} copied, {skipped_count} reused from cache')
