from pathlib import Path

from obstagoon.config import SiteConfig
from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.learnsets import parse_learnsets
from obstagoon.extract.parsers.species import parse_species
from obstagoon.extract.parsers.types import parse_species_to_national
from obstagoon.extract.parsers.sprites import parse_sprite_assets
from obstagoon.pipeline import build_site


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_macro_species_families_expand(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/pokemon.h', '#define P_FAMILY_FLABEBE TRUE\n#define P_FAMILY_VIVILLON TRUE\n')
    _write(project / 'include/constants/pokedex.h', '\n'.join([
        '#define NATIONAL_DEX_FLABEBE 669',
        '#define NATIONAL_DEX_FLOETTE 670',
        '#define NATIONAL_DEX_FLORGES 671',
        '#define NATIONAL_DEX_VIVILLON 666',
        '#define NATIONAL_DEX_MOTHIM 414',
    ]))
    _write(project / 'src/data/pokemon/species_info.h', r'''
#define MON_TYPES(type1, ...) { type1, __VA_ARGS__ }
#define MON_EGG_GROUPS(g1, ...) { g1, __VA_ARGS__ }
#if P_FAMILY_FLABEBE
#define FLABEBE_MISC_INFO(Form, FORM, iconPal) \
    .baseHP = 47, \
    .types = MON_TYPES(TYPE_FAIRY), \
    .abilities = { ABILITY_FLOWER_VEIL, ABILITY_NONE, ABILITY_SYMBIOSIS }, \
    .speciesName = _("Flabebe"), \
    .natDexNum = NATIONAL_DEX_FLABEBE, \
    .frontPic = gMonFrontPic_Flabebe, \
    .iconSprite = gMonIcon_Flabebe##Form, \
    .formSpeciesIdTable = sFlabebeFormSpeciesIdTable
#define FLOETTE_MISC_INFO(form, FORM, iconPal) \
    .types = MON_TYPES(TYPE_FAIRY), \
    .abilities = { ABILITY_FLOWER_VEIL, ABILITY_NONE, ABILITY_SYMBIOSIS }, \
    .speciesName = _("Floette"), \
    .natDexNum = NATIONAL_DEX_FLOETTE, \
    .iconSprite = gMonIcon_Floette##form, \
    .formSpeciesIdTable = sFloetteFormSpeciesIdTable
#define FLOETTE_NORMAL_INFO(form, FORM, iconPal) \
{ \
    .baseHP = 60, \
    .frontPic = gMonFrontPic_Floette, \
    FLOETTE_MISC_INFO(form, FORM, iconPal), \
}
#define FLORGES_MISC_INFO(Form, iconPal) \
    .baseHP = 78, \
    .types = MON_TYPES(TYPE_FAIRY), \
    .abilities = { ABILITY_FLOWER_VEIL, ABILITY_NONE, ABILITY_SYMBIOSIS }, \
    .speciesName = _("Florges"), \
    .natDexNum = NATIONAL_DEX_FLORGES, \
    .frontPic = gMonFrontPic_Florges, \
    .iconSprite = gMonIcon_Florges##Form, \
    .formSpeciesIdTable = sFlorgesFormSpeciesIdTable
#define VIVILLON_MISC_INFO(form, color, iconPal) \
{ \
    .baseHP = 80, \
    .types = MON_TYPES(TYPE_BUG, TYPE_FLYING), \
    .abilities = { ABILITY_SHIELD_DUST, ABILITY_COMPOUND_EYES, ABILITY_FRIEND_GUARD }, \
    .speciesName = _("Vivillon"), \
    .natDexNum = NATIONAL_DEX_VIVILLON, \
    .frontPic = gMonFrontPic_Vivillon##form, \
    .formSpeciesIdTable = sVivillonFormSpeciesIdTable, \
}
#define MOTHIM_SPECIES_INFO \
{ \
    .baseHP = 70, \
    .types = MON_TYPES(TYPE_BUG, TYPE_FLYING), \
    .abilities = { ABILITY_SHIELD_DUST, ABILITY_TINTED_LENS, ABILITY_COVETOUS }, \
    .speciesName = _("Mothim"), \
    .natDexNum = NATIONAL_DEX_MOTHIM, \
    .frontPic = gMonFrontPic_Mothim, \
}
const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_FLABEBE_RED_FLOWER] = { FLABEBE_MISC_INFO(RedFlower, RED_FLOWER, 0), },
    [SPECIES_FLOETTE_RED_FLOWER] = FLOETTE_NORMAL_INFO(RedFlower, RED_FLOWER, 0),
    [SPECIES_FLORGES_RED_FLOWER] = { FLORGES_MISC_INFO(RedFlower, 0), },
    [SPECIES_VIVILLON_ICY_SNOW_PATTERN] = VIVILLON_MISC_INFO(IcySnow, _("Icy Snow"), 0),
    [SPECIES_MOTHIM] = MOTHIM_SPECIES_INFO,
};
#endif
''')
    _write(project / 'src/data/pokemon/form_species_tables.h', '''
static const u16 sFlabebeFormSpeciesIdTable[] = { SPECIES_FLABEBE_RED_FLOWER, FORM_SPECIES_END };
static const u16 sFloetteFormSpeciesIdTable[] = { SPECIES_FLOETTE_RED_FLOWER, SPECIES_FLOETTE_ETERNAL, FORM_SPECIES_END };
static const u16 sFlorgesFormSpeciesIdTable[] = { SPECIES_FLORGES_RED_FLOWER, FORM_SPECIES_END };
static const u16 sVivillonFormSpeciesIdTable[] = { SPECIES_VIVILLON_ICY_SNOW_PATTERN, FORM_SPECIES_END };
''')
    defines = discover_project_defines(str(project))
    species_to_national = parse_species_to_national(project)
    learnsets = parse_learnsets(project, defines=defines)
    species = parse_species(project, species_to_national, learnsets, defines=defines)
    assert 'SPECIES_FLABEBE_RED_FLOWER' in species
    assert 'SPECIES_FLOETTE_RED_FLOWER' in species
    assert 'SPECIES_FLORGES_RED_FLOWER' in species
    assert 'SPECIES_VIVILLON_ICY_SNOW_PATTERN' in species
    assert 'SPECIES_MOTHIM' in species
    assert species['SPECIES_FLORGES_RED_FLOWER']['speciesName'] == 'Florges'
    assert species['SPECIES_VIVILLON_ICY_SNOW_PATTERN']['graphics']['frontPic'] == 'gMonFrontPic_VivillonIcySnow'


def test_sprite_prefers_anim_front_and_plain_front(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'graphics/pokemon/pikachu').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/pikachu').joinpath('anim_front.png').write_text('x')
    (project / 'graphics/pokemon/pikachu/world').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/pikachu/world/front.png').write_text('x')
    (project / 'graphics/pokemon/ogerpon').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/ogerpon/front.png').write_text('x')
    (project / 'graphics/pokemon/ogerpon_teal_tera').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/ogerpon_teal_tera/front.png').write_text('x')
    species = {
        'SPECIES_PIKACHU': {'speciesName': 'Pikachu', 'graphics': {'frontPic': 'gMonFrontPic_Pikachu'}},
        'SPECIES_OGERPON': {'speciesName': 'Ogerpon', 'graphics': {'frontPic': 'gMonFrontPic_Ogerpon'}},
        'SPECIES_BASCULEGION_M': {'speciesName': 'Basculegion M', 'graphics': {'frontPic': 'gMonFrontPic_BasculegionM'}},
    }
    (project / 'graphics/pokemon/basculegion_m').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/basculegion_m/anim_front.png').write_text('x')
    (project / 'graphics/pokemon/nidoran_m/anim_front.png').parent.mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/nidoran_m/anim_front.png').write_text('x')
    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_PIKACHU']['frontPic'].endswith('graphics/pokemon/pikachu/anim_front.png')
    assert sprites['SPECIES_OGERPON']['frontPic'].endswith('graphics/pokemon/ogerpon/front.png')
    assert sprites['SPECIES_BASCULEGION_M']['frontPic'].endswith('graphics/pokemon/basculegion_m/anim_front.png')
