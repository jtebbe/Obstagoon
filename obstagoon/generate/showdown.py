from __future__ import annotations

import json
import re
import shutil

from pathlib import Path as _PathForBuiltin

def _load_pillow_image_module():
    try:
        from PIL import Image as PILImage
    except ImportError as exc:
        raise RuntimeError(
            "--pillow-transparency was requested, but Pillow is not installed. Install it with 'python3 -m pip install Pillow' or omit --pillow-transparency."
        ) from exc
    return PILImage

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..model.schema import AbilityRecord, ItemRecord, MoveRecord, ObstagoonModel, SpeciesRecord
from .site import SiteGenerator

CUSTOM_SPECIES_NUM_START = 20000
CUSTOM_MOVE_NUM_START = 30000
CUSTOM_ABILITY_NUM_START = 40000
CUSTOM_ITEM_NUM_START = 50000
GEN = 9
RASTER_SUFFIXES = {'.png', '.webp', '.jpg', '.jpeg', '.gif'}
BUILTIN_CANONICAL_POKEDEX_PATH = _PathForBuiltin(__file__).resolve().parent.parent / 'data' / 'official_pokedex.ts'

FORME_CANONICAL_BY_ID = {
    '10': '10%',
    '2': '2',
    'alola': 'Alola',
    'alolatotem': 'Alola-Totem',
    'antique': 'Antique',
    'archipelago': 'Archipelago',
    'artisan': 'Artisan',
    'ash': 'Ash',
    'attack': 'Attack',
    'autumn': 'Autumn',
    'belle': 'Belle',
    'black': 'Black',
    'blade': 'Blade',
    'bloodmoon': 'Bloodmoon',
    'blue': 'Blue',
    'bluestriped': 'Blue-Striped',
    'bond': 'Bond',
    'bug': 'Bug',
    'burn': 'Burn',
    'busted': 'Busted',
    'bustedtotem': 'Busted-Totem',
    'caramelswirl': 'Caramel-Swirl',
    'chill': 'Chill',
    'complete': 'Complete',
    'continental': 'Continental',
    'cornerstone': 'Cornerstone',
    'cornerstonetera': 'Cornerstone-Tera',
    'cosplay': 'Cosplay',
    'crowned': 'Crowned',
    'curlymega': 'Curly-Mega',
    'dada': 'Dada',
    'dark': 'Dark',
    'dawnwings': 'Dawn-Wings',
    'defense': 'Defense',
    'douse': 'Douse',
    'dragon': 'Dragon',
    'droopy': 'Droopy',
    'droopymega': 'Droopy-Mega',
    'dusk': 'Dusk',
    'duskmane': 'Dusk-Mane',
    'east': 'East',
    'electric': 'Electric',
    'elegant': 'Elegant',
    'epilogue': 'Epilogue',
    'eternal': 'Eternal',
    'eternamax': 'Eternamax',
    'f': 'F',
    'fmega': 'F-Mega',
    'fairy': 'Fairy',
    'fan': 'Fan',
    'fancy': 'Fancy',
    'fighting': 'Fighting',
    'fire': 'Fire',
    'flying': 'Flying',
    'four': 'Four',
    'frost': 'Frost',
    'galar': 'Galar',
    'galarzen': 'Galar-Zen',
    'garden': 'Garden',
    'ghost': 'Ghost',
    'gmax': 'Gmax',
    'gorging': 'Gorging',
    'grass': 'Grass',
    'green': 'Green',
    'ground': 'Ground',
    'gulping': 'Gulping',
    'hangry': 'Hangry',
    'hearthflame': 'Hearthflame',
    'hearthflametera': 'Hearthflame-Tera',
    'heat': 'Heat',
    'hero': 'Hero',
    'highplains': 'High Plains',
    'hisui': 'Hisui',
    'hoenn': 'Hoenn',
    'ice': 'Ice',
    'icysnow': 'Icy Snow',
    'indigo': 'Indigo',
    'jungle': 'Jungle',
    'kalos': 'Kalos',
    'large': 'Large',
    'lemoncream': 'Lemon-Cream',
    'libre': 'Libre',
    'lowkey': 'Low-Key',
    'lowkeygmax': 'Low-Key-Gmax',
    'mmega': 'M-Mega',
    'marine': 'Marine',
    'masterpiece': 'Masterpiece',
    'matchacream': 'Matcha-Cream',
    'mega': 'Mega',
    'megax': 'Mega-X',
    'megay': 'Mega-Y',
    'megaz': 'Mega-Z',
    'meteor': 'Meteor',
    'midnight': 'Midnight',
    'mintcream': 'Mint-Cream',
    'modern': 'Modern',
    'monsoon': 'Monsoon',
    'mow': 'Mow',
    'neutral': 'Neutral',
    'noice': 'Noice',
    'ocean': 'Ocean',
    'orange': 'Orange',
    'origin': 'Origin',
    'original': 'Original',
    'originalmega': 'Original-Mega',
    'pau': "Pa'u",
    'paldea': 'Paldea',
    'paldeaaqua': 'Paldea-Aqua',
    'paldeablaze': 'Paldea-Blaze',
    'paldeacombat': 'Paldea-Combat',
    'partner': 'Partner',
    'phd': 'PhD',
    'pirouette': 'Pirouette',
    'poison': 'Poison',
    'pokeball': 'Pokeball',
    'polar': 'Polar',
    'pompom': 'Pom-Pom',
    'popstar': 'Pop-Star',
    'primal': 'Primal',
    'propu2': 'PropU2',
    'psychic': 'Psychic',
    'radiant': 'Radiant',
    'rainbowswirl': 'Rainbow-Swirl',
    'rainy': 'Rainy',
    'rapidstrike': 'Rapid-Strike',
    'rapidstrikegmax': 'Rapid-Strike-Gmax',
    'resolute': 'Resolute',
    'river': 'River',
    'roaming': 'Roaming',
    'rock': 'Rock',
    'rockstar': 'Rock-Star',
    'rubycream': 'Ruby-Cream',
    'rubyswirl': 'Ruby-Swirl',
    'sandstorm': 'Sandstorm',
    'sandy': 'Sandy',
    'savanna': 'Savanna',
    'school': 'School',
    'sensu': 'Sensu',
    'shadow': 'Shadow',
    'shock': 'Shock',
    'sinnoh': 'Sinnoh',
    'sky': 'Sky',
    'small': 'Small',
    'snowy': 'Snowy',
    'speed': 'Speed',
    'spikyeared': 'Spiky-eared',
    'starter': 'Starter',
    'steel': 'Steel',
    'stellar': 'Stellar',
    'stretchy': 'Stretchy',
    'stretchymega': 'Stretchy-Mega',
    'summer': 'Summer',
    'sun': 'Sun',
    'sunny': 'Sunny',
    'sunshine': 'Sunshine',
    'super': 'Super',
    'tealtera': 'Teal-Tera',
    'terastal': 'Terastal',
    'therian': 'Therian',
    'threesegment': 'Three-Segment',
    'totem': 'Totem',
    'trash': 'Trash',
    'tundra': 'Tundra',
    'ultra': 'Ultra',
    'unbound': 'Unbound',
    'unova': 'Unova',
    'violet': 'Violet',
    'wash': 'Wash',
    'water': 'Water',
    'wellspring': 'Wellspring',
    'wellspringtera': 'Wellspring-Tera',
    'white': 'White',
    'whitestriped': 'White-Striped',
    'winter': 'Winter',
    'world': 'World',
    'yellow': 'Yellow',
    'zen': 'Zen',
}

CANONICAL_CAN_GIGANTAMAX = {
    'Venusaur': 'G-Max Vine Lash',
    'Charizard': 'G-Max Wildfire',
    'Blastoise': 'G-Max Cannonade',
    'Butterfree': 'G-Max Befuddle',
    'Pikachu': 'G-Max Volt Crash',
    'Meowth': 'G-Max Gold Rush',
    'Machamp': 'G-Max Chi Strike',
    'Gengar': 'G-Max Terror',
    'Kingler': 'G-Max Foam Burst',
    'Lapras': 'G-Max Resonance',
    'Eevee': 'G-Max Cuddle',
    'Snorlax': 'G-Max Replenish',
    'Garbodor': 'G-Max Malodor',
    'Melmetal': 'G-Max Meltdown',
    'Rillaboom': 'G-Max Drum Solo',
    'Cinderace': 'G-Max Fireball',
    'Inteleon': 'G-Max Hydrosnipe',
    'Corviknight': 'G-Max Wind Rage',
    'Orbeetle': 'G-Max Gravitas',
    'Drednaw': 'G-Max Stonesurge',
    'Coalossal': 'G-Max Volcalith',
    'Flapple': 'G-Max Tartness',
    'Appletun': 'G-Max Sweetness',
    'Sandaconda': 'G-Max Sandblast',
    'Toxtricity': 'G-Max Stun Shock',
    'Toxtricity-Low-Key': 'G-Max Stun Shock',
    'Centiskorch': 'G-Max Centiferno',
    'Hatterene': 'G-Max Smite',
    'Grimmsnarl': 'G-Max Snooze',
    'Alcremie': 'G-Max Finale',
    'Copperajah': 'G-Max Steelsurge',
    'Duraludon': 'G-Max Depletion',
    'Urshifu': 'G-Max One Blow',
    'Urshifu-Rapid-Strike': 'G-Max Rapid Flow',
}



