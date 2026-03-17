from pathlib import Path

from obstagoon.extract.expansion_project import ExpansionProject


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_hoenn_sprite_candidates_keep_form_table_forms(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/constants/pokedex.h', 'enum HoennDexOrder { HOENN_DEX_TREECKO, HOENN_DEX_SCEPTILE, HOENN_DEX_DEOXYS, };')
    _write(project / 'src/data/pokemon/species_info.h', '''
#define _(x) x
const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_TREECKO] = {
        .speciesName = _("Treecko"),
        .types = { TYPE_GRASS },
        .abilities = { ABILITY_OVERGROW },
        .frontPic = gMonFrontPic_Treecko,
        .palette = gMonPalette_Treecko,
        .natDexNum = NATIONAL_DEX_TREECKO,
    },
    [SPECIES_SCEPTILE] = {
        .speciesName = _("Sceptile"),
        .types = { TYPE_GRASS },
        .abilities = { ABILITY_OVERGROW },
        .frontPic = gMonFrontPic_Sceptile,
        .palette = gMonPalette_Sceptile,
        .natDexNum = NATIONAL_DEX_SCEPTILE,
        .formSpeciesIdTable = sSceptileFormSpeciesIdTable,
    },
    [SPECIES_SCEPTILE_MEGA] = {
        .speciesName = _("Sceptile"),
        .types = { TYPE_GRASS },
        .abilities = { ABILITY_LIGHTNING_ROD },
        .frontPic = gMonFrontPic_SceptileMega,
        .palette = gMonPalette_SceptileMega,
        .natDexNum = NATIONAL_DEX_SCEPTILE,
        .formSpeciesIdTable = sSceptileFormSpeciesIdTable,
    },
};
''')
    _write(project / 'src/data/pokemon/form_species_tables.h', '''
static const u16 sSceptileFormSpeciesIdTable[] = {
    SPECIES_SCEPTILE,
    SPECIES_SCEPTILE_MEGA,
    FORM_SPECIES_END,
};
''')
    _write(project / 'src/data/pokemon/level_up_learnsets.h', '')
    _write(project / 'src/data/pokemon/teachable_learnsets.h', '')
    _write(project / 'src/data/pokemon/egg_moves.h', '')
    _write(project / 'src/data/graphics/pokemon.h', '')
    _write(project / 'graphics/pokemon/treecko/front.png', 'treecko')
    _write(project / 'graphics/pokemon/treecko/normal.pal', 'treecko-pal')
    _write(project / 'graphics/pokemon/sceptile/front.png', 'sceptile')
    _write(project / 'graphics/pokemon/sceptile/normal.pal', 'sceptile-pal')
    _write(project / 'graphics/pokemon/sceptile/mega/front.png', 'sceptile-mega')
    _write(project / 'graphics/pokemon/sceptile/mega/normal.pal', 'sceptile-mega-pal')

    raw = ExpansionProject(project, hoenn_dex=True).load_all()

    assert 'SPECIES_SCEPTILE_MEGA' in raw['sprites']
    assert raw['sprites']['SPECIES_SCEPTILE_MEGA']['frontPic'].endswith('graphics/pokemon/sceptile/mega/front.png')


def test_hoenn_sprite_candidates_resolve_deoxys_alias_to_normal_form(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/constants/pokedex.h', 'enum HoennDexOrder { HOENN_DEX_JIRACHI, HOENN_DEX_DEOXYS, };')
    _write(project / 'src/data/pokemon/species_info.h', '''
#define _(x) x
const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_JIRACHI] = {
        .speciesName = _("Jirachi"),
        .types = { TYPE_PSYCHIC },
        .abilities = { ABILITY_SERENE_GRACE },
        .frontPic = gMonFrontPic_Jirachi,
        .palette = gMonPalette_Jirachi,
        .natDexNum = NATIONAL_DEX_JIRACHI,
    },
    [SPECIES_DEOXYS_NORMAL] = {
        .speciesName = _("Deoxys"),
        .types = { TYPE_PSYCHIC },
        .abilities = { ABILITY_PRESSURE },
        .frontPic = gMonFrontPic_Deoxys,
        .palette = gMonPalette_Deoxys,
        .natDexNum = NATIONAL_DEX_DEOXYS,
        .formSpeciesIdTable = sDeoxysFormSpeciesIdTable,
    },
    [SPECIES_DEOXYS_ATTACK] = {
        .speciesName = _("Deoxys"),
        .types = { TYPE_PSYCHIC },
        .abilities = { ABILITY_PRESSURE },
        .frontPic = gMonFrontPic_DeoxysAttack,
        .palette = gMonPalette_DeoxysAttack,
        .natDexNum = NATIONAL_DEX_DEOXYS,
        .formSpeciesIdTable = sDeoxysFormSpeciesIdTable,
    },
};
''')
    _write(project / 'src/data/pokemon/form_species_tables.h', '''
static const u16 sDeoxysFormSpeciesIdTable[] = {
    SPECIES_DEOXYS_NORMAL,
    SPECIES_DEOXYS_ATTACK,
    FORM_SPECIES_END,
};
''')
    _write(project / 'src/data/pokemon/level_up_learnsets.h', '')
    _write(project / 'src/data/pokemon/teachable_learnsets.h', '')
    _write(project / 'src/data/pokemon/egg_moves.h', '')
    _write(project / 'src/data/graphics/pokemon.h', '')
    _write(project / 'graphics/pokemon/jirachi/front.png', 'jirachi')
    _write(project / 'graphics/pokemon/jirachi/normal.pal', 'jirachi-pal')
    _write(project / 'graphics/pokemon/deoxys/normal/front.png', 'deoxys-normal')
    _write(project / 'graphics/pokemon/deoxys/normal/normal.pal', 'deoxys-normal-pal')
    _write(project / 'graphics/pokemon/deoxys/attack/front.png', 'deoxys-attack')
    _write(project / 'graphics/pokemon/deoxys/attack/normal.pal', 'deoxys-attack-pal')

    raw = ExpansionProject(project, hoenn_dex=True).load_all()

    assert raw['hoenn_dex_order'] == ['SPECIES_JIRACHI', 'SPECIES_DEOXYS_NORMAL']
    assert 'SPECIES_DEOXYS' in raw['hoenn_dex_aliases']
    assert 'SPECIES_DEOXYS_NORMAL' in raw['sprites']
    assert raw['sprites']['SPECIES_DEOXYS_NORMAL']['frontPic'].endswith('graphics/pokemon/deoxys/normal/front.png')
