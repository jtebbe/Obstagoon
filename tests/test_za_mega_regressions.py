from pathlib import Path
from types import SimpleNamespace

from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.forms import parse_form_species_tables
from obstagoon.extract.parsers.species import parse_species
from obstagoon.model.builder import build_model
from obstagoon.normalize import infer_form_name


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_discover_project_defines_resolves_nested_gen_9_mega_include(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/species_enabled.h', '#define P_MEGA_EVOLUTIONS TRUE\n#define P_GEN_9_MEGA_EVOLUTIONS P_MEGA_EVOLUTIONS\n')
    _write(project / 'include/config/pokemon.h', '#include "config/species_enabled.h"\n#define P_FAMILY_CLEFAIRY TRUE\n')
    defines = discover_project_defines(str(project))
    assert defines['P_MEGA_EVOLUTIONS'] == 1
    assert defines['P_GEN_9_MEGA_EVOLUTIONS'] == 1


def test_parse_species_keeps_base_species_symbol_and_includes_gen_9_mega_forms(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/species_enabled.h', '#define P_MEGA_EVOLUTIONS TRUE\n#define P_GEN_9_MEGA_EVOLUTIONS P_MEGA_EVOLUTIONS\n')
    _write(project / 'include/config/pokemon.h', '#include "config/species_enabled.h"\n#define P_FAMILY_GARCHOMP TRUE\n')
    _write(project / 'src/data/pokemon/species_info.h', '#include "species_info/gen_4_families.h"\n')
    _write(project / 'src/data/pokemon/species_info/gen_4_families.h', '''
#if P_FAMILY_GARCHOMP
    [SPECIES_GARCHOMP] =
    {
        .speciesName = _("Garchomp"),
        .formSpeciesIdTable = sGarchompFormSpeciesIdTable,
    },
#if P_GEN_9_MEGA_EVOLUTIONS
    [SPECIES_GARCHOMP_MEGA_Z] =
    {
        .speciesName = _("Garchomp"),
        .baseSpecies = SPECIES_GARCHOMP,
        .formSpeciesIdTable = sGarchompFormSpeciesIdTable,
    },
#endif
#endif
''')
    _write(project / 'src/data/pokemon/form_species_tables.h', '''
static const u16 sGarchompFormSpeciesIdTable[] = {
    SPECIES_GARCHOMP,
    SPECIES_GARCHOMP_MEGA_Z,
    SPECIES_NONE,
};
''')
    defines = discover_project_defines(str(project))
    species = parse_species(project, {'SPECIES_GARCHOMP': 445, 'SPECIES_GARCHOMP_MEGA_Z': 445}, {}, defines=defines)
    assert 'SPECIES_GARCHOMP_MEGA_Z' in species
    assert species['SPECIES_GARCHOMP_MEGA_Z']['baseSpecies'] == 'SPECIES_GARCHOMP'
    tables = parse_form_species_tables(project, defines=defines)
    assert tables['sGarchompFormSpeciesIdTable'] == ['SPECIES_GARCHOMP', 'SPECIES_GARCHOMP_MEGA_Z']


def test_infer_form_name_preserves_mega_x_y_z() -> None:
    assert infer_form_name('SPECIES_RAICHU_MEGA_X', 'SPECIES_RAICHU') == 'Mega X'
    assert infer_form_name('SPECIES_RAICHU_MEGA_Y', 'SPECIES_RAICHU') == 'Mega Y'
    assert infer_form_name('SPECIES_GARCHOMP_MEGA_Z', 'SPECIES_GARCHOMP') == 'Mega Z'


def test_build_model_keeps_mega_z_form_name_and_slug_inputs() -> None:
    project = SimpleNamespace(load_all=lambda: {
        'species_to_national': {
            'SPECIES_GARCHOMP': 445,
            'SPECIES_GARCHOMP_MEGA_Z': 445,
        },
        'form_species_tables': {
            'sGarchompFormSpeciesIdTable': ['SPECIES_GARCHOMP', 'SPECIES_GARCHOMP_MEGA_Z'],
        },
        'species': {
            'SPECIES_GARCHOMP': {'speciesName': 'Garchomp', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': []},
            'SPECIES_GARCHOMP_MEGA_Z': {'speciesName': 'Garchomp', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': []},
        },
        'moves': {}, 'abilities': {}, 'items': {}, 'types': {}, 'encounters': [],
    })
    model = build_model(project)
    assert model.species['SPECIES_GARCHOMP_MEGA_Z'].form_name == 'Mega Z'
    assert 'SPECIES_GARCHOMP_MEGA_Z' in model.species['SPECIES_GARCHOMP'].forms