@dataclass(slots=True)
class CanonicalSpecies:
    key: str
    num: int | None
    name: str
    base_species: str | None = None
    forme: str | None = None
    other_formes: list[str] = field(default_factory=list)
    forme_order: list[str] = field(default_factory=list)
    raw_fields: dict[str, Any] = field(default_factory=dict)


class CanonicalPokedex:
    def __init__(self, entries: dict[str, CanonicalSpecies]) -> None:
        self.entries = entries
        self.by_name = {entry.name: entry for entry in entries.values()}
        self.base_by_name = {entry.name: entry for entry in entries.values() if not entry.base_species}
        self.children_by_base: dict[str, list[CanonicalSpecies]] = {}
        for entry in entries.values():
            if entry.base_species:
                self.children_by_base.setdefault(entry.base_species, []).append(entry)
        for children in self.children_by_base.values():
            children.sort(key=lambda e: (e.num or 10**9, e.name))

    @classmethod
    def load(cls, path: Path | None) -> 'CanonicalPokedex | None':
        if not path or not path.exists():
            return None
        text = path.read_text(encoding='utf-8')
        marker = 'export const Pokedex'
        start = text.find(marker)
        if start < 0:
            return None
        brace_start = text.find('{', start)
        if brace_start < 0:
            return None
        brace_end = cls._find_matching_brace(text, brace_start)
        if brace_end < 0:
            return None
        body = text[brace_start + 1:brace_end]
        entries: dict[str, CanonicalSpecies] = {}
        i = 0
        while i < len(body):
            while i < len(body) and body[i].isspace():
                i += 1
            if i >= len(body):
                break
            key_match = re.match(r'([A-Za-z0-9_]+)\s*:\s*{', body[i:])
            if not key_match:
                i += 1
                continue
            key = key_match.group(1)
            entry_brace = i + key_match.end() - 1
            entry_end = cls._find_matching_brace(body, entry_brace)
            if entry_end < 0:
                break
            block = body[entry_brace + 1:entry_end]
            fields = cls._parse_selected_fields(block)
            name = fields.get('name') or key
            entries[key] = CanonicalSpecies(
                key=key,
                num=fields.get('num'),
                name=name,
                base_species=fields.get('baseSpecies'),
                forme=fields.get('forme'),
                other_formes=fields.get('otherFormes') or [],
                forme_order=fields.get('formeOrder') or [],
                raw_fields=fields,
            )
            i = entry_end + 1
        return cls(entries)

    @staticmethod
    def _find_matching_brace(text: str, start: int) -> int:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
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
                    return i
        return -1

    @classmethod
    def _parse_selected_fields(cls, block: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        m = re.search(r'\bnum:\s*(\d+)', block)
        if m:
            out['num'] = int(m.group(1))
        for field_name in ('name', 'baseSpecies', 'forme'):
            m = re.search(rf'\b{field_name}:\s*"((?:[^"\\]|\\.)*)"', block)
            if m:
                out[field_name] = bytes(m.group(1), 'utf-8').decode('unicode_escape')
        for field_name in ('otherFormes', 'formeOrder'):
            m = re.search(rf'\b{field_name}:\s*\[(.*?)\]', block, re.S)
            if m:
                out[field_name] = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
        return out

@dataclass(slots=True)
class ShowdownSpecies:
    key: str
    display_name: str
    num: int
    record: SpeciesRecord
    base_key: str | None
    forme: str | None
    is_cosmetic: bool
    aliases: set[str]
    canonical: CanonicalSpecies | None = None


class ShowdownExportGenerator:
    def __init__(self, config, model: ObstagoonModel) -> None:
        self.config = config
        self.model = model
        self.output_dir = (config.showdown_export_dir or (config.dist_dir.parent / 'showdown-export')).resolve()
        self.server_dir = self.output_dir / 'server'
        self.client_dir = self.output_dir / 'client'
        self._custom_species_counter = CUSTOM_SPECIES_NUM_START
        self._custom_move_counter = CUSTOM_MOVE_NUM_START
        self._custom_ability_counter = CUSTOM_ABILITY_NUM_START
        self._custom_item_counter = CUSTOM_ITEM_NUM_START
        self._species_entries: dict[str, ShowdownSpecies] = {}
        self._record_to_key: dict[str, str] = {}
        self._site_helper = SiteGenerator(config=config, model=model, env=None)
        canonical_path = getattr(config, 'showdown_canonical_pokedex_path', None) or BUILTIN_CANONICAL_POKEDEX_PATH
        self._canonical_pokedex = CanonicalPokedex.load(canonical_path)
        self._record_to_canonical: dict[str, CanonicalSpecies] = {}
        self._prevo_by_species_id: dict[str, str] = {}

    def run(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.config.verbose:
            print("\n" + "=" * 60)
            print("📦 SHOWDOWN EXPORT ENABLED")
            print(f"📁 Output Directory: {self.output_dir}")
            print("=" * 60 + "\n")
        self.server_dir.mkdir(parents=True, exist_ok=True)
        self.client_dir.mkdir(parents=True, exist_ok=True)
        self._build_species_entries()
        self._write_server_payload()
        self._write_client_payload()
        self._write_manifest()
        self._write_readme()
        if self.config.verbose:
            print(f"✅ Showdown export complete: {self.output_dir}")

    def _build_species_entries(self) -> None:
        key_by_base: dict[str, str] = {}
        self._prevo_by_species_id = {}
        for rec in self.model.species.values():
            for evo in rec.evolutions:
                target_id = getattr(evo, 'target_species_id', None) or evo.target_species
                if target_id and target_id != 'SPECIES_NONE' and target_id not in self._prevo_by_species_id:
                    self._prevo_by_species_id[target_id] = rec.species_id
        for species_id, rec in self._species_records_in_export_order():
            if rec.base_species:
                continue
            canonical = self._canonical_match_base(rec)
            display_name = canonical.name if canonical else rec.name
            key = canonical.key if canonical else self._unique_species_key(self._to_id(display_name), species_id)
            num = canonical.num if canonical and canonical.num is not None else rec.national_dex or self._next_custom_species_num()
            aliases = self._species_aliases(rec, display_name, canonical=canonical)
            entry = ShowdownSpecies(
                key=key,
                display_name=display_name,
                num=num,
                record=rec,
                base_key=None,
                forme=canonical.forme if canonical else None,
                is_cosmetic=False,
                aliases=aliases,
                canonical=canonical,
            )
            self._species_entries[key] = entry
            self._record_to_key[species_id] = key
            key_by_base[species_id] = key
            if canonical:
                self._record_to_canonical[species_id] = canonical

        for species_id, rec in self._species_records_in_export_order():
            if not rec.base_species:
                continue
            base_rec = self.model.species.get(rec.base_species)
            if not base_rec:
                continue
            base_key = key_by_base.get(base_rec.species_id)
            if not base_key:
                continue
            canonical = self._canonical_match_form(rec, base_rec)
            forme = canonical.forme if canonical else self._normalize_forme_name(rec, base_rec)
            display_name = canonical.name if canonical else self._display_form_species_name(rec, base_rec, forme)
            key = canonical.key if canonical else self._unique_species_key(self._to_id(display_name), species_id)
            is_cosmetic = False if canonical else self._is_cosmetic_form(rec, base_rec, forme)
            aliases = self._species_aliases(rec, display_name, canonical=canonical)
            entry = ShowdownSpecies(
                key=key,
                display_name=display_name,
                num=canonical.num if canonical and canonical.num is not None else self._species_entries[base_key].num,
                record=rec,
                base_key=base_key,
                forme=forme,
                is_cosmetic=is_cosmetic,
                aliases=aliases,
                canonical=canonical,
            )
            self._species_entries[key] = entry
            self._record_to_key[species_id] = key
            if canonical:
                self._record_to_canonical[species_id] = canonical

    def _write_server_payload(self) -> None:
        mod_dir = self.server_dir / 'data' / 'mods' / 'obstagoon'
        mod_dir.mkdir(parents=True, exist_ok=True)
        (self.server_dir / 'config').mkdir(parents=True, exist_ok=True)
        self._write_text(mod_dir / 'scripts.ts', self._render_scripts_ts())
        self._write_text(mod_dir / 'pokedex.ts', self._render_pokedex_ts())
        self._write_text(mod_dir / 'learnsets.ts', self._render_learnsets_ts())
        self._write_text(mod_dir / 'moves.ts', self._render_moves_ts())
        self._write_text(mod_dir / 'abilities.ts', self._render_abilities_ts())
        self._write_text(mod_dir / 'items.ts', self._render_items_ts())
        self._write_text(mod_dir / 'formats-data.ts', self._render_formats_data_ts())
        self._write_text(mod_dir / 'aliases.ts', self._render_aliases_ts())
        self._write_text(self.server_dir / 'data' / 'aliases.obstagoon.generated.ts', self._render_root_aliases_ts())
        self._write_text(self.server_dir / 'config' / 'formats.obstagoon.generated.ts', self._render_formats_ts())
        self._write_text(self.server_dir / 'README.md', self._render_server_readme())

    def _write_client_payload(self) -> None:
        (self.client_dir / 'build-tools').mkdir(parents=True, exist_ok=True)
        (self.client_dir / 'assets' / 'pokemon').mkdir(parents=True, exist_ok=True)
        (self.client_dir / 'assets' / 'icons').mkdir(parents=True, exist_ok=True)
        self._write_text(self.client_dir / 'build-tools' / 'build-indexes.obstagoon.js', self._render_client_build_script())
        self._write_text(self.client_dir / 'README.md', self._render_client_readme())
        copied_assets = self._copy_client_assets()
        self._write_text(
            self.client_dir / 'assets' / 'manifest.json',
            json.dumps(copied_assets, indent=2, sort_keys=True),
        )

    def _write_manifest(self) -> None:
        manifest = {
            'format': 'pokemon-showdown-obstagoon-export',
            'version': 1,
            'parent_mod': 'gen9',
            'server_dir': str(self.server_dir.relative_to(self.output_dir)),
            'client_dir': str(self.client_dir.relative_to(self.output_dir)),
            'species_entries': len(self._species_entries),
            'included_species': sum(1 for entry in self._species_entries.values() if not entry.is_cosmetic),
            'cosmetic_forms_aliased': sum(1 for entry in self._species_entries.values() if entry.is_cosmetic),
            'moves': len(self.model.moves),
            'abilities': len(self.model.abilities),
            'items': len(self.model.items),
            'custom_species_num_start': CUSTOM_SPECIES_NUM_START,
            'custom_move_num_start': CUSTOM_MOVE_NUM_START,
            'custom_ability_num_start': CUSTOM_ABILITY_NUM_START,
            'custom_item_num_start': CUSTOM_ITEM_NUM_START,
        }
        self._write_text(self.output_dir / 'manifest.json', json.dumps(manifest, indent=2, sort_keys=True))

    def _write_readme(self) -> None:
        text = (
            '# Obstagoon Showdown export\n\n'
            'This directory contains a generated Pokémon Showdown server-mod payload and a client-fork payload.\n\n'
            '- `server/` contains `data/mods/obstagoon/*` and generated format definitions.\n'
            '- `client/` contains a build-indexes helper and copied sprite/icon assets for teambuilder integration.\n\n'
            'The generated mod inherits from `gen9` and only exports teachable learnsets for this custom ruleset.\n'
        )
        self._write_text(self.output_dir / 'README.md', text)


    def _species_records_in_export_order(self) -> list[tuple[str, SpeciesRecord]]:
        def sort_key(item: tuple[str, SpeciesRecord]) -> tuple[int, int, int, str]:
            species_id, rec = item
            num = rec.national_dex if rec.national_dex is not None else 10**9 + rec.form_index if rec.form_index is not None else 10**9
            is_form = 1 if rec.base_species else 0
            form_index = rec.form_index if rec.form_index is not None else 0
            return (num, is_form, form_index, species_id)
        return sorted(self.model.species.items(), key=sort_key)

    def _species_entries_in_export_order(self) -> list[tuple[str, ShowdownSpecies]]:
        def sort_key(item: tuple[str, ShowdownSpecies]) -> tuple[int, int, int, str]:
            key, entry = item
            num = entry.num if entry.record.national_dex is not None else 10**9 + entry.num
            is_form = 1 if entry.base_key else 0
            form_index = entry.record.form_index if entry.record.form_index is not None else 0
            return (num, is_form, form_index, key)
        return sorted(self._species_entries.items(), key=sort_key)

    def _render_scripts_ts(self) -> str:
        return (
            '/**\n'
            ' * Generated by Obstagoon.\n'
            ' */\n'
            "export const Scripts: import('../../../sim/dex').ModdedBattleScriptsData = {\n"
            "\tinherit: 'gen9',\n"
            f'\tgen: {GEN},\n'
            '};\n'
        )

    def _render_pokedex_ts_generic(self) -> str:
        lines = [
            '/**',
            ' * Generated by Obstagoon.',
            ' */',
            "export const Pokedex: import('../../../sim/dex-species').ModdedSpeciesDataTable = {",
        ]
        base_children: dict[str, list[ShowdownSpecies]] = {}
        for entry in self._species_entries.values():
            if entry.base_key:
                base_children.setdefault(entry.base_key, []).append(entry)
        for key, entry in self._species_entries_in_export_order():
            if entry.is_cosmetic:
                continue
            record = entry.record
            base_stats = self._species_base_stats(record)
            abilities = self._species_abilities(record)
            canonical = entry.canonical
            fields: list[tuple[str, Any]] = [
                ('num', entry.num),
                ('name', canonical.name if canonical else entry.display_name),
                ('types', record.types[:2] or ['Normal']),
                ('baseStats', base_stats),
                ('abilities', abilities),
                ('weightkg', self._species_weightkg(record)),
                ('heightm', self._species_heightm(record)),
            ]
            if record.category:
                fields.append(('species', record.category))
            if record.description:
                fields.append(('desc', record.description))
            egg_groups = record.egg_groups[:2]
            if egg_groups:
                fields.append(('eggGroups', egg_groups))
            gender = self._normalize_gender(record.gender_ratio)
            if gender:
                fields.append(('gender', gender))
            elif record.gender_ratio:
                ratio = self._parse_gender_ratio(record.gender_ratio)
                if ratio:
                    fields.append(('genderRatio', ratio))
            if entry.base_key:
                base_species_name = canonical.raw_fields.get('baseSpecies') if canonical else self._species_entries[entry.base_key].display_name
                if base_species_name:
                    fields.append(('baseSpecies', base_species_name))
                forme_name = canonical.raw_fields.get('forme') if canonical else entry.forme
                if forme_name:
                    fields.append(('forme', forme_name))
                required_item = self._required_item_for_form(entry)
                if required_item:
                    fields.append(('requiredItem', required_item))
                required_ability = self._required_ability_for_form(entry)
                if required_ability:
                    fields.append(('requiredAbility', required_ability))
                battle_only = self._battle_only_for_form(entry)
                if battle_only:
                    fields.append(('battleOnly', battle_only))
                changes_from = self._changes_from_for_form(entry)
                if changes_from:
                    fields.append(('changesFrom', changes_from))
            child_forms = [child for child in base_children.get(key, []) if not child.is_cosmetic and not self._is_gigantamax_form(child)]
            can_gigantamax = self._can_gigantamax_for_base(entry) if not entry.base_key else None
            if can_gigantamax:
                fields.append(('canGigantamax', can_gigantamax))
            if canonical and canonical.other_formes:
                available_names = {child.display_name for child in child_forms}
                ordered_other = [name for name in canonical.other_formes if name in available_names]
                if ordered_other:
                    fields.append(('otherFormes', ordered_other))
                    forme_order = [name for name in canonical.forme_order if name == entry.display_name or name in available_names]
                    if not forme_order:
                        forme_order = [entry.display_name, *ordered_other]
                    fields.append(('formeOrder', forme_order))
            elif child_forms:
                child_forms.sort(key=lambda child: ((child.record.form_index if child.record.form_index is not None else 10**9), child.key))
                fields.append(('otherFormes', [child.display_name for child in child_forms]))
                fields.append(('formeOrder', [entry.display_name, *[child.display_name for child in child_forms]]))
            if entry.is_cosmetic:
                fields.append(('isCosmeticForme', True))
            rendered = ',\n'.join(f'\t\t{field}: {self._ts(value)}' for field, value in fields)
            lines.append(f"\t{self._quote_key(key)}: {{\n{rendered}\n\t}},")
        lines.append('};')
        return '\n'.join(lines) + '\n'

    def _render_pokedex_ts(self) -> str:
        if self._canonical_pokedex and BUILTIN_CANONICAL_POKEDEX_PATH.exists():
            return self._render_exact_pokedex_ts()
        return self._render_pokedex_ts_generic()

    def _render_exact_pokedex_ts(self) -> str:
        template_text = BUILTIN_CANONICAL_POKEDEX_PATH.read_text(encoding='utf-8')
        template_text = template_text.replace("import('../sim/dex-species').SpeciesDataTable", "import('../../../sim/dex-species').ModdedSpeciesDataTable", 1)
        entry_ranges = self._parse_top_level_entry_ranges(template_text)
        replacements: list[tuple[int, int, str]] = []
        seen_keys: set[str] = set()
        for key, entry in self._species_entries_in_export_order():
            if entry.is_cosmetic:
                continue
            if key in entry_ranges:
                start, end = entry_ranges[key]
                original = template_text[start:end]
                replacements.append((start, end, self._overlay_species_entry_block(original, entry)))
                seen_keys.add(key)
        pieces: list[str] = []
        cursor = 0
        for start, end, replacement in sorted(replacements, key=lambda x: x[0]):
            pieces.append(template_text[cursor:start])
            pieces.append(replacement)
            cursor = end
        pieces.append(template_text[cursor:])
        rendered = ''.join(pieces)

        extra_entries: list[str] = []
        for key, entry in self._species_entries_in_export_order():
            if entry.is_cosmetic or key in entry_ranges:
                continue
            extra_entries.append(self._render_custom_species_entry_block(key, entry))
        if extra_entries:
            rendered = rendered.rstrip()
            if rendered.endswith('};'):
                rendered = rendered[:-2]
                if not rendered.endswith('\n'):
                    rendered += '\n'
                rendered += ''.join(extra_entries)
                rendered += '};\n'
        return rendered

    def _parse_top_level_entry_ranges(self, text: str) -> dict[str, tuple[int, int]]:
        marker = 'export const Pokedex'
        start = text.find(marker)
        if start < 0:
            return {}
        brace_start = text.find('{', start)
        brace_end = CanonicalPokedex._find_matching_brace(text, brace_start)
        body_start = brace_start + 1
        body_end = brace_end
        body = text[body_start:body_end]
        ranges: dict[str, tuple[int, int]] = {}
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
            entry_end = CanonicalPokedex._find_matching_brace(body, entry_brace)
            if entry_end < 0:
                break
            j = entry_end + 1
            while j < len(body) and body[j].isspace():
                j += 1
            if j < len(body) and body[j] == ',':
                j += 1
            if j < len(body) and body[j] == '\n':
                j += 1
            ranges[key] = (body_start + entry_start, body_start + j)
            i = j
        return ranges

    def _overlay_species_entry_block(self, block: str, entry: ShowdownSpecies) -> str:
        updated = block
        for field, value in self._overlayable_species_fields(entry).items():
            updated = self._replace_ts_field(updated, field, self._ts(value), insert_missing=False)
        return updated

    def _replace_ts_field(self, block: str, field: str, value_ts: str, *, insert_missing: bool = True) -> str:
        pattern = rf'(^\t\t{re.escape(field)}:\s*)(.*?)(,\n)'
        new_block, count = re.subn(pattern, lambda m: f"{m.group(1)}{value_ts}{m.group(3)}", block, count=1, flags=re.M)
        if count or not insert_missing:
            return new_block if count else block
        insert_after = re.search(r'(^\t\tname:\s*.*?,\n)', block, flags=re.M)
        if insert_after:
            idx = insert_after.end()
            return block[:idx] + f'\t\t{field}: {value_ts},\n' + block[idx:]
        open_brace = block.find('{\n')
        if open_brace >= 0:
            idx = open_brace + 2
            return block[:idx] + f'\t\t{field}: {value_ts},\n' + block[idx:]
        return block

    def _overlayable_species_fields(self, entry: ShowdownSpecies) -> dict[str, Any]:
        record = entry.record
        values: dict[str, Any] = {
            'name': entry.canonical.name if entry.canonical else entry.display_name,
            'types': record.types[:2] or ['Normal'],
            'baseStats': self._species_base_stats(record),
            'abilities': self._species_abilities(record),
            'weightkg': self._species_weightkg(record),
            'heightm': self._species_heightm(record),
        }
        if record.category:
            values['species'] = record.category
        if record.description:
            values['desc'] = record.description
            values['shortDesc'] = record.description
        egg_groups = record.egg_groups[:2]
        if egg_groups:
            values['eggGroups'] = egg_groups
        gender = self._normalize_gender(record.gender_ratio)
        if gender:
            values['gender'] = gender
        elif record.gender_ratio:
            ratio = self._parse_gender_ratio(record.gender_ratio)
            if ratio:
                values['genderRatio'] = ratio
        prevo_name = self._prevo_name_for_species(entry)
        if prevo_name:
            values['prevo'] = prevo_name
        evos = self._evos_for_species(entry)
        if evos:
            values['evos'] = evos
        values.update(self._evolution_fields_for_species(entry))
        if entry.base_key:
            base_species_name = entry.canonical.raw_fields.get('baseSpecies') if entry.canonical else self._species_entries[entry.base_key].display_name
            if base_species_name:
                values['baseSpecies'] = base_species_name
            forme_name = entry.canonical.raw_fields.get('forme') if entry.canonical else entry.forme
            if forme_name:
                values['forme'] = forme_name
            required_item = self._required_item_for_form(entry)
            if required_item:
                values['requiredItem'] = required_item
            required_ability = self._required_ability_for_form(entry)
            if required_ability:
                values['requiredAbility'] = required_ability
            battle_only = self._battle_only_for_form(entry)
            if battle_only:
                values['battleOnly'] = battle_only
            changes_from = self._changes_from_for_form(entry)
            if changes_from:
                values['changesFrom'] = changes_from
        can_gigantamax = self._can_gigantamax_for_base(entry) if not entry.base_key else None
        if can_gigantamax:
            values['canGigantamax'] = can_gigantamax
        if entry.canonical and entry.canonical.other_formes:
            base_children: dict[str, list[ShowdownSpecies]] = {}
            for child in self._species_entries.values():
                if child.base_key:
                    base_children.setdefault(child.base_key, []).append(child)
            child_forms = [child for child in base_children.get(entry.key, []) if not child.is_cosmetic and not self._is_gigantamax_form(child)]
            available_names = {child.display_name for child in child_forms}
            ordered_other = [name for name in entry.canonical.other_formes if name in available_names]
            if ordered_other:
                values['otherFormes'] = ordered_other
                forme_order = [name for name in entry.canonical.forme_order if name == entry.display_name or name in available_names]
                if forme_order:
                    values['formeOrder'] = forme_order
        return values

    def _prevo_name_for_species(self, entry: ShowdownSpecies) -> str | None:
        prevo_id = self._prevo_by_species_id.get(entry.record.species_id)
        if not prevo_id:
            return None
        prevo_key = self._record_to_key.get(prevo_id)
        prevo_entry = self._species_entries.get(prevo_key) if prevo_key else None
        return prevo_entry.display_name if prevo_entry else None

    def _evos_for_species(self, entry: ShowdownSpecies) -> list[str]:
        names: list[str] = []
        for evo in entry.record.evolutions:
            target_id = getattr(evo, 'target_species_id', None) or evo.target_species
            target_key = self._record_to_key.get(target_id)
            target_entry = self._species_entries.get(target_key) if target_key else None
            if target_entry and not target_entry.is_cosmetic:
                names.append(target_entry.display_name)
        seen: set[str] = set()
        ordered: list[str] = []
        for name in names:
            if name not in seen:
                seen.add(name)
                ordered.append(name)
        return ordered

    def _evolution_fields_for_species(self, entry: ShowdownSpecies) -> dict[str, Any]:
        prevo_id = self._prevo_by_species_id.get(entry.record.species_id)
        if not prevo_id:
            return {}
        prevo = self.model.species.get(prevo_id)
        if not prevo:
            return {}
        for evo in prevo.evolutions:
            target_id = getattr(evo, 'target_species_id', None) or evo.target_species
            if target_id == entry.record.species_id:
                return self._map_evolution_to_showdown_fields(evo.method, evo.param)
        return {}

    def _map_evolution_to_showdown_fields(self, method: str | None, param: str | None) -> dict[str, Any]:
        method = str(method or '').strip()
        out: dict[str, Any] = {}
        if method == 'EVO_LEVEL':
            level = self._safe_int(param, default=0)
            if level:
                out['evoLevel'] = level
        elif method == 'EVO_ITEM':
            out['evoType'] = 'useItem'
            item_name = self._item_name(param) if param else None
            if item_name:
                out['evoItem'] = item_name
        elif method == 'EVO_TRADE':
            out['evoType'] = 'trade'
            item_name = self._item_name(param) if param else None
            if item_name and item_name != '0':
                out['evoItem'] = item_name
        elif method == 'EVO_FRIENDSHIP':
            out['evoType'] = 'levelFriendship'
        elif method == 'EVO_MOVE':
            out['evoType'] = 'levelMove'
            move_name = self._move_name(param) if param else None
            if move_name:
                out['evoMove'] = move_name
        elif method == 'EVO_MOVE_TYPE':
            out['evoType'] = 'levelExtra'
            type_name = self._type_name(param) if param else None
            if type_name:
                out['evoCondition'] = f'knowing a {type_name}-type move'
        elif method == 'EVO_LEVEL_DAY':
            level = self._safe_int(param, default=0)
            if level:
                out['evoLevel'] = level
            out['evoCondition'] = 'during the day'
        elif method == 'EVO_LEVEL_NIGHT':
            level = self._safe_int(param, default=0)
            if level:
                out['evoLevel'] = level
            out['evoCondition'] = 'at night'
        elif method == 'EVO_SPECIFIC_MON_IN_PARTY':
            out['evoType'] = 'levelExtra'
            species_name = self._species_name_from_symbol(param) if param else None
            if species_name:
                out['evoCondition'] = f'with {species_name} in party'
        elif method == 'EVO_SPECIFIC_MAP':
            out['evoType'] = 'levelExtra'
            map_name = self._map_name(param) if param else None
            if map_name:
                out['evoCondition'] = f'on {map_name}'
        return out

    def _move_name(self, move_symbol: str | None) -> str | None:
        move = self.model.moves.get(str(move_symbol or '').strip())
        if move:
            return move.name
        text = str(move_symbol or '').strip()
        if text.startswith('MOVE_'):
            text = text[5:]
        text = text.replace('_', ' ').title().strip()
        return text or None

    def _type_name(self, type_symbol: str | None) -> str | None:
        text = str(type_symbol or '').strip()
        if not text:
            return None
        type_name = self.model.types.get(text)
        if type_name:
            return type_name
        if text.startswith('TYPE_'):
            text = text[5:]
        text = text.replace('_', ' ').title().strip()
        return text or None

    def _species_name_from_symbol(self, species_symbol: str | None) -> str | None:
        species = self.model.species.get(str(species_symbol or '').strip())
        if species:
            return species.name
        text = str(species_symbol or '').strip()
        if text.startswith('SPECIES_'):
            text = text[8:]
        text = text.replace('_', '-').title().strip()
        return text or None

    def _map_name(self, map_symbol: str | None) -> str | None:
        text = str(map_symbol or '').strip()
        if not text:
            return None
        for prefix in ('MAPSEC_', 'MAP_'):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        text = text.replace('_', ' ').title().strip()
        return text or None

    def _render_custom_species_entry_block(self, key: str, entry: ShowdownSpecies) -> str:
        record = entry.record
        fields: list[tuple[str, Any]] = [
            ('num', entry.num),
            ('name', entry.display_name),
            ('types', record.types[:2] or ['Normal']),
            ('baseStats', self._species_base_stats(record)),
            ('abilities', self._species_abilities(record)),
            ('heightm', self._species_heightm(record)),
            ('weightkg', self._species_weightkg(record)),
        ]
        egg_groups = record.egg_groups[:2]
        if egg_groups:
            fields.append(('eggGroups', egg_groups))
        gender = self._normalize_gender(record.gender_ratio)
        if gender:
            fields.append(('gender', gender))
        elif record.gender_ratio:
            ratio = self._parse_gender_ratio(record.gender_ratio)
            if ratio:
                fields.append(('genderRatio', ratio))
        if entry.base_key:
            base_species_name = self._species_entries[entry.base_key].display_name
            fields.append(('baseSpecies', base_species_name))
            if entry.forme:
                fields.append(('forme', entry.forme))
            required_item = self._required_item_for_form(entry)
            if required_item:
                fields.append(('requiredItem', required_item))
            required_ability = self._required_ability_for_form(entry)
            if required_ability:
                fields.append(('requiredAbility', required_ability))
            battle_only = self._battle_only_for_form(entry)
            if battle_only:
                fields.append(('battleOnly', battle_only))
            changes_from = self._changes_from_for_form(entry)
            if changes_from:
                fields.append(('changesFrom', changes_from))
        rendered = ',\n'.join(f'\t\t{field}: {self._ts(value)}' for field, value in fields)
        return f"\t{self._quote_key(key)}: {{\n{rendered}\n\t}},\n"

    def _render_learnsets_ts(self) -> str:
        lines = [
            '/**',
            ' * Generated by Obstagoon. Only teachable learnsets are emitted for this mod.',
            ' */',
            "export const Learnsets: import('../../../sim/dex-species').ModdedLearnsetDataTable = {",
        ]
        for key, entry in self._species_entries_in_export_order():
            if entry.is_cosmetic:
                continue
            learnset: dict[str, list[str]] = {}
            for teachable in entry.record.learnsets.teachable:
                value = str(teachable.get('value') or '').strip()
                move_key = self._move_lookup_key(value)
                if not move_key:
                    continue
                learnset.setdefault(move_key, ['9M'])
            lines.append(
                f"\t{self._quote_key(key)}: {{\n\t\tlearnset: {self._ts(learnset)}\n\t}},"
            )
        lines.append('};')
        return '\n'.join(lines) + '\n'

    def _render_moves_ts(self) -> str:
        lines = [
            '/**',
            ' * Generated by Obstagoon.',
            ' */',
            "export const Moves: import('../../../sim/dex-moves').ModdedMoveDataTable = {",
        ]
        for move_id, move in sorted(self.model.moves.items()):
            fields: list[tuple[str, Any]] = [
                ('name', move.name),
                ('num', self._move_num(move_id)),
                ('type', move.type or 'Normal'),
                ('category', move.category or 'Status'),
                ('basePower', self._safe_int(move.power, default=0)),
                ('accuracy', self._move_accuracy(move.accuracy)),
                ('pp', self._safe_int(move.pp, default=1)),
                ('priority', 0),
                ('target', 'normal'),
                ('gen', GEN),
            ]
            if move.description:
                fields.append(('desc', move.description))
                fields.append(('shortDesc', move.description))
            rendered = ',\n'.join(f'\t\t{field}: {self._ts(value)}' for field, value in fields)
            lines.append(f"\t{self._quote_key(self._move_key(move_id))}: {{\n{rendered}\n\t}},")
        lines.append('};')
        return '\n'.join(lines) + '\n'

    def _render_abilities_ts(self) -> str:
        lines = [
            '/**',
            ' * Generated by Obstagoon.',
            ' */',
            "export const Abilities: import('../../../sim/dex-abilities').ModdedAbilityDataTable = {",
        ]
        for ability_id, ability in sorted(self.model.abilities.items()):
            fields: list[tuple[str, Any]] = [
                ('name', ability.name),
                ('num', self._ability_num(ability_id)),
                ('gen', GEN),
            ]
            if ability.description:
                fields.append(('desc', ability.description))
                fields.append(('shortDesc', ability.description))
            rendered = ',\n'.join(f'\t\t{field}: {self._ts(value)}' for field, value in fields)
            lines.append(f"\t{self._quote_key(self._ability_key(ability_id))}: {{\n{rendered}\n\t}},")
        lines.append('};')
        return '\n'.join(lines) + '\n'

    def _render_items_ts(self) -> str:
        lines = [
            '/**',
            ' * Generated by Obstagoon.',
            ' */',
            "export const Items: import('../../../sim/dex-items').ModdedItemDataTable = {",
        ]
        for item_id, item in sorted(self.model.items.items()):
            fields: list[tuple[str, Any]] = [
                ('name', item.name),
                ('num', self._item_num(item_id)),
                ('gen', GEN),
            ]
            if item.description:
                fields.append(('desc', item.description))
                fields.append(('shortDesc', item.description))
            rendered = ',\n'.join(f'\t\t{field}: {self._ts(value)}' for field, value in fields)
            lines.append(f"\t{self._quote_key(self._item_key(item_id))}: {{\n{rendered}\n\t}},")
        lines.append('};')
        return '\n'.join(lines) + '\n'

    def _render_formats_data_ts(self) -> str:
        lines = [
            '/**',
            ' * Generated by Obstagoon.',
            ' */',
            "export const FormatsData: import('../../../sim/dex-species').ModdedSpeciesFormatsDataTable = {",
        ]
        for key, entry in self._species_entries_in_export_order():
            if entry.is_cosmetic:
                continue
            lines.append(
                f"\t{self._quote_key(key)}: {{\n\t\ttier: 'Illegal',\n\t\tdoublesTier: 'Illegal',\n\t}},"
            )
        lines.append('};')
        return '\n'.join(lines) + '\n'

    def _render_aliases_ts(self) -> str:
        aliases: dict[str, str] = {}
        for entry in self._species_entries.values():
            target = entry.base_key if entry.is_cosmetic and entry.base_key else entry.key
            for alias in entry.aliases:
                if alias and alias != target:
                    aliases[alias] = target
        lines = [
            '/**',
            ' * Generated by Obstagoon.',
            ' */',
            "export const Aliases: import('../../../sim/dex').AliasesTable = {",
        ]
        for alias, target in sorted(aliases.items()):
            lines.append(f'\t{json.dumps(alias)}: {json.dumps(target)},')
        lines.append('};')
        return '\n'.join(lines) + '\n'


    def _render_root_aliases_ts(self) -> str:
        aliases: dict[str, str] = {}
        compound_word_names: list[str] = []
        for entry in self._species_entries.values():
            target = entry.base_key if entry.is_cosmetic and entry.base_key else entry.key
            for alias in entry.aliases:
                if alias and alias != target:
                    aliases[alias] = target
            if '-' in entry.display_name or ' ' in entry.display_name:
                compound_word_names.append(entry.display_name)
        lines = [
            '/**',
            ' * Generated by Obstagoon.',
            ' * Merge these aliases into data/aliases.ts in your Showdown fork.',
            ' */',
            "export const Aliases: import('../sim/dex').AliasesTable = {",
        ]
        for alias, target in sorted(aliases.items()):
            lines.append(f'\t{json.dumps(alias)}: {json.dumps(target)},')
        lines.extend([
            '};',
            '',
            'export const CompoundWordNames = [',
        ])
        for name in sorted(set(compound_word_names)):
            lines.append(f'\t{json.dumps(name)},')
        lines.append('];')
        return '\n'.join(lines) + '\n'

    def _render_formats_ts(self) -> str:
        formats = [
            {
                'name': '[Gen 9 Obstagoon] Teambuilder',
                'mod': 'obstagoon',
                'searchShow': True,
                'debug': True,
                'battle': {'trunc': 'Math.trunc'},
                'ruleset': ['Team Preview', 'Obtainable', 'Cancel Mod', 'Max Team Size = 24', 'Max Move Count = 24', 'Default Level = 100'],
            },
            {
                'name': '[Gen 9 Obstagoon] Singles',
                'mod': 'obstagoon',
                'ruleset': ['[Gen 9 Obstagoon] Teambuilder'],
            },
            {
                'name': '[Gen 9 Obstagoon] Doubles',
                'mod': 'obstagoon',
                'gameType': 'doubles',
                'ruleset': ['[Gen 9 Obstagoon] Teambuilder'],
            },
        ]
        lines = [
            '/**',
            ' * Generated by Obstagoon.',
            ' * Import or paste these entries into your Showdown fork\'s config/formats.ts list.',
            ' */',
            'export const ObstagoonFormats = [',
        ]
        for fmt in formats:
            lines.append('\t' + self._format_object_ts(fmt) + ',')
        lines.append('];')
        return '\n'.join(lines) + '\n'

    def _render_server_readme(self) -> str:
        return (
            '# Server fork payload\n\n'
            'Copy `data/mods/obstagoon` into your Pokémon Showdown fork, merge the generated format definitions from `config/formats.obstagoon.generated.ts` into `config/formats.ts`, and merge `data/aliases.obstagoon.generated.ts` into the root `data/aliases.ts`.\n\n'
            'This mod inherits from `gen9` and intentionally emits only teachable learnsets for validation in the custom Obstagoon format.\n'
        )

    def _render_client_build_script(self) -> str:
        return (
            '#!/usr/bin/env node\n'
            "'use strict';\n\n"
            'const fs = require("fs");\n'
            'const path = require("path");\n'
            'const child_process = require("child_process");\n\n'
            'const rootDir = path.resolve(__dirname, "..");\n'
            'process.chdir(rootDir);\n\n'
            'const sourceRepo = process.env.OBSTAGOON_SHOWDOWN_SOURCE || path.resolve(rootDir, "..", "server");\n'
            'const cacheDir = path.resolve(rootDir, "caches", "pokemon-showdown-obstagoon");\n'
            'fs.mkdirSync(path.dirname(cacheDir), {recursive: true});\n'
            'if (fs.existsSync(cacheDir)) fs.rmSync(cacheDir, {recursive: true, force: true});\n'
            'fs.cpSync(sourceRepo, cacheDir, {recursive: true});\n'
            'child_process.execSync("npm run build", {cwd: cacheDir, stdio: "inherit"});\n'
            'console.log("Prepared local Showdown source at", cacheDir);\n'
            'console.log("Replace the upstream clone step in build-tools/build-indexes with this local-source preparation step before requiring Dex.");\n'
        )

    def _render_client_readme(self) -> str:
        return (
            '# Client fork payload\n\n'
            'The stock Pokémon Showdown client builds teambuilder indexes from a checked-out server repository. Use `build-tools/build-indexes.obstagoon.js` as the local-source preparation step so the client indexes build against the generated server fork payload instead of upstream.\n\n'
            'Copied raster assets live under `assets/pokemon` and `assets/icons`. Non-raster sources are listed in the asset manifest for manual conversion if you want a fully skinned teambuilder.\n'
        )

    def _copy_client_assets(self) -> dict[str, Any]:
        manifest: dict[str, Any] = {'pokemon': {}, 'icons': {}, 'unresolved': {}}
        pokemon_dir = self.client_dir / 'assets' / 'pokemon'
        icon_dir = self.client_dir / 'assets' / 'icons'
        for entry in self._species_entries.values():
            if entry.is_cosmetic:
                continue
            display_graphics = self._display_graphics_for_record(entry.record)
            front_src = self._asset_source_for_record(entry.record, 'frontPic', display_graphics=display_graphics)
            icon_src = self._asset_source_for_record(entry.record, 'iconSprite', display_graphics=display_graphics)
            palette_src = None if self._is_site_rendered_asset(front_src) else display_graphics.get('palette')
            if front_src:
                copied = self._copy_asset(front_src, pokemon_dir, entry.key, kind='frontPic', palette_source=palette_src)
                if copied:
                    manifest['pokemon'][entry.key] = copied
                else:
                    manifest['unresolved'].setdefault(entry.key, {})['frontPic'] = str(front_src)
            else:
                manifest['unresolved'].setdefault(entry.key, {})['frontPic'] = 'missing'
            if icon_src:
                copied = self._copy_asset(icon_src, icon_dir, entry.key, kind='iconSprite')
                if copied:
                    manifest['icons'][entry.key] = copied
                else:
                    manifest['unresolved'].setdefault(entry.key, {})['iconSprite'] = str(icon_src)
            else:
                manifest['unresolved'].setdefault(entry.key, {})['iconSprite'] = 'missing'
        return manifest

    def _display_graphics_for_record(self, record: SpeciesRecord) -> dict[str, str]:
        return self._site_helper._display_graphics_for_species(record)

    def _asset_source_for_record(self, record: SpeciesRecord, kind: str, *, display_graphics: dict[str, str] | None = None) -> Path | None:
        display_graphics = display_graphics or self._display_graphics_for_record(record)
        candidate_values: list[str | None] = [display_graphics.get(kind), record.graphics.get(kind)]
        if kind == 'frontPic':
            for value in candidate_values:
                rendered = self._resolve_site_output_asset_path(value)
                if rendered:
                    return rendered
        for value in candidate_values:
            rendered = self._resolve_site_output_asset_path(value)
            if rendered:
                return rendered
            source = self._resolve_graphic_source(value)
            if source:
                resolved = self._resolve_raster_asset_source(source, kind)
                if resolved:
                    return resolved
        for candidate in self._candidate_asset_paths(record, kind):
            if candidate.exists() and candidate.is_file():
                resolved = self._resolve_raster_asset_source(candidate, kind)
                if resolved:
                    return resolved
        return None

    def _candidate_asset_paths(self, record: SpeciesRecord, kind: str) -> list[Path]:
        filenames = ['front.png', 'anim_front.png', 'front.webp', 'front.gif', 'front.jpg', 'front.jpeg'] if kind == 'frontPic' else ['icon.png', 'icon.webp', 'icon.gif', 'icon.jpg', 'icon.jpeg']
        roots: list[Path] = []
        seen: set[Path] = set()

        def add_root(path: Path) -> None:
            if path not in seen:
                seen.add(path)
                roots.append(path)

        for slug in self._species_asset_slugs(record):
            add_root(self.config.project_dir / 'graphics' / 'pokemon' / slug)
            if kind == 'iconSprite':
                add_root(self.config.project_dir / 'graphics' / 'pokemon' / 'icon')
                add_root(self.config.project_dir / 'graphics' / 'pokemon' / 'icons')
        candidates: list[Path] = []
        for root in roots:
            if kind == 'iconSprite' and root.name in {'icon', 'icons'}:
                for slug in self._species_asset_slugs(record):
                    for ext in ['.png', '.webp', '.gif', '.jpg', '.jpeg']:
                        candidates.append(root / f'{slug}{ext}')
            for filename in filenames:
                candidates.append(root / filename)
        return candidates

    def _species_asset_slugs(self, record: SpeciesRecord) -> list[str]:
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

        add(record.species_id)
        add(record.name)
        if record.base_species:
            add(record.base_species)
            base = self.model.species.get(record.base_species)
            if base:
                add(base.name)
                if record.form_name:
                    add(f'{base.name}_{record.form_name}')
                    add(f'{base.species_id.replace("SPECIES_", "")}_{record.form_name}')
        if record.form_name:
            add(record.form_name)
        return slugs

    def _resolve_raster_asset_source(self, source: Path, kind: str) -> Path | None:
        if source.suffix.lower() in RASTER_SUFFIXES:
            return source
        raster = self._find_raster_variant_near(source, kind)
        if raster:
            return raster
        return None

    def _find_raster_variant_near(self, source: Path, kind: str) -> Path | None:
        preferred_names = ['front.png', 'anim_front.png', 'front.webp', 'front.gif', 'front.jpg', 'front.jpeg'] if kind == 'frontPic' else ['icon.png', 'icon.webp', 'icon.gif', 'icon.jpg', 'icon.jpeg']
        stem = source.name
        stem = stem[:-8] if stem.endswith('.4bpp.lz') else Path(stem).stem
        dynamic_names = [f'{stem}{ext}' for ext in ['.png', '.webp', '.gif', '.jpg', '.jpeg'] if stem and stem not in {'front', 'icon'}]
        names = preferred_names + dynamic_names
        search_dirs = [source.parent, *source.parent.parents]
        project_root = self.config.project_dir.resolve()
        seen: set[Path] = set()
        for directory in search_dirs:
            directory = directory.resolve()
            if directory in seen:
                continue
            seen.add(directory)
            for name in names:
                candidate = directory / name
                if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in RASTER_SUFFIXES:
                    return candidate
            if directory == project_root:
                break
        return None

    def _copy_asset(self, source: Path, dest_dir: Path, dest_name: str, *, kind: str, palette_source: str | None = None) -> str | None:
        suffix = source.suffix.lower()
        if suffix not in RASTER_SUFFIXES:
            return None
        site_rendered = self._is_site_rendered_asset(source)
        output_suffix = '.png' if (self.config.pillow_transparency and suffix in {'.png', '.webp', '.jpg', '.jpeg'} and not site_rendered) else suffix
        dest = dest_dir / f'{dest_name}{output_suffix}'
        if site_rendered:
            shutil.copy2(source, dest)
        elif self.config.pillow_transparency and suffix in {'.png', '.webp', '.jpg', '.jpeg'}:
            rel = self._relative_to_project_or_self(source)
            if kind == 'frontPic':
                apply_palette = False
                if palette_source:
                    apply_palette = self._site_helper._should_apply_palette_variant(rel, palette_source)
                self._site_helper._process_png_asset(source, rel, dest, palette_source=palette_source, apply_palette=apply_palette)
            else:
                self._copy_asset_with_transparency(source, dest)
        else:
            shutil.copy2(source, dest)
        return str(dest.relative_to(self.client_dir))

    def _relative_to_project_or_self(self, path: Path) -> Path:
        try:
            return path.resolve().relative_to(self.config.project_dir.resolve())
        except ValueError:
            return Path(path.name)

    def _copy_asset_with_transparency(self, source: Path, dest: Path) -> None:
        Image = _load_pillow_image_module()
        with Image.open(source) as img:
            processed = self._make_png_background_transparent(img)
            processed.save(dest)

    def _make_png_background_transparent(self, image):
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

    def _resolve_graphic_source(self, value: str | None) -> Path | None:
        if not value:
            return None
        source = Path(value)
        if not source.is_absolute():
            source = (self.config.project_dir / source).resolve()
        if not source.exists():
            return None
        return source

    def _resolve_site_output_asset_path(self, value: str | None) -> Path | None:
        if not value:
            return None
        text = str(value).replace('\\', '/')
        marker = 'assets/game/'
        idx = text.find(marker)
        if idx < 0:
            return None
        rel = Path(text[idx:])
        candidate = (self.config.dist_dir / rel).resolve()
        if candidate.exists() and candidate.is_file():
            return candidate
        return None

    def _is_site_rendered_asset(self, path: Path | None) -> bool:
        if path is None:
            return False
        try:
            path.resolve().relative_to((self.config.dist_dir / 'assets' / 'game').resolve())
            return True
        except ValueError:
            return False

    def _species_aliases(self, rec: SpeciesRecord, display_name: str, canonical: CanonicalSpecies | None = None) -> set[str]:
        aliases = {
            self._to_id(display_name),
            self._species_id_to_id(rec.species_id),
        }
        if canonical:
            aliases.add(canonical.key)
            aliases.add(self._to_id(canonical.name))
        if not rec.base_species:
            aliases.add(self._to_id(rec.name))
        if rec.form_name:
            aliases.add(self._to_id(f'{rec.name}-{rec.form_name}'))
        if rec.base_species and rec.form_name:
            base = self.model.species.get(rec.base_species)
            if base:
                aliases.add(self._to_id(f'{base.name}-{rec.form_name}'))
                aliases.add(self._to_id(f'{base.name} {rec.form_name}'))
        return {alias for alias in aliases if alias}

    def _canonical_match_base(self, rec: SpeciesRecord) -> CanonicalSpecies | None:
        if not self._canonical_pokedex:
            return None
        direct = self._canonical_pokedex.base_by_name.get(rec.name)
        if direct and self._canonical_name_matches_record(direct.name, rec.name) and (direct.num is None or rec.national_dex is None or direct.num == rec.national_dex):
            return direct
        target_id = self._to_id(rec.name)
        for entry in self._canonical_pokedex.base_by_name.values():
            if self._to_id(entry.name) == target_id and (entry.num is None or rec.national_dex is None or entry.num == rec.national_dex):
                return entry
        return None

    def _canonical_match_form(self, rec: SpeciesRecord, base_rec: SpeciesRecord) -> CanonicalSpecies | None:
        if not self._canonical_pokedex:
            return None
        base_canonical = self._record_to_canonical.get(base_rec.species_id) or self._canonical_match_base(base_rec)
        if not base_canonical:
            return None
        if rec.form_index is not None and base_canonical.forme_order and rec.form_index < len(base_canonical.forme_order):
            child_name = base_canonical.forme_order[rec.form_index]
            child = self._canonical_pokedex.by_name.get(child_name)
            if child:
                return child
        candidates = self._canonical_pokedex.children_by_base.get(base_canonical.name, [])
        desired = self._normalize_matching_form_token(rec, base_rec)
        for candidate in candidates:
            if self._normalize_matching_form_token_from_canonical(candidate) == desired:
                return candidate
        return None

    def _canonical_name_matches_record(self, canonical_name: str, record_name: str) -> bool:
        return self._to_id(canonical_name) == self._to_id(record_name)

    def _normalize_matching_form_token(self, rec: SpeciesRecord, base_rec: SpeciesRecord) -> str:
        raw = (rec.form_name or '').strip()
        if not raw:
            base_name = self._to_id(base_rec.name)
            rec_name = self._to_id(rec.name)
            raw = rec_name.removeprefix(base_name) or rec.name
        return self._to_id(raw)

    def _normalize_matching_form_token_from_canonical(self, canonical: CanonicalSpecies) -> str:
        if canonical.forme:
            return self._to_id(canonical.forme)
        if canonical.base_species and canonical.name.startswith(f'{canonical.base_species}-'):
            return self._to_id(canonical.name[len(canonical.base_species) + 1:])
        return self._to_id(canonical.name)

    def _normalize_forme_name(self, rec: SpeciesRecord, base_rec: SpeciesRecord) -> str:
        form = (rec.form_name or '').replace('_', ' ').replace('-', ' ').strip()
        if not form:
            base_name = self._to_id(base_rec.name)
            rec_name = self._to_id(rec.name)
            form = rec_name.removeprefix(base_name).strip() or rec.name
        form = re.sub(r'\s+', ' ', form).strip()
        if form:
            base_words = [word for word in re.split(r'[\s-]+', base_rec.name) if word]
            form_words = [word for word in re.split(r'[\s-]+', form) if word]
            while form_words and base_words and form_words[0].lower() == base_words[0].lower():
                form_words.pop(0)
                base_words.pop(0)
            if form_words:
                form = ' '.join(form_words)
        canonical = FORME_CANONICAL_BY_ID.get(self._to_id(form))
        if canonical:
            return canonical
        form = re.sub(r'\bMega\s+([XYZ])\b', r'Mega-\1', form, flags=re.I)
        form = re.sub(r'\bLow\s+Key\b', 'Low-Key', form, flags=re.I)
        form = re.sub(r'\bRapid\s+Strike\b', 'Rapid-Strike', form, flags=re.I)
        form = re.sub(r'\bDawn\s+Wings\b', 'Dawn-Wings', form, flags=re.I)
        form = re.sub(r'\bDusk\s+Mane\b', 'Dusk-Mane', form, flags=re.I)
        form = re.sub(r'\bRock\s+Star\b', 'Rock-Star', form, flags=re.I)
        form = re.sub(r'\bPop\s+Star\b', 'Pop-Star', form, flags=re.I)
        form = re.sub(r'\bPom\s+Pom\b', 'Pom-Pom', form, flags=re.I)
        form = re.sub(r'\b([A-Za-z]+)\s+Tera\b', r'\1-Tera', form, flags=re.I)
        return ' '.join(part.capitalize() if part.lower() not in {'gmax'} else 'Gmax' for part in form.split())

    def _display_form_species_name(self, rec: SpeciesRecord, base_rec: SpeciesRecord, forme: str) -> str:
        if forme:
            return f'{base_rec.name}-{forme}'
        if rec.name and self._to_id(rec.name) != self._to_id(base_rec.name):
            return rec.name
        return rec.name or base_rec.name

    def _is_cosmetic_form(self, rec: SpeciesRecord, base_rec: SpeciesRecord, forme: str | None) -> bool:
        text = f'{rec.species_id} {rec.name} {forme or ""}'.lower()
        cosmetic_species = {'alcremie', 'furfrou'}
        if any(species in text for species in cosmetic_species) and 'gmax' not in text:
            return True
        functional_tokens = {
            'alola', 'galar', 'hisui', 'paldea', 'mega', 'gmax', 'gigantamax', 'primal', 'origin', 'therian',
            'attack', 'defense', 'speed', 'complete', 'crowned', 'hero', 'blade', 'school', 'eternamax',
        }
        if any(token in text for token in functional_tokens):
            return False
        same_types = rec.types == base_rec.types
        same_abilities = rec.abilities == base_rec.abilities
        same_stats = rec.stats == base_rec.stats
        same_learnsets = rec.learnsets.teachable == base_rec.learnsets.teachable
        return same_types and same_abilities and same_stats and same_learnsets

    def _species_base_stats(self, rec: SpeciesRecord) -> dict[str, int]:
        stats = rec.stats or {}
        return {
            'hp': self._safe_int(stats.get('Base HP') or stats.get('HP') or stats.get('baseHP'), default=1),
            'atk': self._safe_int(stats.get('Base Attack') or stats.get('Atk') or stats.get('baseAttack'), default=1),
            'def': self._safe_int(stats.get('Base Defense') or stats.get('Def') or stats.get('baseDefense'), default=1),
            'spa': self._safe_int(stats.get('Base Sp. Attack') or stats.get('SpA') or stats.get('baseSpAttack'), default=1),
            'spd': self._safe_int(stats.get('Base Sp. Defense') or stats.get('SpD') or stats.get('baseSpDefense'), default=1),
            'spe': self._safe_int(stats.get('Base Speed') or stats.get('Spe') or stats.get('baseSpeed'), default=1),
        }

    def _species_heightm(self, rec: SpeciesRecord) -> float:
        raw = (rec.stats or {}).get('Height')
        value = self._safe_float(raw, default=0.0)
        return round(value / 10.0, 3) if value else 0

    def _species_weightkg(self, rec: SpeciesRecord) -> float:
        raw = (rec.stats or {}).get('Weight')
        value = self._safe_float(raw, default=0.0)
        return round(value / 10.0, 3) if value else 0

    def _species_abilities(self, rec: SpeciesRecord) -> dict[str, str]:
        abilities: dict[str, str] = {}
        slots = list(rec.ability_slots or [])
        if not slots and rec.abilities:
            slots = list(rec.abilities[:3])
        if len(slots) > 0 and slots[0]:
            abilities['0'] = slots[0]
        if len(slots) > 1 and slots[1]:
            abilities['1'] = slots[1]
        if len(slots) > 2 and slots[2]:
            abilities['H'] = slots[2]
        return abilities or {'0': 'None'}

    def _normalize_gender(self, gender_ratio: str | None) -> str | None:
        if not gender_ratio:
            return None
        text = str(gender_ratio).strip()
        lowered = text.lower()
        if lowered in {'male only', 'male'} or text == 'MON_MALE':
            return 'M'
        if lowered in {'female only', 'female'} or text == 'MON_FEMALE':
            return 'F'
        if lowered in {'genderless'} or text == 'MON_GENDERLESS':
            return 'N'
        return None

    def _parse_gender_ratio(self, value: str) -> dict[str, float] | None:
        text = str(value).strip()
        m = re.match(r'PERCENT_FEMALE\(([^)]+)\)', text)
        if m:
            try:
                female = float(m.group(1).strip()) / 100.0
                male = 1.0 - female
                return {'M': round(male, 3), 'F': round(female, 3)}
            except ValueError:
                return None
        clean = text.replace('%', '').replace('/', ' ').replace(',', ' ').strip()
        parts = [part for part in clean.split() if part]
        if len(parts) >= 2:
            try:
                male = float(parts[0])
                female = float(parts[1])
                if male > 1 or female > 1:
                    total = male + female
                    if total:
                        male /= total
                        female /= total
                return {'M': round(male, 3), 'F': round(female, 3)}
            except ValueError:
                return None
        return None

    def _form_change_for_entry(self, entry: ShowdownSpecies) -> dict[str, Any] | None:
        if not entry.base_key:
            return None
        base_entry = self._species_entries.get(entry.base_key)
        if not base_entry:
            return None
        for change in base_entry.record.form_changes:
            if change.get('target_species') == entry.record.species_id:
                return change
        return None

    def _required_item_for_form(self, entry: ShowdownSpecies) -> str | None:
        change = self._form_change_for_entry(entry)
        if not change:
            return None
        item = change.get('item')
        if not item or item == 'ITEM_NONE':
            return None
        return self._item_name(item)

    def _changes_from_for_form(self, entry: ShowdownSpecies) -> str | None:
        change = self._form_change_for_entry(entry)
        if not change:
            return None
        method = str(change.get('method') or '')
        if 'GIGANTAMAX' in method:
            base_entry = self._species_entries.get(entry.base_key)
            return base_entry.display_name if base_entry else None
        return None

    def _battle_only_for_form(self, entry: ShowdownSpecies) -> str | None:
        change = self._form_change_for_entry(entry)
        if not change:
            return None
        method = str(change.get('method') or '')
        if 'BATTLE' not in method or 'GIGANTAMAX' in method or 'MEGA_EVOLUTION_ITEM' in method:
            return None
        base_entry = self._species_entries.get(entry.base_key)
        return base_entry.display_name if base_entry else None

    def _required_ability_for_form(self, entry: ShowdownSpecies) -> str | None:
        if not self._battle_only_for_form(entry):
            return None
        base_entry = self._species_entries.get(entry.base_key)
        if not base_entry:
            return None
        base_abilities = [ability for ability in self._species_abilities(base_entry.record).values() if ability and ability != 'None']
        form_abilities = [ability for ability in self._species_abilities(entry.record).values() if ability and ability != 'None']
        shared = [ability for ability in form_abilities if ability in base_abilities]
        if len(set(shared)) == 1:
            return shared[0]
        if len(set(form_abilities)) == 1:
            return form_abilities[0]
        return None

    def _is_gigantamax_form(self, entry: ShowdownSpecies) -> bool:
        change = self._form_change_for_entry(entry)
        if change and 'GIGANTAMAX' in str(change.get('method') or ''):
            return True
        forme = entry.forme or ''
        return self._to_id(forme) == 'gmax'

    def _can_gigantamax_for_base(self, entry: ShowdownSpecies) -> str | None:
        for child in self._species_entries.values():
            if child.base_key == entry.key and self._is_gigantamax_form(child):
                return CANONICAL_CAN_GIGANTAMAX.get(entry.display_name)
        return None

    def _item_name(self, item_symbol: str) -> str:
        item = self.model.items.get(item_symbol)
        if item:
            return item.name
        text = str(item_symbol or '').strip()
        if text.startswith('ITEM_'):
            text = text[5:]
        return text.replace('_', ' ').title()

    def _move_accuracy(self, value: str | None) -> int | bool:
        text = str(value or '').strip()
        if text.lower() in {'true', 'always', 'never miss'}:
            return True
        return self._safe_int(text, default=100)


    def _move_lookup_key(self, value: str | None) -> str | None:
        text = str(value or '').strip()
        if not text:
            return None
        if text.startswith('MOVE_'):
            return self._move_key(text)
        target = self._to_id(text)
        for move_id, move in self.model.moves.items():
            if self._to_id(move.name) == target or self._to_id(move_id.replace('MOVE_', '')) == target:
                return self._move_key(move_id)
        return None
    def _move_key(self, move_id: str) -> str:
        return self._to_id(self.model.moves.get(move_id, MoveRecord(move_id, move_id)).name if move_id in self.model.moves else move_id.replace('MOVE_', '').replace('_', ' '))

    def _ability_key(self, ability_id: str) -> str:
        ability = self.model.abilities.get(ability_id)
        return self._to_id(ability.name if ability else ability_id.replace('ABILITY_', '').replace('_', ' '))

    def _item_key(self, item_id: str) -> str:
        item = self.model.items.get(item_id)
        return self._to_id(item.name if item else item_id.replace('ITEM_', '').replace('_', ' '))

    def _move_num(self, move_id: str) -> int:
        self._custom_move_counter += 1
        return self._custom_move_counter - 1

    def _ability_num(self, ability_id: str) -> int:
        self._custom_ability_counter += 1
        return self._custom_ability_counter - 1

    def _item_num(self, item_id: str) -> int:
        self._custom_item_counter += 1
        return self._custom_item_counter - 1

    def _next_custom_species_num(self) -> int:
        self._custom_species_counter += 1
        return self._custom_species_counter - 1

    def _unique_species_key(self, preferred: str, species_id: str) -> str:
        key = preferred or self._species_id_to_id(species_id)
        if key not in self._species_entries:
            return key
        suffix = self._species_id_to_id(species_id)
        if suffix and not key.endswith(suffix):
            candidate = f'{key}{suffix}'
            if candidate not in self._species_entries:
                return candidate
        i = 2
        while f'{key}{i}' in self._species_entries:
            i += 1
        return f'{key}{i}'

    def _format_object_ts(self, value: dict[str, Any]) -> str:
        parts = []
        for key, raw in value.items():
            if isinstance(raw, dict) and raw == {'trunc': 'Math.trunc'}:
                parts.append(f'{key}: {{trunc: Math.trunc}}')
            else:
                parts.append(f'{key}: {self._ts(raw)}')
        return '{' + ', '.join(parts) + '}'

    def _write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def _quote_key(self, key: str) -> str:
        return self._ts_key(key)

    def _ts(self, value: Any) -> str:
        if isinstance(value, dict):
            inner = ', '.join(f'{self._ts_key(k)}: {self._ts(v)}' for k, v in value.items())
            return '{' + inner + '}'
        if isinstance(value, list):
            return '[' + ', '.join(self._ts(v) for v in value) + ']'
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if value is None:
            return 'undefined'
        if isinstance(value, (int, float)):
            return repr(value)
        return json.dumps(str(value), ensure_ascii=False)

    def _ts_key(self, key: str) -> str:
        if key.isdigit():
            return key
        return key if key.replace('_', '').isalnum() and not key[0].isdigit() else json.dumps(key)

    def _safe_int(self, value: Any, default: int = 0) -> int:
        try:
            text = str(value).strip()
            if not text:
                return default
            if text.startswith('0x'):
                return int(text, 16)
            return int(float(text))
        except Exception:
            return default

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            text = str(value).strip()
            if not text:
                return default
            return float(text)
        except Exception:
            return default

    def _species_id_to_id(self, value: str | None) -> str:
        return self._to_id(str(value or '').replace('SPECIES_', ''))

    def _to_id(self, value: str | None) -> str:
        text = str(value or '').lower()
        text = text.replace('♀', 'f').replace('♂', 'm')
        text = text.replace("'", '')
        return ''.join(ch for ch in text if ch.isalnum())


def generate_showdown_export(config, model: ObstagoonModel) -> None:
    ShowdownExportGenerator(config=config, model=model).run()
