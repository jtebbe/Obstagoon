from pathlib import Path

from obstagoon.config import SiteConfig
from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.learnsets import parse_learnsets
from obstagoon.extract.parsers.species import parse_species
from obstagoon.extract.parsers.types import parse_species_to_national
from obstagoon.model.builder import build_model
from obstagoon.pipeline import build_site


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_unown_macro_species_parses_and_renders(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/pokemon.h', '#define P_FAMILY_UNOWN TRUE\n')
    _write(project / 'include/constants/pokedex.h', '#define NATIONAL_DEX_UNOWN 201\n#define NATIONAL_DEX_PIKACHU 25\n')
    _write(project / 'src/data/pokemon/form_species_tables.h', '''
static const u16 sUnownFormSpeciesIdTable[] = {
    SPECIES_UNOWN_A,
    SPECIES_UNOWN_B,
    FORM_SPECIES_END,
};
''')
    _write(project / 'src/data/pokemon/species_info.h', r'''
#define MON_TYPES(type1, ...) { type1, type1 }
#if P_FAMILY_UNOWN
#define UNOWN_MISC_INFO(letter, _noFlip, frontWidth, frontHeight, backWidth, backHeight, backYOffset) \
    { \
        .baseHP = 65, \
        .baseAttack = 72, \
        .baseDefense = 48, \
        .baseSpeed = 48, \
        .baseSpAttack = 72, \
        .baseSpDefense = 48, \
        .types = MON_TYPES(TYPE_PSYCHIC), \
        .abilities = { ABILITY_LEVITATE, ABILITY_NONE, ABILITY_NONE }, \
        .speciesName = _("Unown"), \
        .natDexNum = NATIONAL_DEX_UNOWN, \
        .categoryName = _("Symbol"), \
        .description = _("A hidden power Pokemon."), \
        .frontPic = gMonFrontPic_Unown ## letter, \
        .backPic = gMonBackPic_Unown ## letter, \
        .iconSprite = gMonIcon_Unown ## letter, \
        .levelUpLearnset = sUnownLevelUpLearnset, \
        .teachableLearnset = sUnownTeachableLearnset, \
        .formSpeciesIdTable = sUnownFormSpeciesIdTable, \
    }
const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_UNOWN_A] = UNOWN_MISC_INFO(A, NO_FLIP, 24, 24, 24, 24, 0),
    [SPECIES_UNOWN_B] = UNOWN_MISC_INFO(B, NO_FLIP, 24, 24, 24, 24, 0),
    [SPECIES_PIKACHU] = {
        .speciesName = _("Pikachu"),
        .natDexNum = NATIONAL_DEX_PIKACHU,
        .types = MON_TYPES(TYPE_ELECTRIC),
        .abilities = { ABILITY_STATIC, ABILITY_NONE, ABILITY_LIGHTNING_ROD },
        .frontPic = gMonFrontPic_Pikachu,
        .iconSprite = gMonIcon_Pikachu,
        .description = _("Pikachu desc."),
        .categoryName = _("Mouse"),
    },
};
#endif
''')
    _write(project / 'graphics/pokemon/unown/anim_front.png', 'x')
    _write(project / 'graphics/pokemon/unown_a/anim_front.png', 'x')
    _write(project / 'graphics/pokemon/unown_b/anim_front.png', 'x')
    _write(project / 'graphics/pokemon/pikachu/anim_front.png', 'x')

    defines = discover_project_defines(str(project))
    species_to_national = parse_species_to_national(project)
    learnsets = parse_learnsets(project, defines=defines)
    species = parse_species(project, species_to_national, learnsets, defines=defines)

    assert 'SPECIES_UNOWN_A' in species
    assert 'SPECIES_UNOWN_B' in species
    assert species['SPECIES_UNOWN_A']['speciesName'] == 'Unown'
    assert species['SPECIES_UNOWN_A']['graphics']['frontPic'] == 'gMonFrontPic_UnownA'
    assert species_to_national['SPECIES_UNOWN_A'] == 201

    class P:
        def load_all(self):
            return {
                'types': {'TYPE_PSYCHIC': 'Psychic', 'TYPE_ELECTRIC': 'Electric'},
                'species_to_national': species_to_national,
                'moves': {}, 'abilities': {}, 'items': {}, 'learnsets': learnsets,
                'species': species,
                'form_species_tables': {'sUnownFormSpeciesIdTable': ['SPECIES_UNOWN_A', 'SPECIES_UNOWN_B']},
                'sprites': {}, 'encounters': [], 'validation': {}, 'sprite_diagnostics': {},
            }

    model = build_model(P())
    assert model.national_to_species[201] == 'SPECIES_UNOWN_A'
    assert 'SPECIES_UNOWN_B' in model.species['SPECIES_UNOWN_A'].forms

    dist = tmp_path / 'dist'
    build_site(SiteConfig(project_dir=project, dist_dir=dist, site_title='test', documentation=True))
    pokedex = (dist / 'pokedex' / 'index.html').read_text(encoding='utf-8')
    species_page = (dist / 'pokedex' / 'unown-a.html').read_text(encoding='utf-8')
    assert 'Unown' in pokedex
    assert 'unown-b.html' in species_page
