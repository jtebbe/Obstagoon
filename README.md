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
pip install Pillow
```

Pillow is required when you use the Trainer Editor, because `--trainer-editor` now automatically enables documentation asset generation and transparency/sprite processing for the browser previews.

## Usage

```bash
python -m obstagoon /path/to/pokeemerald-expansion --title "My Hack Dex" --documentation
```



## CLI flags at a glance

Obstagoon currently supports these top-level flags:

- `--documentation` — build the HTML documentation site
- `--showdown-export` — generate the Showdown export payload
- `--trainer-editor` — build the documentation outputs needed by the Trainer Editor, then launch the browser editor for `src/data/trainers.party`
- `--copy-assets` — copy web-ready assets into the generated site output
- `--pillow-transparency` — use Pillow to crop `anim_front.png` / `front_anim.png` to the top half and make the top-left background color transparent for copied Pokémon sprites
- `--wild-encounters-json PATH` — ingest a generated wild encounters JSON export instead of relying only on source parsing
- `--title TEXT` — set the generated site title
- `--dist-dir PATH` — choose the output directory
- `--site-url URL` — set the site base URL used in generated output
- `--verbose` — print step-by-step build progress

Example:

```bash
python -m obstagoon /path/to/project \
  --documentation \
  --showdown-export \
  --copy-assets \
  --pillow-transparency \
  --title "My Hack Dex"
```

### Trainer Editor flag behavior

When `--trainer-editor` is used, Obstagoon now automatically enables the flags and behavior the browser editor depends on:

- `--documentation`
- `--copy-assets`
- `--pillow-transparency`

This means Trainer Editor users should have Pillow installed. The editor preview sprites are sourced from the generated documentation outputs so that form handling and shiny previews match the documentation pipeline.

Example:

```bash
python -m obstagoon /path/to/project --trainer-editor
```

That single command now builds the documentation outputs required for previews and then launches the Trainer Editor.

## Documentation generation

Documentation is no longer generated automatically.

You must explicitly pass the `--documentation` flag to generate documentation output.

### Example:

```bash
python -m obstagoon /path/to/project \
  --title "My Hack Dex" \
  --documentation
```

If `--documentation` is not provided, documentation will not be generated.
If `--showdown-export` is not provided, showdown data will not be generated.


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


## Trainer Editor (`--trainer-editor`)

The Trainer Editor currently focuses on trainer-level metadata in `src/data/trainers.party` and runs in your browser instead of requiring Tkinter or another desktop GUI toolkit.

Current browser-editor support includes:

- trainer selection by `TRAINER_*` section id, displayed without the `TRAINER_` prefix and annotated with in-game location when available
- trainer picture preview using the trainer's current `Pic` value and the same located trainer front pics Obstagoon already resolves for TrainerDex pages
- dropdown editing for trainer class, gender, music, battle type / double battle (depending on trainer format), mugshot color, pool rules, and party size
- up to 3 trainer items with `None` meaning the field is omitted on save
- checkbox editing for starting statuses in their own dedicated tab
- checkbox editing for AI flags
- a dedicated Pokémon tab with form-aware sprite previews, shiny previews, stats, abilities, natures, moves, tera type, balls, IVs, EVs, and tags
- dynamic Pokémon entry counts: only the trainer's current number of Pokémon are rendered, with add buttons up to 6 entries for standard trainers or 256 for pool trainers
- save / discard / cancel prompts when switching away from a trainer with unsaved changes

Current save behavior:

- empty / `None` dropdown values are omitted from the trainer's metadata block
- empty Pokémon entries are ignored and not written
- pool-related fields are only written when pool rules are set
- Pokémon previews are sourced from the generated documentation outputs so form handling matches the documentation pipeline


When auto-opening the browser, Obstagoon first tries Python's normal browser hook, then falls back to common platform launchers such as `wslview`, `cmd.exe /c start`, `xdg-open`, `open`, and common Chromium / Brave executable names. Some WSL or headless setups may still require opening the printed localhost URL manually.

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

#
