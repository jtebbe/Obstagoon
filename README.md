# Obstagoon


**For the wonderful Linoone documentation generator that works with pokeemerald and not pokeemerald-expansion, please find it here courtesy of huderlem: https://github.com/huderlem/linoone**

Obstagoon is a static documentation generator for **`pokeemerald-expansion`** and related modern Pokémon decompilation forks.

It is intentionally **not** a direct Linoone fork in architecture. Instead, it is a new backend-first system built around the expansion data model:

- `gSpeciesInfo`
- `gMovesInfo`
- `gAbilitiesInfo`
- `gItemsInfo`
- expansion learnset tables
- expansion form tables and form species
- expansion wild encounter data
- expansion sprite/palette/icon references

The goal is to generate a reference site similar to Bulbapedia / Serebii for ROM hacks, while tolerating the much broader data model in `pokeemerald-expansion`.

## Current design goals

- Parse expansion-native species, moves, abilities, items, types, evolutions, forms, learnsets, encounters, and sprite references
- Build a single normalized intermediate model before HTML generation
- Keep parsing and rendering separated so the project can later support JSON APIs, search indexes, and alternate frontends
- Favor **symbol-reference extraction** and **include flattening** over brittle vanilla-only AST assumptions

## Features

- Expansion-native species, moves, abilities, items, evolutions, forms, and encounter parsing
- Search bars on Pokédex, Moves, Abilities, and Encounters pages
- Type color badges across Pokédex, species, move, and type pages
- Egg move inheritance for evolved species
- Encounter locations shown on species pages
- Optional asset copying for front sprites and other web-ready assets
- UTF-8 / mojibake cleanup for Pokémon text and symbols
- Validation reports for missing or ambiguous sprite matches

## Status

This repository is a **best-effort complete architecture starter** for an expansion-native site generator.
It is materially more complete than the earlier scaffold and includes modules for:

- species parsing
- move / ability / item parsing
- teachable learnset parsing
- explicit form handling
- encounter parsing
- sprite manifest generation and file copying
- page generation for index, Pokédex, species, moves, abilities, types, encounters, and forms

It is still a porting project rather than a guaranteed drop-in mirror of every expansion fork. The largest likely customization points are:

- exact learnset macro variants used by a hack
- exact sprite asset locations
- encounter include organization
- custom forms outside the standard expansion conventions

## Install

```bash
pip install -r requirements.txt

# optional, only needed for --pillow-transparency
pip install Pillow
```

## Usage

```bash
python -m obstagoon /path/to/pokeemerald-expansion --title "My Hack Dex"
```

Optional arguments:


```bash
python -m obstagoon /path/to/project \
  --title "My Hack Dex" \
  --dist-dir ./dist \
  --site-url https://example.com/dex \
  --copy-assets \
  --pillow-transparency \
  --wild-encounters-json ./wild_encounters.json
```

`--pillow-transparency` is optional. Without it, Obstagoon copies assets as-is and does not require Pillow.

## Output

Generated site structure includes pages for:

- `/index.html`
- `/pokedex/index.html`
- `/pokedex/<dex>.html`
- `/moves/index.html`
- `/moves/<move>.html`
- `/abilities/index.html`
- `/abilities/<ability>.html`
- `/types/<type>.html`
- `/forms/index.html`
- `/encounters/index.html`

## Architecture

Obstagoon has three layers:

1. **Extraction**: parse expansion source files into raw symbols and records.
2. **Normalization**: create a unified in-memory model with species, dex, forms, learnsets, evolutions, encounters, and assets.
3. **Generation**: render HTML templates and optionally copy sprite assets.

## Notes on sprite support

Obstagoon currently treats sprite support as **reference-manifest + asset copy**, not image decompression. That is the right fit for expansion projects, where many hacks already keep PNG/web assets alongside the decomp or have custom export pipelines.

## Notes on forms

Forms are explicit first-class records. The model preserves:

- base species
- form species
- shared National Dex mapping when present
- parent/child relationships
- separate learnsets / abilities / graphics when the data differs

