from pathlib import Path

from obstagoon.config import SiteConfig
from obstagoon.pipeline import build_site


def _write(path: Path, text: str = '') -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _touch(path: Path, data: bytes = b'x') -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_showdown_export_uses_raster_siblings_for_non_raster_bindings_and_symbol_ids(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/constants/pokedex.h', '#define NATIONAL_DEX_NIDORAN_F 29\n')
    _write(project / 'src/data/types_info.h', '''
static const struct TypeInfo sTypeInfo[] = {
    [TYPE_POISON] = {.name = _("Poison")},
};
''')
    _write(project / 'src/data/abilities.h', '''
static const struct Ability gAbilitiesInfo[] = {
    [ABILITY_POISON_POINT] = {.name = _("Poison Point"), .description = _("May poison on contact.")},
};
''')
    _write(project / 'src/data/moves_info.h', '''
static const struct MoveInfo sMovesInfo[] = {
    [MOVE_TACKLE] = {
        .name = _("Tackle"),
        .description = _("A physical attack."),
        .type = TYPE_POISON,
        .power = 40,
        .accuracy = 100,
        .pp = 35,
        .category = DAMAGE_CATEGORY_PHYSICAL,
    },
};
''')
    _write(project / 'src/data/items.h', 'static const struct Item gItems[] = {};\n')
    _write(project / 'src/data/pokemon/teachable_learnsets.h', '''
static const u16 sNidoranFTeachableLearnset[] = { MOVE_TACKLE, TEACHABLE_LEARNSET_END };
''')
    _write(project / 'src/data/pokemon/species_info.h', '''
static const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_NIDORAN_F] = {
        .speciesName = _("Nidoran♀"),
        .categoryName = _("Poison Pin"),
        .description = COMPOUND_STRING("A poisonous Pokemon."),
        .types = MON_TYPES(TYPE_POISON),
        .abilities = { ABILITY_POISON_POINT },
        .natDexNum = NATIONAL_DEX_NIDORAN_F,
        .baseHP = 55,
        .baseAttack = 47,
        .baseDefense = 52,
        .baseSpeed = 41,
        .baseSpAttack = 40,
        .baseSpDefense = 40,
        .frontPic = gMonFrontPic_NidoranF,
        .iconSprite = gMonIcon_NidoranF,
        .teachableLearnset = sNidoranFTeachableLearnset,
    },
};
''')
    _touch(project / 'graphics/pokemon/nidoran_f/front.4bpp.lz')
    _touch(project / 'graphics/pokemon/nidoran_f/front.png')
    _touch(project / 'graphics/pokemon/icon/nidoran_f.4bpp.lz')
    _touch(project / 'graphics/pokemon/icon/nidoran_f.png')

    export_dir = tmp_path / 'showdown-export'
    build_site(SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', showdown_export=True, showdown_export_dir=export_dir))

    assert (export_dir / 'client/assets/pokemon/nidoranf.png').exists()
    assert (export_dir / 'client/assets/icons/nidoranf.png').exists()
    pokedex_text = (export_dir / 'server/data/mods/obstagoon/pokedex.ts').read_text(encoding='utf-8')
    manifest_text = (export_dir / 'client/assets/manifest.json').read_text(encoding='utf-8')
    assert '	nidoranf: {' in pokedex_text
    assert 'assets/pokemon/nidoranf.png' in manifest_text
    assert 'assets/icons/nidoranf.png' in manifest_text


from obstagoon.generate.showdown import ShowdownExportGenerator
from obstagoon.model.schema import LearnsetBucket, ObstagoonModel, SpeciesRecord


def test_showdown_export_prefers_docs_rendered_front_asset(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    project.mkdir()
    dist = tmp_path / 'dist'
    rendered = dist / 'assets' / 'game' / 'graphics' / 'pokemon' / 'bulbasaur' / 'front.png'
    rendered.parent.mkdir(parents=True, exist_ok=True)
    rendered.write_bytes(b'rendered-front')

    species = SpeciesRecord(
        species_id='SPECIES_BULBASAUR',
        national_dex=1,
        name='Bulbasaur',
        types=['Grass'],
        abilities=['Overgrow'],
        learnsets=LearnsetBucket(),
        graphics={'frontPic': '../assets/game/graphics/pokemon/bulbasaur/front.png'},
    )
    model = ObstagoonModel(
        species={'SPECIES_BULBASAUR': species},
        moves={}, abilities={}, items={}, types={}, encounters=[], sprites=[],
        species_to_national={'SPECIES_BULBASAUR': 1}, national_to_species={1: 'SPECIES_BULBASAUR'},
        forms={}, trainers={}, metadata={},
    )
    config = SiteConfig(project_dir=project, dist_dir=dist, site_title='Test', showdown_export=True, showdown_export_dir=tmp_path / 'showdown-export')
    config.ensure()
    gen = ShowdownExportGenerator(config=config, model=model)
    gen._build_species_entries()

    resolved = gen._asset_source_for_record(species, 'frontPic')
    assert resolved == rendered.resolve()
