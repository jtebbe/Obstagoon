from __future__ import annotations

import subprocess
from pathlib import Path

from obstagoon.config import SiteConfig
from obstagoon.pipeline import build_site


def _write(path: Path, text: str = '') -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'')


def _write_canonical_pokedex(path: Path) -> None:
    _write(path, """export const Pokedex = {
	venusaur: {
		num: 3,
		name: "Venusaur",
		otherFormes: ["Venusaur-Mega", "Venusaur-Gmax"],
		formeOrder: ["Venusaur", "Venusaur-Mega", "Venusaur-Gmax"]
	},
	venusaurmega: {
		num: 3,
		name: "Venusaur-Mega",
		baseSpecies: "Venusaur",
		forme: "Mega"
	},
	venusaurgmax: {
		num: 3,
		name: "Venusaur-Gmax",
		baseSpecies: "Venusaur",
		forme: "Gmax"
	},
	vulpix: {
		num: 37,
		name: "Vulpix",
		otherFormes: ["Vulpix-Alola"],
		formeOrder: ["Vulpix", "Vulpix-Alola"]
	},
	vulpixalola: {
		num: 37,
		name: "Vulpix-Alola",
		baseSpecies: "Vulpix",
		forme: "Alola"
	},
	palafin: {
		num: 964,
		name: "Palafin",
		otherFormes: ["Palafin-Hero"],
		formeOrder: ["Palafin", "Palafin-Hero"]
	},
	palafinhero: {
		num: 964,
		name: "Palafin-Hero",
		baseSpecies: "Palafin",
		forme: "Hero"
	},
};
""")