## Notes on teachable learnsets

Expansion forks often represent teachable learnsets through symbol references and macros instead of the old vanilla bitfield assumptions. Obstagoon resolves these symbol references, tokenizes macro invocations, and classifies them into buckets like TM/HM, tutor, and generic teachable sources.

## License

This repository is intended as a new project inspired by the needs of Linoone users who target `pokeemerald-expansion`. Verify upstream licensing requirements before publishing a public fork or derivative distribution.


## Generated wild encounters JSON

Because expansion wild encounters are often generated at build time, Obstagoon can ingest a generated JSON export directly with `--wild-encounters-json`. The parser expects a top-level `wild_encounter_groups` array with per-method definitions, encounter-rate weights, optional fishing subgroups, and per-map encounter blocks.


## Validation output

Each build now emits:

- `dist/assets/manifest.json`
- `dist/assets/validation.json`

The validation report flags unresolved graphics, likely kind mismatches (for example a front sprite resolving to an icon), and missing assets.


## Progress output

Run with `--verbose` to show step-by-step progress, including parse stages, page rendering counts, asset copy progress, and a final build summary.


## Search and filtering

Generated index pages include built-in client-side search:

- **Pokédex**: dex number, name, type, and ability
- **Moves**: name, type, category, power, accuracy, PP, and description
- **Abilities**: name and description
- **Encounters**: area, method, and species

## Type badges

Obstagoon renders color-coded type badges for easier scanning on the Pokédex, move pages, and species pages. The badge palette includes expansion types such as **Fairy** and **Stellar**.

## Asset copying

Use `--copy-assets` when you want web-ready assets copied into the generated site. For a fast data-only build, omit it.

By default, copied PNG assets are left unchanged. To enable the experimental Pillow-based post-processing pass for `graphics/pokemon/.../*.png`, add `--pillow-transparency`. That pass removes every pixel matching the top-left pixel color and crops `anim_front.png` / `front_anim.png` to the top half. Trainer front pics are not altered.


## Generational config support

Obstagoon now reads project config defines from `include/config/` and applies them when parsing species, moves, abilities, and learnsets. This lets the generated docs reflect config-driven data changes such as updated types, updated abilities, and move-data generation switches.

Supported parsing behavior includes:
- `#if / #elif / #else / #endif` blocks in include-flattened source data
- inline ternary values such as `B_UPDATED_MOVE_DATA >= GEN_2 ? TYPE_DARK : TYPE_NORMAL`
- symbolic config defines like `#define P_UPDATED_ABILITIES GEN_9`

This means Pokémon, move, and ability data shown by the site should track the active expansion configuration much more closely.


## Hoenn Dex Mode (`--hoenn-dex`)

- Limits parsing strictly to the Hoenn Pokédex (Treecko → Deoxys)
- Uses `enum HoennDexOrder` from `include/constants/pokedex.h`
- Skips all non-Hoenn species entirely (not parsed, not rendered)
- Respects conditional flags (e.g. `P_NEW_EVOS_IN_REGIONAL_DEX`)
- Alternate forms share the same Hoenn dex number as their base species

## Species Inclusion (`species_enabled.h`)

Obstagoon respects:

`include/config/species_enabled.h`

- If a family (e.g. `P_FAMILY_BULBASAUR`) is `FALSE`, all species in that family are excluded
- Disabled species are not parsed, counted, or rendered


## Pokémon Showdown export (`--showdown-export`)

Obstagoon can now generate a **Pokémon Showdown fork payload** after the normal site build.
This export is aimed at a **custom teambuilder / validator workflow** for `pokeemerald-expansion`-based projects.

### What it generates

When `--showdown-export` is enabled, Obstagoon writes a generated export tree to:

Pass `--showdown-canonical-pokedex /path/to/pokedex.ts` to preserve upstream Showdown canonical keys, names, `forme`, `otherFormes`, and `formeOrder` for unchanged species/forms instead of reconstructing them from ROM labels.

- `./dist/showdown-export` by default (or `<your --dist-dir>/showdown-export` when `--dist-dir` is used), or
- the path provided with `--showdown-export-dir`

