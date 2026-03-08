from pathlib import Path

from obstagoon.extract.c_utils import discover_project_defines, preprocess_conditionals, normalize_preprocessor_layout
from obstagoon.extract.parsers.species import parse_species


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_preprocessor_handles_else_endif_with_trailing_comments() -> None:
    text = '''
#if FOO
keep_a
#else // fallback branch
keep_b
#endif // end branch
keep_c
'''
    out = preprocess_conditionals(normalize_preprocessor_layout(text), {'FOO': 1})
    assert 'keep_a' in out
    assert 'keep_b' not in out
    assert 'keep_c' in out


def test_species_parser_resolves_family_macros_abilities_and_forms_with_commented_endifs(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/pokemon.h', '#define P_UPDATED_TYPES GEN_LATEST\n#define P_UPDATED_ABILITIES GEN_LATEST\n#define P_FAMILY_CLEFAIRY TRUE\n#define P_FAMILY_JIGGLYPUFF TRUE\n#define P_FAMILY_PIPLUP TRUE\n#define P_FAMILY_METAGROSS TRUE\n#define P_MEGA_EVOLUTIONS TRUE\n#define P_GEN_9_MEGA_EVOLUTIONS P_MEGA_EVOLUTIONS\n')
    _write(project / 'src/data/pokemon/species_info.h', '''
const struct SpeciesInfo gSpeciesInfo[] = {
#if P_FAMILY_CLEFAIRY
#if P_UPDATED_TYPES >= GEN_6
#define CLEFAIRY_FAMILY_TYPES { TYPE_FAIRY, TYPE_FAIRY }
#else // old typing
#define CLEFAIRY_FAMILY_TYPES { TYPE_NORMAL, TYPE_NORMAL }
#endif // P_UPDATED_TYPES
[SPECIES_CLEFAIRY] = { .speciesName = _("Clefairy"), #if P_UPDATED_ABILITIES >= GEN_4 .abilities = { ABILITY_CUTE_CHARM, ABILITY_MAGIC_GUARD, ABILITY_FRIEND_GUARD }, #else .abilities = { ABILITY_CUTE_CHARM, ABILITY_NONE, ABILITY_FRIEND_GUARD }, #endif .types = CLEFAIRY_FAMILY_TYPES, },
#if P_GEN_9_MEGA_EVOLUTIONS
[SPECIES_CLEFABLE_MEGA] = { .speciesName = _("Clefable"), .baseSpecies = SPECIES_CLEFABLE, .types = MON_TYPES(TYPE_FAIRY, TYPE_FLYING), },
#endif // P_GEN_9_MEGA_EVOLUTIONS
#endif // P_FAMILY_CLEFAIRY
#if P_FAMILY_JIGGLYPUFF
#if P_UPDATED_TYPES >= GEN_6
#define JIGGLYPUFF_FAMILY_TYPES { TYPE_NORMAL, TYPE_FAIRY }
#else // old typing
#define JIGGLYPUFF_FAMILY_TYPES { TYPE_NORMAL, TYPE_NORMAL }
#endif // P_UPDATED_TYPES
[SPECIES_JIGGLYPUFF] = { .speciesName = _("Jigglypuff"), .types = JIGGLYPUFF_FAMILY_TYPES, },
#endif // P_FAMILY_JIGGLYPUFF
#if P_FAMILY_PIPLUP
[SPECIES_EMPOLEON] = { .speciesName = _("Empoleon"), .types = MON_TYPES(TYPE_WATER, TYPE_STEEL), #if P_UPDATED_ABILITIES >= GEN_9 .abilities = { ABILITY_TORRENT, ABILITY_NONE, ABILITY_COMPETITIVE }, #else .abilities = { ABILITY_TORRENT, ABILITY_NONE, ABILITY_DEFIANT }, #endif },
#endif // P_FAMILY_PIPLUP
#if P_FAMILY_METAGROSS
[SPECIES_METAGROSS] = { .speciesName = _("Metagross"), .types = MON_TYPES(TYPE_STEEL, TYPE_PSYCHIC), },
#if P_MEGA_EVOLUTIONS
[SPECIES_METAGROSS_MEGA] = { .speciesName = _("Metagross"), .baseSpecies = SPECIES_METAGROSS, .types = MON_TYPES(TYPE_STEEL, TYPE_PSYCHIC), },
#endif // P_MEGA_EVOLUTIONS
#endif // P_FAMILY_METAGROSS
};
''')
    defines = discover_project_defines(str(project))
    species = parse_species(project, {}, {}, defines=defines)
    assert species['SPECIES_CLEFAIRY']['types'] == ['TYPE_FAIRY', 'TYPE_FAIRY']
    assert species['SPECIES_JIGGLYPUFF']['types'] == ['TYPE_NORMAL', 'TYPE_FAIRY']
    assert species['SPECIES_EMPOLEON']['abilities'][-1] == 'ABILITY_COMPETITIVE'
    assert 'SPECIES_METAGROSS_MEGA' in species
    assert 'SPECIES_CLEFABLE_MEGA' in species
