from pathlib import Path

from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.species import parse_species


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_define_aliases_resolve_to_numeric_values(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/pokemon.h', '#define P_UPDATED_TYPES GEN_LATEST\n#define P_UPDATED_ABILITIES GEN_9\n')
    defines = discover_project_defines(str(project))
    assert defines['GEN_LATEST'] == 9
    assert defines['P_UPDATED_TYPES'] == 9
    assert defines['P_UPDATED_ABILITIES'] == 9


def test_species_config_and_forms_regression_cases(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/pokemon.h', '#define P_UPDATED_TYPES GEN_LATEST\n#define P_UPDATED_ABILITIES GEN_LATEST\n')
    _write(project / 'src/data/pokemon/species_info.h', '''
static const struct SpeciesInfo gSpeciesInfo[] = {
[SPECIES_CLEFAIRY] = { .speciesName = _("Clefairy"), .types = P_UPDATED_TYPES >= GEN_6 ? MON_TYPES(TYPE_FAIRY, TYPE_FAIRY) : MON_TYPES(TYPE_NORMAL, TYPE_NORMAL), .abilities = { ABILITY_CUTE_CHARM, ABILITY_NONE, ABILITY_FRIEND_GUARD }, },
[SPECIES_JIGGLYPUFF] = { .speciesName = _("Jigglypuff"), .types = P_UPDATED_TYPES >= GEN_6 ? MON_TYPES(TYPE_NORMAL, TYPE_FAIRY) : MON_TYPES(TYPE_NORMAL, TYPE_NORMAL), .abilities = { ABILITY_CUTE_CHARM, ABILITY_NONE, ABILITY_FRIEND_GUARD }, },
[SPECIES_EMPOLEON] = { .speciesName = _("Empoleon"), .types = MON_TYPES(TYPE_WATER, TYPE_STEEL), .abilities = { ABILITY_TORRENT, ABILITY_NONE, P_UPDATED_ABILITIES >= GEN_9 ? ABILITY_COMPETITIVE : ABILITY_DEFIANT }, },
[SPECIES_CHARIZARD] = { .speciesName = _("Charizard"), .types = MON_TYPES(TYPE_FIRE, TYPE_FLYING), .abilities = { ABILITY_BLAZE, ABILITY_NONE, ABILITY_SOLAR_POWER }, },
[SPECIES_CHARIZARD_MEGA_X] = { .speciesName = _("Charizard Mega X"), .baseSpecies = SPECIES_CHARIZARD, .types = MON_TYPES(TYPE_FIRE, TYPE_DRAGON), .abilities = { ABILITY_TOUGH_CLAWS }, },
};
''')
    defines = discover_project_defines(str(project))
    species = parse_species(project, {
        'SPECIES_CLEFAIRY': 35,
        'SPECIES_JIGGLYPUFF': 39,
        'SPECIES_EMPOLEON': 395,
        'SPECIES_CHARIZARD': 6,
        'SPECIES_CHARIZARD_MEGA_X': None,
    }, {}, defines=defines)
    assert species['SPECIES_CLEFAIRY']['types'] == ['TYPE_FAIRY', 'TYPE_FAIRY']
    assert species['SPECIES_JIGGLYPUFF']['types'] == ['TYPE_NORMAL', 'TYPE_FAIRY']
    assert species['SPECIES_EMPOLEON']['abilities'][-1] == 'ABILITY_COMPETITIVE'
    assert 'SPECIES_CHARIZARD_MEGA_X' in species
    assert species['SPECIES_CHARIZARD_MEGA_X']['baseSpecies'] == 'SPECIES_CHARIZARD'


def test_parenthesized_family_type_macros_resolve(tmp_path: Path) -> None:
    project = tmp_path / 'project'
    _write(project / 'include/config/pokemon.h', '#define P_UPDATED_TYPES GEN_LATEST\n#define P_FAMILY_RALTS TRUE\n#define P_FAMILY_TOGEPI TRUE\n')
    _write(project / 'src/data/pokemon/species_info.h', '''
#if P_FAMILY_RALTS
#define RALTS_FAMILY_TYPE2 (P_UPDATED_TYPES >= GEN_6 ? TYPE_FAIRY : TYPE_PSYCHIC)
[SPECIES_RALTS] = { .speciesName = _("Ralts"), .types = MON_TYPES(TYPE_PSYCHIC, RALTS_FAMILY_TYPE2), },
#endif
#if P_FAMILY_TOGEPI
#define TOGEPI_FAMILY_TYPE (P_UPDATED_TYPES >= GEN_6 ? TYPE_FAIRY : TYPE_NORMAL)
[SPECIES_TOGEPI] = { .speciesName = _("Togepi"), .types = MON_TYPES(TOGEPI_FAMILY_TYPE), },
#endif
''')
    defines = discover_project_defines(str(project))
    species = parse_species(project, {}, {}, defines=defines)
    assert species['SPECIES_RALTS']['types'] == ['TYPE_PSYCHIC', 'TYPE_FAIRY']
    assert species['SPECIES_TOGEPI']['types'] == ['TYPE_FAIRY']