def _make_showdown_project(tmp_path: Path) -> Path:
    project = tmp_path / 'proj'
    _write(project / 'include/constants/pokedex.h', '''
#define NATIONAL_DEX_VENUSAUR 3
#define NATIONAL_DEX_VULPIX 37
#define NATIONAL_DEX_ALCREMIE 869

enum HoennDexOrder {
    HOENN_DEX_VENUSAUR,
    HOENN_DEX_VULPIX,
    HOENN_DEX_ALCREMIE,
};
''')
    _write(project / 'src/data/types_info.h', '''
static const struct TypeInfo sTypeInfo[] = {
    [TYPE_NORMAL] = {.name = _("Normal")},
    [TYPE_GRASS] = {.name = _("Grass")},
    [TYPE_FIRE] = {.name = _("Fire")},
    [TYPE_ICE] = {.name = _("Ice")},
    [TYPE_FAIRY] = {.name = _("Fairy")},
};
''')
    _write(project / 'src/data/abilities.h', '''
static const struct Ability gAbilitiesInfo[] = {
    [ABILITY_OVERGROW] = {.name = _("Overgrow"), .description = _("Boosts Grass moves in a pinch.")},
    [ABILITY_CHLOROPHYLL] = {.name = _("Chlorophyll"), .description = _("Boosts Speed in sunshine.")},
    [ABILITY_FLASH_FIRE] = {.name = _("Flash Fire"), .description = _("Powers up Fire-type moves when hit by fire.")},
    [ABILITY_SNOW_CLOAK] = {.name = _("Snow Cloak"), .description = _("Raises evasion in hail.")},
    [ABILITY_SWEET_VEIL] = {.name = _("Sweet Veil"), .description = _("Prevents sleep in allies.")},
};
''')
    _write(project / 'src/data/moves_info.h', '''
static const struct MoveInfo sMovesInfo[] = {
    [MOVE_TACKLE] = {
        .name = _("Tackle"),
        .description = _("A physical attack."),
        .type = TYPE_NORMAL,
        .power = 40,
        .accuracy = 100,
        .pp = 35,
        .category = DAMAGE_CATEGORY_PHYSICAL,
    },
    [MOVE_FLAMETHROWER] = {
        .name = _("Flamethrower"),
        .description = _("A powerful fire attack."),
        .type = TYPE_FIRE,
        .power = 90,
        .accuracy = 100,
        .pp = 15,
        .category = DAMAGE_CATEGORY_SPECIAL,
    },
    [MOVE_DAZZLING_GLEAM] = {
        .name = _("Dazzling Gleam"),
        .description = _("Damages foes with a fairy flash."),
        .type = TYPE_FAIRY,
        .power = 80,
        .accuracy = 100,
        .pp = 10,
        .category = DAMAGE_CATEGORY_SPECIAL,
    },
    [MOVE_ICE_BEAM] = {
        .name = _("Ice Beam"),
        .description = _("Strikes with an icy beam."),
        .type = TYPE_ICE,
        .power = 90,
        .accuracy = 100,
        .pp = 10,
        .category = DAMAGE_CATEGORY_SPECIAL,
    },
};
''')
    _write(project / 'src/data/items.h', '''
static const struct Item gItems[] = {
    [ITEM_POTION] = {.name = _("Potion"), .description = _("Restores HP."), .pocket = POCKET_ITEMS, .price = 300},
    [ITEM_VENUSAURITE] = {.name = _("Venusaurite"), .description = _("Mega stone."), .pocket = POCKET_ITEMS, .price = 0},
    [ITEM_ULTRANECROZIUM_Z] = {.name = _("Ultranecrozium Z"), .description = _("Ultra burst item."), .pocket = POCKET_ITEMS, .price = 0},
};
''')
    _write(project / 'src/data/pokemon/form_species_tables.h', '''
static const u16 sVenusaurFormSpeciesIdTable[] = {
    SPECIES_VENUSAUR,
    SPECIES_VENUSAUR_MEGA,
    SPECIES_VENUSAUR_GMAX,
};
static const u16 sVulpixFormSpeciesIdTable[] = {
    SPECIES_VULPIX,
    SPECIES_VULPIX_ALOLA,
};
static const u16 sAlcremieFormSpeciesIdTable[] = {
    SPECIES_ALCREMIE,
    SPECIES_ALCREMIE_RUBY_CREAM,
};
''')
    _write(project / 'src/data/pokemon/form_change_tables.h', '''
static const struct FormChange sVenusaurFormChangeTable[] = {
    {FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM, SPECIES_VENUSAUR_MEGA, ITEM_VENUSAURITE},
    {FORM_CHANGE_BATTLE_GIGANTAMAX, SPECIES_VENUSAUR_GMAX},
    {FORM_CHANGE_TERMINATOR},
};
static const struct Fusion sNecrozmaFusionTable[] = {
    {1, ITEM_ULTRANECROZIUM_Z, SPECIES_NECROZMA, SPECIES_SOLGALEO, SPECIES_NECROZMA_DUSK_MANE, MOVE_TACKLE, 0},
    {FUSION_TERMINATOR},
};
static const struct FormChange sNecrozmaFormChangeTable[] = {
    {FORM_CHANGE_BATTLE_ULTRA_BURST, SPECIES_NECROZMA_ULTRA, ITEM_ULTRANECROZIUM_Z},
    {FORM_CHANGE_TERMINATOR},
};
''')
    _write(project / 'src/data/pokemon/teachable_learnsets.h', '''
static const u16 sVulpixTeachableLearnset[] = { MOVE_TACKLE, MOVE_FLAMETHROWER, TEACHABLE_LEARNSET_END };
static const u16 sVulpixAlolaTeachableLearnset[] = { MOVE_TACKLE, MOVE_ICE_BEAM, TEACHABLE_LEARNSET_END };
static const u16 sAlcremieTeachableLearnset[] = { MOVE_DAZZLING_GLEAM, TEACHABLE_LEARNSET_END };
static const u16 sAlcremieRubyCreamTeachableLearnset[] = { MOVE_DAZZLING_GLEAM, TEACHABLE_LEARNSET_END };
static const u16 sTestmonTeachableLearnset[] = { MOVE_TACKLE, MOVE_ICE_BEAM, TEACHABLE_LEARNSET_END };
''')
    _write(project / 'src/data/pokemon/species_info.h', '''
static const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_VENUSAUR] = {
        .genderRatio = PERCENT_FEMALE(12.5),
        .speciesName = _("Venusaur"),
        .categoryName = _("Seed"),
        .description = COMPOUND_STRING("A large plant dinosaur Pokémon."),
        .types = MON_TYPES(TYPE_GRASS),
        .abilities = { ABILITY_OVERGROW, ABILITY_NONE, ABILITY_CHLOROPHYLL },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FIELD),
        .natDexNum = NATIONAL_DEX_VENUSAUR,
        .baseHP = 80,
        .baseAttack = 82,
        .baseDefense = 83,
        .baseSpeed = 80,
        .baseSpAttack = 100,
        .baseSpDefense = 100,
        .height = 20,
        .weight = 1000,
        .teachableLearnset = sTestmonTeachableLearnset,
        .formSpeciesIdTable = sVenusaurFormSpeciesIdTable,
        .formChangeTable = sVenusaurFormChangeTable,
    },
    [SPECIES_VENUSAUR_MEGA] = {
        .speciesName = _("Venusaur"),
        .categoryName = _("Seed"),
        .description = COMPOUND_STRING("Mega Venusaur."),
        .types = MON_TYPES(TYPE_GRASS),
        .abilities = { ABILITY_OVERGROW },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FIELD),
        .natDexNum = NATIONAL_DEX_VENUSAUR,
        .baseSpecies = SPECIES_VENUSAUR,
        .formSpeciesIdTable = sVenusaurFormSpeciesIdTable,
        .formSpeciesIdTableIndex = 1,
        .baseHP = 80, .baseAttack = 100, .baseDefense = 123, .baseSpeed = 80, .baseSpAttack = 122, .baseSpDefense = 120,
        .height = 24, .weight = 1555,
    },
    [SPECIES_VENUSAUR_GMAX] = {
        .speciesName = _("Venusaur"),
        .categoryName = _("Seed"),
        .description = COMPOUND_STRING("Gigantamax Venusaur."),
        .types = MON_TYPES(TYPE_GRASS),
        .abilities = { ABILITY_OVERGROW, ABILITY_NONE, ABILITY_CHLOROPHYLL },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FIELD),
        .natDexNum = NATIONAL_DEX_VENUSAUR,
        .baseSpecies = SPECIES_VENUSAUR,
        .formSpeciesIdTable = sVenusaurFormSpeciesIdTable,
        .formSpeciesIdTableIndex = 2,
        .baseHP = 80, .baseAttack = 82, .baseDefense = 83, .baseSpeed = 80, .baseSpAttack = 100, .baseSpDefense = 100,
        .height = 240, .weight = 0,
    },
    [SPECIES_VULPIX] = {
        .speciesName = _("Vulpix"),
        .categoryName = _("Fox"),
        .description = COMPOUND_STRING("A fiery fox Pokémon."),
        .types = MON_TYPES(TYPE_FIRE),
        .abilities = { ABILITY_FLASH_FIRE },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FIELD),
        .natDexNum = NATIONAL_DEX_VULPIX,
        .baseHP = 38,
        .baseAttack = 41,
        .baseDefense = 40,
        .baseSpeed = 65,
        .baseSpAttack = 50,
        .baseSpDefense = 65,
        .height = 6,
        .weight = 99,
        .teachableLearnset = sVulpixTeachableLearnset,
        .formSpeciesIdTable = sVulpixFormSpeciesIdTable,
    },
    [SPECIES_VULPIX_ALOLA] = {
        .speciesName = _("Vulpix"),
        .categoryName = _("Fox"),
        .description = COMPOUND_STRING("A snowy fox Pokémon."),
        .types = MON_TYPES(TYPE_ICE),
        .abilities = { ABILITY_SNOW_CLOAK },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FIELD),
        .natDexNum = NATIONAL_DEX_VULPIX,
        .baseSpecies = SPECIES_VULPIX,
        .formSpeciesIdTable = sVulpixFormSpeciesIdTable,
        .formSpeciesIdTableIndex = 1,
        .baseHP = 38,
        .baseAttack = 41,
        .baseDefense = 40,
        .baseSpeed = 65,
        .baseSpAttack = 50,
        .baseSpDefense = 65,
        .height = 6,
        .weight = 99,
        .teachableLearnset = sVulpixAlolaTeachableLearnset,
    },
    [SPECIES_ALCREMIE] = {
        .speciesName = _("Alcremie"),
        .categoryName = _("Cream"),
        .description = COMPOUND_STRING("A whipped cream Pokémon."),
        .types = MON_TYPES(TYPE_FAIRY),
        .abilities = { ABILITY_SWEET_VEIL },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FAIRY),
        .natDexNum = NATIONAL_DEX_ALCREMIE,
        .baseHP = 65,
        .baseAttack = 60,
        .baseDefense = 75,
        .baseSpeed = 64,
        .baseSpAttack = 110,
        .baseSpDefense = 121,
        .height = 3,
        .weight = 5,
        .teachableLearnset = sAlcremieTeachableLearnset,
        .formSpeciesIdTable = sAlcremieFormSpeciesIdTable,
    },
    [SPECIES_ALCREMIE_RUBY_CREAM] = {
        .speciesName = _("Alcremie"),
        .categoryName = _("Cream"),
        .description = COMPOUND_STRING("A cosmetic flavor variant."),
        .types = MON_TYPES(TYPE_FAIRY),
        .abilities = { ABILITY_SWEET_VEIL },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FAIRY),
        .natDexNum = NATIONAL_DEX_ALCREMIE,
        .baseSpecies = SPECIES_ALCREMIE,
        .formSpeciesIdTable = sAlcremieFormSpeciesIdTable,
        .formSpeciesIdTableIndex = 1,
        .baseHP = 65,
        .baseAttack = 60,
        .baseDefense = 75,
        .baseSpeed = 64,
        .baseSpAttack = 110,
        .baseSpDefense = 121,
        .height = 3,
        .weight = 5,
        .teachableLearnset = sAlcremieRubyCreamTeachableLearnset,
    },
    [SPECIES_TESTMON] = {
        .speciesName = _("Testmon"),
        .categoryName = _("Debug"),
        .description = COMPOUND_STRING("A custom species."),
        .types = MON_TYPES(TYPE_NORMAL, TYPE_ICE),
        .abilities = { ABILITY_SNOW_CLOAK },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FIELD),
        .baseHP = 90,
        .baseAttack = 95,
        .baseDefense = 80,
        .baseSpeed = 70,
        .baseSpAttack = 85,
        .baseSpDefense = 75,
        .height = 18,
        .weight = 450,
        .teachableLearnset = sTestmonTeachableLearnset,
    },
};
''')
    _touch(project / 'graphics/pokemon/venusaur/front.png')
    _touch(project / 'graphics/pokemon/venusaur/icon.png')
    _touch(project / 'graphics/pokemon/vulpix/front.png')
    _touch(project / 'graphics/pokemon/vulpix/icon.png')
    _touch(project / 'graphics/pokemon/vulpix_alola/front.png')
    _touch(project / 'graphics/pokemon/vulpix_alola/icon.png')
    _touch(project / 'graphics/pokemon/alcremie/front.png')
    _touch(project / 'graphics/pokemon/alcremie/icon.png')
    _touch(project / 'graphics/pokemon/alcremie_ruby_cream/front.png')
    _touch(project / 'graphics/pokemon/alcremie_ruby_cream/icon.png')
    _touch(project / 'graphics/pokemon/testmon/front.png')
    _touch(project / 'graphics/pokemon/testmon/icon.png')
    return project


