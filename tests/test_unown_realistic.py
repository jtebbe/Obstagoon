from pathlib import Path

from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.forms import parse_form_species_tables
from obstagoon.extract.parsers.learnsets import parse_learnsets
from obstagoon.extract.parsers.species import parse_species
from obstagoon.extract.parsers.types import parse_species_to_national
from obstagoon.model.builder import build_model


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_realistic_unown_macro_and_forms_are_present(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/pokemon.h', '#define P_FAMILY_UNOWN TRUE\n#define P_MEGA_EVOLUTIONS TRUE\n')
    _write(project / 'include/constants/pokedex.h', '#define NATIONAL_DEX_UNOWN 201\n#define NATIONAL_DEX_SCEPTILE 254\n')
    _write(project / 'src/data/pokemon/species_info.h', r'''
#define MON_TYPES(type1, ...) { type1, type1 }
#if P_FAMILY_UNOWN
#define UNOWN_MISC_INFO(letter, _noFlip, frontWidth, frontHeight, backWidth, backHeight, backYOffset)   \
    {                                                                                                   \
        .baseHP        = 48,                                                                            \
        .baseAttack    = 72,                                                                            \
        .baseDefense   = 48,                                                                            \
        .baseSpeed     = 48,                                                                            \
        .baseSpAttack  = 72,                                                                            \
        .baseSpDefense = 48,                                                                            \
        .types = MON_TYPES(TYPE_PSYCHIC),                                                               \
        .abilities = { ABILITY_LEVITATE, ABILITY_NONE, ABILITY_NONE },                                  \
        .speciesName = _("Unown"),                                                                      \
        .natDexNum = NATIONAL_DEX_UNOWN,                                                                \
        .categoryName = _("Symbol"),                                                                    \
        .description = gUnownPokedexText,                                                               \
        .frontPic = gMonFrontPic_Unown ##letter,                                                        \
        .backPic = gMonBackPic_Unown ##letter,                                                          \
        .iconSprite = gMonIcon_Unown ##letter,                                                          \
        .levelUpLearnset = sUnownLevelUpLearnset,                                                       \
        .teachableLearnset = sUnownTeachableLearnset,                                                   \
        .formSpeciesIdTable = sUnownFormSpeciesIdTable,                                                 \
    }
const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_UNOWN] = UNOWN_MISC_INFO(A, FALSE, 24, 40, 24, 48, 8),
    [SPECIES_UNOWN_B] = UNOWN_MISC_INFO(B, TRUE, 24, 32, 40, 48, 9),
    [SPECIES_UNOWN_C] = UNOWN_MISC_INFO(C, TRUE, 32, 32, 48, 56, 6),
#if P_MEGA_EVOLUTIONS
    [SPECIES_SCEPTILE] = {
        .speciesName = _("Sceptile"),
        .natDexNum = NATIONAL_DEX_SCEPTILE,
        .types = MON_TYPES(TYPE_GRASS),
        .abilities = { ABILITY_OVERGROW, ABILITY_NONE, ABILITY_UNBURDEN },
        .formSpeciesIdTable = sSceptileFormSpeciesIdTable,
    },
    [SPECIES_SCEPTILE_MEGA] = {
        .speciesName = _("Sceptile"),
        .natDexNum = NATIONAL_DEX_SCEPTILE,
        .types = MON_TYPES(TYPE_GRASS, TYPE_DRAGON),
        .abilities = { ABILITY_LIGHTNING_ROD, ABILITY_LIGHTNING_ROD, ABILITY_LIGHTNING_ROD },
        .formSpeciesIdTable = sSceptileFormSpeciesIdTable,
        .baseSpecies = SPECIES_SCEPTILE,
    },
#endif
};
#endif
''')
    _write(project / 'src/data/pokemon/form_species_tables.h', '''
#if P_FAMILY_UNOWN
static const u16 sUnownFormSpeciesIdTable[] = {
    SPECIES_UNOWN,
    SPECIES_UNOWN_B,
    SPECIES_UNOWN_C,
    FORM_SPECIES_END,
};
#endif
#if P_MEGA_EVOLUTIONS
static const u16 sSceptileFormSpeciesIdTable[] = {
    SPECIES_SCEPTILE,
    SPECIES_SCEPTILE_MEGA,
    FORM_SPECIES_END,
};
#endif
''')

    defines = discover_project_defines(str(project))
    species_to_national = parse_species_to_national(project)
    learnsets = parse_learnsets(project, defines=defines)
    species = parse_species(project, species_to_national, learnsets, defines=defines)
    tables = parse_form_species_tables(project, defines=defines)

    assert 'SPECIES_UNOWN' in species
    assert species['SPECIES_UNOWN']['graphics']['frontPic'] == 'gMonFrontPic_UnownA'
    assert tables['sUnownFormSpeciesIdTable'][:3] == ['SPECIES_UNOWN', 'SPECIES_UNOWN_B', 'SPECIES_UNOWN_C']
    assert 'SPECIES_SCEPTILE_MEGA' in species

    class P:
        def load_all(self):
            return {
                'types': {'TYPE_PSYCHIC': 'Psychic', 'TYPE_GRASS': 'Grass', 'TYPE_DRAGON': 'Dragon'},
                'species_to_national': species_to_national,
                'moves': {}, 'abilities': {}, 'items': {}, 'learnsets': learnsets,
                'species': species,
                'form_species_tables': tables,
                'sprites': {}, 'encounters': [], 'validation': {}, 'sprite_diagnostics': {},
            }

    model = build_model(P())
    assert model.national_to_species[201] == 'SPECIES_UNOWN'
    assert 'SPECIES_UNOWN_B' in model.species['SPECIES_UNOWN'].forms
    assert 'SPECIES_SCEPTILE_MEGA' in model.species['SPECIES_SCEPTILE'].forms
