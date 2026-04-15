from pathlib import Path

from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.forms import parse_form_species_tables
from obstagoon.extract.parsers.species import parse_species


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_p_gen_9_mega_evolutions_aliases_p_mega_evolutions_from_same_config_file(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/pokemon.h', '''
#define P_MEGA_EVOLUTIONS TRUE
#define P_GEN_9_MEGA_EVOLUTIONS P_MEGA_EVOLUTIONS // Mega Evolutions introduced in Z-A and its DLC
#define P_FAMILY_CLEFAIRY TRUE
''')
    _write(project / 'src/data/pokemon/species_info.h', '#include "species_info/gen_1_families.h"\n')
    _write(project / 'src/data/pokemon/species_info/gen_1_families.h', '''
#if P_FAMILY_CLEFAIRY
[SPECIES_CLEFAIRY] =
{
    .speciesName = _("Clefairy"),
    .formSpeciesIdTable = sClefairyFormSpeciesIdTable,
},
#if P_GEN_9_MEGA_EVOLUTIONS
[SPECIES_CLEFABLE_MEGA] =
{
    .speciesName = _("Clefable"),
    .baseSpecies = SPECIES_CLEFAIRY,
    .formSpeciesIdTable = sClefairyFormSpeciesIdTable,
},
#endif
#endif
''')
    _write(project / 'src/data/pokemon/form_species_tables.h', '''
static const u16 sClefairyFormSpeciesIdTable[] = {
    SPECIES_CLEFAIRY,
    SPECIES_CLEFABLE_MEGA,
    SPECIES_NONE,
};
''')

    defines = discover_project_defines(str(project))
    assert defines['P_MEGA_EVOLUTIONS'] == 1
    assert defines['P_GEN_9_MEGA_EVOLUTIONS'] == 1

    species = parse_species(project, {'SPECIES_CLEFAIRY': 35, 'SPECIES_CLEFABLE_MEGA': 36}, {}, defines=defines)
    assert 'SPECIES_CLEFABLE_MEGA' in species
    assert species['SPECIES_CLEFABLE_MEGA']['baseSpecies'] == 'SPECIES_CLEFAIRY'

    tables = parse_form_species_tables(project, defines=defines)
    assert tables['sClefairyFormSpeciesIdTable'] == ['SPECIES_CLEFAIRY', 'SPECIES_CLEFABLE_MEGA']
