from pathlib import Path

from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.forms import parse_form_species_tables
from obstagoon.extract.parsers.species import parse_species


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_realistic_family_type_and_ability_switches(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/pokemon.h', """#define P_UPDATED_TYPES GEN_LATEST
#define P_UPDATED_ABILITIES GEN_LATEST
#define P_FAMILY_CLEFAIRY TRUE
#define P_FAMILY_JIGGLYPUFF TRUE
#define P_FAMILY_PIPLUP TRUE
""")
    _write(project / 'src/data/pokemon/species_info.h', """
const struct SpeciesInfo gSpeciesInfo[] = {
#if P_FAMILY_CLEFAIRY
#if P_UPDATED_TYPES >= GEN_6
    #define CLEFAIRY_FAMILY_TYPES { TYPE_FAIRY, TYPE_FAIRY }
#else
    #define CLEFAIRY_FAMILY_TYPES { TYPE_NORMAL, TYPE_NORMAL }
#endif
    [SPECIES_CLEFAIRY] =
    {
        .speciesName = _("Clefairy"),
        .types = CLEFAIRY_FAMILY_TYPES,
    },
#endif
#if P_FAMILY_JIGGLYPUFF
#if P_UPDATED_TYPES >= GEN_6
    #define JIGGLYPUFF_FAMILY_TYPES { TYPE_NORMAL, TYPE_FAIRY }
#else
    #define JIGGLYPUFF_FAMILY_TYPES { TYPE_NORMAL, TYPE_NORMAL }
#endif
    [SPECIES_JIGGLYPUFF] =
    {
        .speciesName = _("Jigglypuff"),
        .types = JIGGLYPUFF_FAMILY_TYPES,
    },
#endif
#if P_FAMILY_PIPLUP
    [SPECIES_EMPOLEON] =
    {
        .speciesName = _("Empoleon"),
    #if P_UPDATED_ABILITIES >= GEN_9
        .abilities = { ABILITY_TORRENT, ABILITY_NONE, ABILITY_COMPETITIVE },
    #else
        .abilities = { ABILITY_TORRENT, ABILITY_NONE, ABILITY_DEFIANT },
    #endif
    },
#endif
};
""")
    defines = discover_project_defines(str(project))
    species = parse_species(project, {}, {}, defines=defines)
    assert species['SPECIES_CLEFAIRY']['types'] == ['TYPE_FAIRY', 'TYPE_FAIRY']
    assert species['SPECIES_JIGGLYPUFF']['types'] == ['TYPE_NORMAL', 'TYPE_FAIRY']
    assert species['SPECIES_EMPOLEON']['abilities'][-1] == 'ABILITY_COMPETITIVE'


def test_form_tables_respect_enabled_form_defines(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/species_enabled.h', """#define P_MEGA_EVOLUTIONS TRUE
#define P_GIGANTAMAX_FORMS TRUE
""")
    _write(project / 'include/config/pokemon.h', '#include "config/species_enabled.h"\n')
    _write(project / 'src/data/pokemon/form_species_tables.h', """
#if P_MEGA_EVOLUTIONS
static const u16 sCharizardFormSpeciesIdTable[] = {
    SPECIES_CHARIZARD,
    SPECIES_CHARIZARD_MEGA_X,
    SPECIES_CHARIZARD_MEGA_Y,
#if P_GIGANTAMAX_FORMS
    SPECIES_CHARIZARD_GMAX,
#endif
    FORM_SPECIES_END,
};
#endif
#if P_MEGA_EVOLUTIONS
static const u16 sMetagrossFormSpeciesIdTable[] = {
    SPECIES_METAGROSS,
    SPECIES_METAGROSS_MEGA,
    FORM_SPECIES_END,
};
#endif
""")
    defines = discover_project_defines(str(project))
    tables = parse_form_species_tables(project, defines=defines)
    assert tables['sCharizardFormSpeciesIdTable'] == [
        'SPECIES_CHARIZARD',
        'SPECIES_CHARIZARD_MEGA_X',
        'SPECIES_CHARIZARD_MEGA_Y',
        'SPECIES_CHARIZARD_GMAX',
    ]
    assert tables['sMetagrossFormSpeciesIdTable'] == [
        'SPECIES_METAGROSS',
        'SPECIES_METAGROSS_MEGA',
    ]