def test_showdown_export_generates_server_and_client_payloads(tmp_path: Path) -> None:
    project = _make_showdown_project(tmp_path)
    dist_dir = tmp_path / 'dist'
    export_dir = tmp_path / 'showdown-export'
    canonical = tmp_path / 'pokedex.ts'
    _write_canonical_pokedex(canonical)
    build_site(SiteConfig(project_dir=project, dist_dir=dist_dir, site_title='Test', showdown_export=True, showdown_export_dir=export_dir, showdown_canonical_pokedex_path=canonical))

    pokedex_text = (export_dir / 'server/data/mods/obstagoon/pokedex.ts').read_text(encoding='utf-8')
    learnsets_text = (export_dir / 'server/data/mods/obstagoon/learnsets.ts').read_text(encoding='utf-8')
    aliases_text = (export_dir / 'server/data/mods/obstagoon/aliases.ts').read_text(encoding='utf-8')
    manifest_text = (export_dir / 'client/assets/manifest.json').read_text(encoding='utf-8')

    assert pokedex_text.index('\tvenusaur: {') < pokedex_text.index('\tvulpix: {') < pokedex_text.index('\talcremie: {')
    assert '	vulpixalola: {' in pokedex_text
    assert 'name: "Vulpix-Alola"' in pokedex_text
    assert 'baseStats: {hp: 80, atk: 82, def: 83, spa: 100, spd: 100, spe: 80}' in pokedex_text
    assert 'heightm: 2,' in pokedex_text
    assert 'weightkg: 100,' in pokedex_text
    assert 'abilities: {0: "Overgrow", H: "Chlorophyll"}' in pokedex_text
    assert 'genderRatio: { M: 0.875, F: 0.125 }' in pokedex_text
    assert 'otherFormes: ["Venusaur-Mega"]' in pokedex_text
    assert 'formeOrder: ["Venusaur", "Venusaur-Mega"]' in pokedex_text
    assert 'canGigantamax: "G-Max Vine Lash"' in pokedex_text
    assert 'baseSpecies: "Venusaur"' in pokedex_text
    assert 'forme: "Gmax"' in pokedex_text
    assert 'requiredItem: "Venusaurite"' in pokedex_text
    assert 'changesFrom: "Venusaur"' in pokedex_text
    assert '	alcremierubycream: {' in pokedex_text
    assert '"alcremierubycream": "alcremie"' in aliases_text
    assert 'learnset: {tackle: ["9M"], icebeam: ["9M"]}' in learnsets_text or 'learnset: {icebeam: ["9M"], tackle: ["9M"]}' in learnsets_text
    assert 'assets/pokemon/vulpix.png' in manifest_text
    assert (export_dir / 'client/assets/pokemon/vulpix.png').exists()
    assert (export_dir / 'client/assets/icons/vulpix.png').exists()