The export contains two payloads:

- `server/` — a generated Showdown mod payload
- `client/` — generated client-fork helpers and copied teambuilder assets

Example layout:

```text
dist/showdown-export/
  README.md
  manifest.json
  server/
    README.md
    data/mods/obstagoon/
      scripts.ts
      pokedex.ts
      learnsets.ts
      moves.ts
      abilities.ts
      items.ts
      formats-data.ts
      aliases.ts
    aliases.obstagoon.generated.ts
    config/
      formats.obstagoon.generated.ts
  client/
    README.md
    build-tools/
      build-indexes.obstagoon.js
    assets/
      pokemon/
      icons/
      manifest.json
```

### Usage

```bash
python -m obstagoon /path/to/project \
  --title "My Hack Dex" \
  --showdown-export
```

By default, Obstagoon prints a clearly marked verbose message with the resolved Showdown export path when `--verbose` is enabled.

Optional custom export path:

```bash
python -m obstagoon /path/to/project \
  --title "My Hack Dex" \
  --showdown-export \
  --showdown-export-dir ./showdown-export \
  --showdown-canonical-pokedex ./pokedex.ts
```

### Showdown export rules

The generated Showdown mod is designed around these rules:

- **Parent mod:** inherits from `gen9`
- **Species precedence:** if expansion data changes an official entry, expansion data wins
- **Custom species/forms:** generated with reserved synthetic number ranges when no official National Dex number exists
- **Learnsets:** generated from each species' **teachable learnset only** for this custom ruleset
- **Descriptions:** move, ability, item, and species descriptions are preserved when available for teambuilder UX
- **Forms:** functionally distinct forms are exported separately, while cosmetic-only forms are aliased back to their base species where possible

Examples of expected form handling:

- regional variants such as Alolan / Galarian / Hisuian / Paldean forms → exported distinctly
- battle-relevant forms such as Mega / Primal / Origin / Gmax forms → exported distinctly
- cosmetic-only forms such as most Furfrou trims or non-Gmax Alcremie flavor variants → aliased to base species

### Move export scope

Generated move entries intentionally omit fields that are not needed for teambuilder-first export.
The current export excludes these fields when present:

- `effect`
- `battleAnimScript`
- `contestEffect`
- `contestCategory`
- `contestComboStarterId`
- `contestComboMoves`

The goal is to create valid Showdown Dex data for search, display, import/export, and custom-format validation without implementing custom battle logic for every new move.

### Sprite and icon handling

The client export tries to copy **raster** assets for teambuilder use:

- Pokémon front sprites → `client/assets/pokemon/`
- icons → `client/assets/icons/`

Supported direct-copy source formats currently include:

- `.png`
- `.webp`
- `.jpg`
- `.jpeg`
- `.gif`

Non-raster or unresolved sources are tracked in:

- `showdown-export/client/assets/manifest.json`

That makes it easier to identify assets that still need manual conversion or a separate sprite pipeline.

### Important limitations

The Showdown export is currently intended for:

- teambuilder support
- custom-format validation support
- teambuilder asset staging

It does **not** guarantee full battle simulation support for custom move / ability / item effects.
Custom entries are exported as data-first Showdown records unless their runtime behavior already exists in Showdown or matches an inherited official implementation.

### Recommended workflow

1. Run Obstagoon with `--showdown-export`
2. Copy `showdown-export/server/data/mods/obstagoon/` into your Showdown server fork
3. Merge `showdown-export/server/config/formats.obstagoon.generated.ts` into your fork's `config/formats.ts`
4. Merge `showdown-export/server/data/aliases.obstagoon.generated.ts` into the root `data/aliases.ts` in your Showdown fork
5. Point your Showdown client fork at the generated server fork when rebuilding teambuilder indexes
6. Review `client/assets/manifest.json` for unresolved sprites/icons


When `--pillow-transparency` is enabled, generated Showdown client assets in `client/assets/pokemon` and `client/assets/icons` are also rewritten with transparent backgrounds using Pillow where supported.
