from pathlib import Path

from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.species import parse_species
from obstagoon.extract.parsers.sprites import _build_lookup_index, _resolve_path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_species_stat_macro_resolves_from_local_conditional_define(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/pokemon.h', '#define P_UPDATED_STATS GEN_LATEST\n')
    _write(project / 'src/data/pokemon/species_info.h', '''
#if P_UPDATED_STATS >= GEN_6
#define WIGGLYTUFF_SP_ATK 85
#elif P_UPDATED_STATS >= GEN_2
#define WIGGLYTUFF_SP_ATK 75
#else
#define WIGGLYTUFF_SP_ATK 50
#endif
const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_WIGGLYTUFF] =
    {
        .speciesName = _("Wigglytuff"),
        .baseSpAttack = WIGGLYTUFF_SP_ATK,
    },
};
''')
    defines = discover_project_defines(str(project))
    species = parse_species(project, {}, {}, defines=defines)
    assert species['SPECIES_WIGGLYTUFF']['stats']['baseSpAttack'] == '85'


def test_pikachu_base_anim_front_beats_world_variant(tmp_path: Path) -> None:
    base = tmp_path / 'graphics' / 'pokemon' / 'pikachu'
    world = tmp_path / 'graphics' / 'pokemon' / 'pikachu_world'
    base.mkdir(parents=True)
    world.mkdir(parents=True)
    anim_front = base / 'anim_front.png'
    world_front = world / 'front.png'
    anim_front.write_text('x')
    world_front.write_text('x')
    idx = _build_lookup_index(tmp_path, [anim_front, world_front])
    resolved, _ = _resolve_path(tmp_path, idx, 'SPECIES_PIKACHU', 'frontPic', 'gMonFrontPic_Pikachu')
    assert resolved == 'graphics/pokemon/pikachu/anim_front.png'