def test_showdown_export_fixture_master_style_presence_and_cosmetic_omissions(tmp_path: Path) -> None:
    project = _make_showdown_project(tmp_path)
    export_dir = tmp_path / 'showdown-export'
    build_site(SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', showdown_export=True, showdown_export_dir=export_dir))

    pokedex_text = (export_dir / 'server/data/mods/obstagoon/pokedex.ts').read_text(encoding='utf-8')
    generated_keys = {
        line.strip()[:-3]
        for line in pokedex_text.splitlines()
        if line.strip().endswith(': {') and not line.strip().startswith('export const')
    }

    assert {'venusaur', 'venusaurmega', 'venusaurgmax', 'vulpix', 'vulpixalola', 'alcremie'}.issubset(generated_keys)
    assert {'testmon'}.issubset(generated_keys)
    assert 'alcremierubycream' in generated_keys



def test_generated_typescript_is_syntactically_valid(tmp_path: Path) -> None:
    project = _make_showdown_project(tmp_path)
    export_dir = tmp_path / 'showdown-export'
    build_site(SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', showdown_export=True, showdown_export_dir=export_dir))

    sim_dir = export_dir / 'server/sim'
    sim_dir.mkdir(parents=True, exist_ok=True)
    (sim_dir / 'dex.d.ts').write_text("""
export type ModdedBattleScriptsData = any;
export type AliasesTable = Record<string, string>;
""", encoding='utf-8')
    (sim_dir / 'dex-species.d.ts').write_text("""
export type ModdedSpeciesDataTable = Record<string, any>;
export type ModdedLearnsetDataTable = Record<string, any>;
export type ModdedSpeciesFormatsDataTable = Record<string, any>;
""", encoding='utf-8')
    (sim_dir / 'dex-moves.d.ts').write_text('export type ModdedMoveDataTable = Record<string, any>;\n', encoding='utf-8')
    (sim_dir / 'dex-abilities.d.ts').write_text('export type ModdedAbilityDataTable = Record<string, any>;\n', encoding='utf-8')
    (sim_dir / 'dex-items.d.ts').write_text('export type ModdedItemDataTable = Record<string, any>;\n', encoding='utf-8')
    tsconfig = export_dir / 'server/tsconfig.json'
    tsconfig.write_text('''
{
  "compilerOptions": {
    "strict": false,
    "target": "ES2020",
    "module": "commonjs",
    "skipLibCheck": true,
    "noEmit": true
  },
  "files": [
    "data/mods/obstagoon/scripts.ts",
    "data/mods/obstagoon/pokedex.ts",
    "data/mods/obstagoon/learnsets.ts",
    "data/mods/obstagoon/moves.ts",
    "data/mods/obstagoon/abilities.ts",
    "data/mods/obstagoon/items.ts",
    "data/mods/obstagoon/formats-data.ts",
    "data/mods/obstagoon/aliases.ts",
    "config/formats.obstagoon.generated.ts"
  ]
}
''', encoding='utf-8')

    subprocess.run(['tsc', '-p', str(tsconfig)], cwd=export_dir / 'server', check=True)


def test_showdown_export_defaults_to_dist_subdirectory(tmp_path: Path) -> None:
    project = _make_showdown_project(tmp_path)
    dist_dir = tmp_path / 'site-out'
    build_site(SiteConfig(project_dir=project, dist_dir=dist_dir, site_title='Test', showdown_export=True))

    export_dir = dist_dir.parent / 'showdown-export'
    assert export_dir.exists()
    assert (export_dir / 'server/data/mods/obstagoon/pokedex.ts').exists()


def test_showdown_export_verbose_message_includes_output_dir(tmp_path: Path, capsys) -> None:
    project = _make_showdown_project(tmp_path)
    dist_dir = tmp_path / 'dist'
    build_site(SiteConfig(project_dir=project, dist_dir=dist_dir, site_title='Test', showdown_export=True, verbose=True))

    captured = capsys.readouterr()
    expected = str((dist_dir.parent / 'showdown-export').resolve())
    assert 'SHOWDOWN EXPORT ENABLED' in captured.out
    assert expected in captured.out
    assert 'Showdown export complete' in captured.out


def test_showdown_export_bakes_in_showdown_normalization_without_canonical_fixture(tmp_path: Path) -> None:
    project = _make_showdown_project(tmp_path)
    export_dir = tmp_path / 'showdown-export'
    build_site(SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', showdown_export=True, showdown_export_dir=export_dir))

    pokedex_text = (export_dir / 'server/data/mods/obstagoon/pokedex.ts').read_text(encoding='utf-8')

    assert 'name: "Vulpix-Alola"' in pokedex_text
    assert 'name: "Venusaur-Mega"' in pokedex_text
    assert 'name: "Venusaur-Gmax"' in pokedex_text
    assert 'requiredItem: "Venusaurite"' in pokedex_text
    assert 'changesFrom: "Venusaur"' in pokedex_text
    assert 'canGigantamax: "G-Max Vine Lash"' in pokedex_text


def _parse_ts_entry_map(text: str) -> dict[str, str]:
    marker = 'export const Pokedex'
    start = text.find(marker)
    assert start >= 0
    brace_start = text.find('{', start)
    depth = 0
    in_string = False
    escape = False
    brace_end = -1
    for i in range(brace_start, len(text)):
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
                brace_end = i
                break
    assert brace_end >= 0
    body = text[brace_start + 1:brace_end]
    entries: dict[str, str] = {}
    i = 0
    while i < len(body):
        while i < len(body) and body[i].isspace():
            i += 1
        if i >= len(body):
            break
        import re
        m = re.match(r'([A-Za-z0-9_]+)\s*:\s*{', body[i:])
        if not m:
            i += 1
            continue
        key = m.group(1)
        entry_start = i
        entry_brace = i + m.end() - 1
        depth = 0
        in_string = False
        escape = False
        entry_end = -1
        for j in range(entry_brace, len(body)):
            ch = body[j]
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
                    entry_end = j
                    break
        assert entry_end >= 0
        k = entry_end + 1
        while k < len(body) and body[k].isspace():
            k += 1
        if k < len(body) and body[k] == ',':
            k += 1
        if k < len(body) and body[k] == '\n':
            k += 1
        entries[key] = body[entry_start:k]
        i = k
    return entries


def _ordered_species_fields(block: str) -> list[str]:
    import re
    return re.findall(r'^\t\t([A-Za-z0-9_]+):', block, flags=re.M)


def test_showdown_export_matches_official_field_schema(tmp_path: Path) -> None:
    project = _make_showdown_project(tmp_path)
    export_dir = tmp_path / 'showdown-export'
    build_site(SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', showdown_export=True, showdown_export_dir=export_dir))

    generated = (export_dir / 'server/data/mods/obstagoon/pokedex.ts').read_text(encoding='utf-8')
    official = (Path(__file__).parent / 'fixtures' / 'official_pokedex.ts').read_text(encoding='utf-8')

    generated_entries = _parse_ts_entry_map(generated)
    official_entries = _parse_ts_entry_map(official)

    overlap = sorted(set(generated_entries) & set(official_entries))
    assert overlap
    mismatches = [
        key for key in overlap
        if _ordered_species_fields(generated_entries[key]) != _ordered_species_fields(official_entries[key])
    ]
    assert mismatches == []

def test_showdown_export_overlays_existing_canonical_values_without_changing_field_set(tmp_path: Path) -> None:
    project = _make_showdown_project(tmp_path)
    export_dir = tmp_path / 'showdown-export'
    build_site(SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', showdown_export=True, showdown_export_dir=export_dir))
    pokedex_text = (export_dir / 'server/data/mods/obstagoon/pokedex.ts').read_text(encoding='utf-8')
    assert 'heightm: 2.0' in pokedex_text
    assert 'weightkg: 100.0' in pokedex_text
    assert 'eggGroups: ["Field"]' in pokedex_text
    fields = _ordered_species_fields(_parse_ts_entry_map(pokedex_text)['venusaur'])
    assert fields == _ordered_species_fields(_parse_ts_entry_map((Path(__file__).parent / 'fixtures' / 'official_pokedex.ts').read_text(encoding='utf-8'))['venusaur'])


def test_showdown_export_overlays_prevo_evos_and_evo_fields_when_present_in_canonical(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/constants/pokedex.h', '''
#define NATIONAL_DEX_BULBASAUR 1
#define NATIONAL_DEX_IVYSAUR 2

enum HoennDexOrder {
    HOENN_DEX_BULBASAUR,
    HOENN_DEX_IVYSAUR,
};
''')
    _write(project / 'src/data/types_info.h', '''
static const struct TypeInfo sTypeInfo[] = {
    [TYPE_GRASS] = {.name = _("Grass")},
};
''')
    _write(project / 'src/data/abilities.h', '''
static const struct Ability gAbilitiesInfo[] = {
    [ABILITY_OVERGROW] = {.name = _("Overgrow"), .description = _("Boosts Grass moves.")},
};
''')
    _write(project / 'src/data/moves_info.h', 'static const struct MoveInfo sMovesInfo[] = {};\n')
    _write(project / 'src/data/items.h', 'static const struct Item gItems[] = {};\n')
    _write(project / 'src/data/pokemon/species_info.h', '''
static const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_BULBASAUR] = {
        .speciesName = _("Bulbasaur"),
        .categoryName = _("Seed"),
        .description = COMPOUND_STRING("Bulbasaur."),
        .types = MON_TYPES(TYPE_GRASS),
        .abilities = { ABILITY_OVERGROW },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FIELD),
        .natDexNum = NATIONAL_DEX_BULBASAUR,
        .baseHP = 45, .baseAttack = 49, .baseDefense = 49, .baseSpeed = 45, .baseSpAttack = 65, .baseSpDefense = 65,
        .height = 7, .weight = 69,
        .evolutions = EVOLUTION({EVO_LEVEL, 22, SPECIES_IVYSAUR}),
    },
    [SPECIES_IVYSAUR] = {
        .speciesName = _("Ivysaur"),
        .categoryName = _("Seed"),
        .description = COMPOUND_STRING("Ivysaur."),
        .types = MON_TYPES(TYPE_GRASS),
        .abilities = { ABILITY_OVERGROW },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FIELD),
        .natDexNum = NATIONAL_DEX_IVYSAUR,
        .baseHP = 60, .baseAttack = 62, .baseDefense = 63, .baseSpeed = 60, .baseSpAttack = 80, .baseSpDefense = 80,
        .height = 10, .weight = 130,
    },
};
''')
    export_dir = tmp_path / 'showdown-export'
    canonical = tmp_path / 'pokedex.ts'
    _write(canonical, '''export const Pokedex = {
	bulbasaur: {
		num: 1,
		name: "Bulbasaur",
		types: ["Grass"],
		baseStats: {hp: 1, atk: 1, def: 1, spa: 1, spd: 1, spe: 1},
		abilities: {0: "Overgrow"},
		evos: ["Ivysaur"],
	},
	ivysaur: {
		num: 2,
		name: "Ivysaur",
		types: ["Grass"],
		baseStats: {hp: 1, atk: 1, def: 1, spa: 1, spd: 1, spe: 1},
		abilities: {0: "Overgrow"},
		prevo: "Bulbasaur",
		evoLevel: 16,
	},
};
''')
    build_site(SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', showdown_export=True, showdown_export_dir=export_dir, showdown_canonical_pokedex_path=canonical))
    pokedex_text = (export_dir / 'server/data/mods/obstagoon/pokedex.ts').read_text(encoding='utf-8')
    assert 'evos: ["Ivysaur"]' in pokedex_text
    assert 'prevo: "Bulbasaur"' in pokedex_text
    assert 'evoLevel: 22' in pokedex_text
