from __future__ import annotations

from pathlib import Path

from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.abilities import parse_abilities
from obstagoon.extract.parsers.learnsets import parse_learnsets
from obstagoon.extract.parsers.moves import parse_moves
from obstagoon.extract.parsers.species import parse_species
from obstagoon.extract.expansion_project import ExpansionProject
from obstagoon.model.builder import build_model


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"

    _write(project / "include/config/battle.h", """
#define B_UPDATED_MOVE_DATA GEN_2
""")
    _write(project / "include/config/pokemon.h", """
#define P_UPDATED_ABILITIES GEN_9
#define P_UPDATED_TYPES GEN_6
""")
    _write(project / "include/constants/pokedex.h", """
#define NATIONAL_DEX_EMPOLEON 395
#define NATIONAL_DEX_JIGGLYPUFF 39
""")
    _write(project / "src/data/types_info.h", """
static const u8 sTypeNames[][7] = {
    [TYPE_NORMAL] = _("Normal"),
    [TYPE_FAIRY] = _("Fairy"),
    [TYPE_WATER] = _("Water"),
    [TYPE_STEEL] = _("Steel"),
    [TYPE_DARK] = _("Dark"),
};
""")
    _write(project / "src/data/abilities.h", """
static const struct Ability gAbilitiesInfo[] = {
    [ABILITY_TORRENT] = {.name = _("Torrent"), .description = _("Boosts Water moves.")},
    [ABILITY_COMPETITIVE] = {.name = _("Competitive"), .description = _("Raises Sp. Atk when stats fall.")},
    [ABILITY_CUTE_CHARM] = {.name = _("Cute Charm"), .description = _("Infatuates on contact.")},
    [ABILITY_FRIEND_GUARD] = {.name = _("Friend Guard"), .description = _("Reduces allies' damage.")},
};
""")
    _write(project / "src/data/moves_info.h", """
static const struct MoveInfo sMovesInfo[] = {
    [MOVE_BITE] = {
        .name = _("Bite"),
        .description = _("Bites with sharp fangs."),
        .type = B_UPDATED_MOVE_DATA >= GEN_2 ? TYPE_DARK : TYPE_NORMAL,
        .power = 60,
        .accuracy = 100,
        .pp = 25,
        .category = DAMAGE_CATEGORY_PHYSICAL,
    },
};
""")
    _write(project / "src/data/pokemon/species_info.h", """
static const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_EMPOLEON] = {
        .speciesName = _("Empoleon"),
        .categoryName = _("Emperor"),
        .description = COMPOUND_STRING("The emperor penguin Pokémon."),
        .types = MON_TYPES(TYPE_WATER, TYPE_STEEL),
        .abilities = { ABILITY_TORRENT, ABILITY_NONE, P_UPDATED_ABILITIES >= GEN_9 ? ABILITY_COMPETITIVE : ABILITY_NONE },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_WATER_1, EGG_GROUP_FIELD),
        .growthRate = GROWTH_MEDIUM_SLOW,
        .natDexNum = NATIONAL_DEX_EMPOLEON,
        .levelUpLearnset = sEmpoleonLevelUpLearnset,
    },
    [SPECIES_JIGGLYPUFF] = {
        .speciesName = _("Jigglypuff"),
        .categoryName = _("Balloon"),
        .description = COMPOUND_STRING("It rolls around cutely."),
        .types = P_UPDATED_TYPES >= GEN_6 ? MON_TYPES(TYPE_NORMAL, TYPE_FAIRY) : MON_TYPES(TYPE_NORMAL),
        .abilities = { ABILITY_CUTE_CHARM, ABILITY_NONE, ABILITY_FRIEND_GUARD },
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_FAIRY),
        .growthRate = GROWTH_FAST,
        .natDexNum = NATIONAL_DEX_JIGGLYPUFF,
        .levelUpLearnset = B_UPDATED_MOVE_DATA >= GEN_2 ? sJigglypuffModernLevelUpLearnset : sJigglypuffClassicLevelUpLearnset,
    },
};
""")
    _write(project / "src/data/pokemon/level_up_learnsets.h", """
static const struct LevelUpMove sEmpoleonLevelUpLearnset[] = {
    LEVEL_UP_MOVE(1, MOVE_TACKLE),
    LEVEL_UP_MOVE(20, MOVE_BITE),
    LEVEL_UP_END
};
static const struct LevelUpMove sJigglypuffClassicLevelUpLearnset[] = {
    LEVEL_UP_MOVE(1, MOVE_POUND),
    LEVEL_UP_END
};
static const struct LevelUpMove sJigglypuffModernLevelUpLearnset[] = {
    LEVEL_UP_MOVE(1, MOVE_DISARMING_VOICE),
    LEVEL_UP_END
};
""")
    return project


