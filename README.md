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