def test_discover_project_defines_reads_generation_switches(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    defines = discover_project_defines(str(project))
    assert defines["P_UPDATED_ABILITIES"] == 9
    assert defines["P_UPDATED_TYPES"] == 6
    assert defines["B_UPDATED_MOVE_DATA"] == 2


def test_config_driven_species_moves_abilities_and_learnsets(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    defines = discover_project_defines(str(project))
    learnsets = parse_learnsets(project, defines=defines)
    species = parse_species(
        project,
        species_to_national={"SPECIES_EMPOLEON": 395, "SPECIES_JIGGLYPUFF": 39},
        learnsets=learnsets,
        defines=defines,
    )
    moves = parse_moves(project, defines=defines)
    abilities = parse_abilities(project, defines=defines)

    assert species["SPECIES_EMPOLEON"]["abilities"] == ["ABILITY_TORRENT", "ABILITY_NONE", "ABILITY_COMPETITIVE"]
    assert species["SPECIES_JIGGLYPUFF"]["types"] == ["TYPE_NORMAL", "TYPE_FAIRY"]
    assert species["SPECIES_JIGGLYPUFF"]["levelUpLearnset"] == [{"level": "1", "move": "MOVE_DISARMING_VOICE"}]

    assert moves["MOVE_BITE"]["type"] == "TYPE_DARK"
    assert moves["MOVE_BITE"]["category"] == "DAMAGE_CATEGORY_PHYSICAL"
    assert abilities["ABILITY_COMPETITIVE"]["name"] == "Competitive"

    model = build_model(ExpansionProject(project))
    assert model.species["SPECIES_EMPOLEON"].abilities == ["Torrent", "Competitive"]
    assert model.species["SPECIES_JIGGLYPUFF"].types == ["Normal", "Fairy"]
    assert model.moves["MOVE_BITE"].type == "Dark"
    assert model.moves["MOVE_BITE"].category == "Physical"


def test_species_shared_type_array_reference_resolves(tmp_path):
    from obstagoon.extract.parsers.species import parse_species

    project = tmp_path
    species_path = project / 'src/data/pokemon'
    species_path.mkdir(parents=True, exist_ok=True)
    (project / 'include').mkdir(exist_ok=True)
    (species_path / 'species_info.h').write_text(
        'static const u8 sJigglypuffFamilyTypes[] = { TYPE_NORMAL, TYPE_FAIRY };\n'
        '[SPECIES_JIGGLYPUFF] = {\n'
        '    .speciesName = _("Jigglypuff"),\n'
        '    .types = sJigglypuffFamilyTypes,\n'
        '    .abilities = { ABILITY_CUTE_CHARM, ABILITY_FRIEND_GUARD },\n'
        '}\n',
        encoding='utf-8'
    )
    result = parse_species(project, {'SPECIES_JIGGLYPUFF': 39}, {}, defines={})
    assert result['SPECIES_JIGGLYPUFF']['types'] == ['TYPE_NORMAL', 'TYPE_FAIRY']


def test_species_config_macro_family_types_resolve(tmp_path: Path) -> None:
    project = tmp_path / "proj_macro"
    _write(project / "include/config/pokemon.h", """
#define P_UPDATED_TYPES GEN_6
#define CLEFAIRY_FAMILY_TYPES P_UPDATED_TYPES >= GEN_6 ? MON_TYPES(TYPE_FAIRY) : MON_TYPES(TYPE_NORMAL)
#define JIGGLYPUFF_FAMILY_TYPES \
    P_UPDATED_TYPES >= GEN_6 ? MON_TYPES(TYPE_NORMAL, TYPE_FAIRY) : MON_TYPES(TYPE_NORMAL)
""")
    _write(project / "src/data/pokemon/species_info.h", """
static const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_CLEFAIRY] = {
        .speciesName = _("Clefairy"),
        .types = CLEFAIRY_FAMILY_TYPES,
        .abilities = { ABILITY_CUTE_CHARM },
    },
    [SPECIES_JIGGLYPUFF] = {
        .speciesName = _("Jigglypuff"),
        .types = JIGGLYPUFF_FAMILY_TYPES,
        .abilities = { ABILITY_CUTE_CHARM },
    },
};
""")
    defines = discover_project_defines(str(project))
    result = parse_species(project, {'SPECIES_CLEFAIRY': 35, 'SPECIES_JIGGLYPUFF': 39}, {}, defines=defines)
    assert result['SPECIES_CLEFAIRY']['types'] == ['TYPE_FAIRY']
    assert result['SPECIES_JIGGLYPUFF']['types'] == ['TYPE_NORMAL', 'TYPE_FAIRY']


def test_species_nested_config_macro_family_types_gen_latest(tmp_path: Path) -> None:
    project = tmp_path / "proj_nested_macro"
    _write(project / "include/config/pokemon.h", """
#define P_FAMILY_CLEFAIRY TRUE
#define P_FAMILY_JIGGLYPUFF TRUE
#define P_UPDATED_TYPES GEN_LATEST
#if P_FAMILY_CLEFAIRY
    #if P_UPDATED_TYPES >= GEN_6
        #define CLEFAIRY_FAMILY_TYPES { TYPE_FAIRY, TYPE_FAIRY }
    #else
        #define CLEFAIRY_FAMILY_TYPES { TYPE_NORMAL, TYPE_NORMAL }
    #endif
#endif
#if P_FAMILY_JIGGLYPUFF
    #if P_UPDATED_TYPES >= GEN_6
        #define JIGGLYPUFF_FAMILY_TYPES { TYPE_NORMAL, TYPE_FAIRY }
    #else
        #define JIGGLYPUFF_FAMILY_TYPES { TYPE_NORMAL, TYPE_NORMAL }
    #endif
#endif
""")
    _write(project / "src/data/pokemon/species_info.h", """
static const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_CLEFAIRY] = {
        .speciesName = _("Clefairy"),
        .types = CLEFAIRY_FAMILY_TYPES,
        .abilities = { ABILITY_CUTE_CHARM },
    },
    [SPECIES_JIGGLYPUFF] = {
        .speciesName = _("Jigglypuff"),
        .types = JIGGLYPUFF_FAMILY_TYPES,
        .abilities = { ABILITY_CUTE_CHARM },
    },
};
""")
    defines = discover_project_defines(str(project))
    assert defines["P_UPDATED_TYPES"] == defines["GEN_LATEST"] == 9
    result = parse_species(project, {'SPECIES_CLEFAIRY': 35, 'SPECIES_JIGGLYPUFF': 39}, {}, defines=defines)
    assert result['SPECIES_CLEFAIRY']['types'] == ['TYPE_FAIRY', 'TYPE_FAIRY']
    assert result['SPECIES_JIGGLYPUFF']['types'] == ['TYPE_NORMAL', 'TYPE_FAIRY']

def test_inline_minified_preprocessor_directives_in_species_files(tmp_path: Path) -> None:
    project = tmp_path / 'proj_minified'
    _write(project / 'include/config/pokemon.h', '#define P_UPDATED_TYPES GEN_LATEST\n#define P_UPDATED_ABILITIES GEN_LATEST\n')
    _write(project / 'include/config/species_enabled.h', '#define P_FAMILY_CLEFAIRY TRUE\n#define P_FAMILY_JIGGLYPUFF TRUE\n#define P_FAMILY_PIPLUP TRUE\n')
    _write(project / 'src/data/pokemon/species_info.h', '''
#include "gen_1_families.h"
#include "gen_4_families.h"
''')
    _write(project / 'src/data/pokemon/gen_1_families.h', '''
#if P_FAMILY_CLEFAIRY [SPECIES_CLEFAIRY] = { .speciesName = _("Clefairy"), #if P_UPDATED_TYPES >= GEN_6 .types = MON_TYPES(TYPE_FAIRY, TYPE_FAIRY), #else .types = MON_TYPES(TYPE_NORMAL, TYPE_NORMAL), #endif .abilities = { ABILITY_CUTE_CHARM, ABILITY_NONE, ABILITY_FRIEND_GUARD }, }, [SPECIES_JIGGLYPUFF] = { .speciesName = _("Jigglypuff"), #if P_UPDATED_TYPES >= GEN_6 .types = MON_TYPES(TYPE_NORMAL, TYPE_FAIRY), #else .types = MON_TYPES(TYPE_NORMAL, TYPE_NORMAL), #endif .abilities = { ABILITY_CUTE_CHARM, ABILITY_NONE, ABILITY_FRIEND_GUARD }, }, #endif
''')
    _write(project / 'src/data/pokemon/gen_4_families.h', '''
#if P_FAMILY_PIPLUP [SPECIES_EMPOLEON] = { .speciesName = _("Empoleon"), .types = MON_TYPES(TYPE_WATER, TYPE_STEEL), #if P_UPDATED_ABILITIES >= GEN_9 .abilities = { ABILITY_TORRENT, ABILITY_NONE, ABILITY_COMPETITIVE }, #else .abilities = { ABILITY_TORRENT, ABILITY_NONE, ABILITY_DEFIANT }, #endif }, #endif
''')
    defines = discover_project_defines(str(project))
    result = parse_species(project, {'SPECIES_CLEFAIRY':35,'SPECIES_JIGGLYPUFF':39,'SPECIES_EMPOLEON':395}, {}, defines=defines)
    assert result['SPECIES_CLEFAIRY']['types'] == ['TYPE_FAIRY', 'TYPE_FAIRY']
    assert result['SPECIES_JIGGLYPUFF']['types'] == ['TYPE_NORMAL', 'TYPE_FAIRY']
    assert result['SPECIES_EMPOLEON']['abilities'][-1] == 'ABILITY_COMPETITIVE'
