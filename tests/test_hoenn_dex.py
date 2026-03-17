from pathlib import Path

from obstagoon.config import SiteConfig
from obstagoon.extract.c_utils import discover_project_defines
from obstagoon.extract.parsers.species import parse_species
from obstagoon.extract.parsers.types import parse_hoenn_dex_order
from obstagoon.model.builder import build_model


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_disabled_family_species_are_skipped(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/species_enabled.h', '#define P_FAMILY_BULBASAUR FALSE\n#define P_FAMILY_PIKACHU TRUE\n')
    _write(project / 'src/data/pokemon/species_info.h', '''
#if P_FAMILY_BULBASAUR
[SPECIES_BULBASAUR] = {
    .speciesName = _("Bulbasaur"),
    .abilities = { ABILITY_OVERGROW },
},
#endif
#if P_FAMILY_PIKACHU
[SPECIES_PIKACHU] = {
    .speciesName = _("Pikachu"),
    .abilities = { ABILITY_STATIC },
},
#endif
''')
    defines = discover_project_defines(str(project))
    species = parse_species(project, {'SPECIES_BULBASAUR': 1, 'SPECIES_PIKACHU': 25}, {}, defines=defines)
    assert 'SPECIES_BULBASAUR' not in species
    assert 'SPECIES_PIKACHU' in species


def test_parse_hoenn_dex_order_respects_config_flags(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    _write(project / 'include/config/species_enabled.h', '''
#define P_NEW_EVOS_IN_REGIONAL_DEX TRUE
#define P_GEN_4_CROSS_EVOS TRUE
#define P_GALARIAN_FORMS FALSE
''')
    _write(project / 'include/constants/pokedex.h', '''
enum HoennDexOrder
{
    HOENN_DEX_TREECKO,
#if P_NEW_EVOS_IN_REGIONAL_DEX && P_GEN_4_CROSS_EVOS
    HOENN_DEX_RHYPERIOR,
#endif
#if P_NEW_EVOS_IN_REGIONAL_DEX && P_GALARIAN_FORMS
    HOENN_DEX_CURSOLA,
#endif
    HOENN_DEX_DEOXYS,
};
''')
    defines = discover_project_defines(str(project))
    order = parse_hoenn_dex_order(project, defines=defines)
    assert order == ['SPECIES_TREECKO', 'SPECIES_RHYPERIOR', 'SPECIES_DEOXYS']


class _StubProject:
    def __init__(self, raw: dict, hoenn_dex: bool = False) -> None:
        self._raw = raw
        self.hoenn_dex = hoenn_dex

    def load_all(self) -> dict:
        return self._raw


def test_build_model_hoenn_dex_filters_and_reorders_species() -> None:
    raw = {
        'types': {'TYPE_GRASS': 'Grass', 'TYPE_FIRE': 'Fire', 'TYPE_PSYCHIC': 'Psychic', 'TYPE_ELECTRIC': 'Electric'},
        'species_to_national': {
            'SPECIES_TREECKO': 252,
            'SPECIES_TORCHIC': 255,
            'SPECIES_DEOXYS': 386,
            'SPECIES_PIKACHU': 25,
        },
        'hoenn_dex_order': ['SPECIES_TREECKO', 'SPECIES_TORCHIC', 'SPECIES_DEOXYS'],
        'form_species_tables': {},
        'species': {
            'SPECIES_TREECKO': {'speciesName': 'Treecko', 'types': ['TYPE_GRASS'], 'abilities': ['ABILITY_OVERGROW'], 'graphics': {}},
            'SPECIES_TORCHIC': {'speciesName': 'Torchic', 'types': ['TYPE_FIRE'], 'abilities': ['ABILITY_BLAZE'], 'graphics': {}},
            'SPECIES_DEOXYS': {'speciesName': 'Deoxys', 'types': ['TYPE_PSYCHIC'], 'abilities': ['ABILITY_PRESSURE'], 'graphics': {}},
            'SPECIES_PIKACHU': {'speciesName': 'Pikachu', 'types': ['TYPE_ELECTRIC'], 'abilities': ['ABILITY_STATIC'], 'graphics': {}},
        },
        'moves': {},
        'abilities': {},
        'items': {},
        'encounters': [],
        'trainers': [],
        'validation': {},
        'sprite_diagnostics': {},
    }
    model = build_model(_StubProject(raw, hoenn_dex=True))
    assert list(model.national_to_species.items()) == [(1, 'SPECIES_TREECKO'), (2, 'SPECIES_TORCHIC'), (3, 'SPECIES_DEOXYS')]
    assert set(model.species) == {'SPECIES_TREECKO', 'SPECIES_TORCHIC', 'SPECIES_DEOXYS'}
    assert model.metadata['dex_mode'] == 'hoenn'
    assert model.metadata['dex_label'] == 'Hoenn Dex #'


def test_build_model_hoenn_dex_forms_share_base_dex_number() -> None:
    raw = {
        'types': {'TYPE_GRASS': 'Grass'},
        'species_to_national': {
            'SPECIES_TREECKO': 252,
            'SPECIES_SCEPTILE': 254,
            'SPECIES_SCEPTILE_MEGA': 10034,
        },
        'hoenn_dex_order': ['SPECIES_TREECKO', 'SPECIES_SCEPTILE'],
        'form_species_tables': {'sSceptileFormSpeciesIdTable': ['SPECIES_SCEPTILE', 'SPECIES_SCEPTILE_MEGA']},
        'species': {
            'SPECIES_TREECKO': {'speciesName': 'Treecko', 'types': ['TYPE_GRASS'], 'abilities': ['ABILITY_OVERGROW'], 'graphics': {}},
            'SPECIES_SCEPTILE': {'speciesName': 'Sceptile', 'types': ['TYPE_GRASS'], 'abilities': ['ABILITY_OVERGROW'], 'graphics': {}},
            'SPECIES_SCEPTILE_MEGA': {'speciesName': 'Sceptile', 'baseSpecies': 'SPECIES_SCEPTILE', 'types': ['TYPE_GRASS'], 'abilities': ['ABILITY_LIGHTNING_ROD'], 'graphics': {}},
        },
        'moves': {}, 'abilities': {}, 'items': {}, 'encounters': [], 'trainers': [], 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(_StubProject(raw, hoenn_dex=True))
    assert model.metadata['active_dex_map']['SPECIES_SCEPTILE'] == 2
    assert model.metadata['active_dex_map']['SPECIES_SCEPTILE_MEGA'] == 2


def test_build_model_hoenn_dex_keeps_deoxys_when_order_ends_with_base_species_with_forms() -> None:
    raw = {
        'types': {'TYPE_PSYCHIC': 'Psychic'},
        'species_to_national': {
            'SPECIES_JIRACHI': 385,
            'SPECIES_DEOXYS': 386,
            'SPECIES_DEOXYS_ATTACK': 10001,
        },
        'hoenn_dex_order': ['SPECIES_JIRACHI', 'SPECIES_DEOXYS'],
        'form_species_tables': {'sDeoxysFormSpeciesIdTable': ['SPECIES_DEOXYS', 'SPECIES_DEOXYS_ATTACK']},
        'species': {
            'SPECIES_JIRACHI': {'speciesName': 'Jirachi', 'types': ['TYPE_PSYCHIC'], 'abilities': ['ABILITY_SERENE_GRACE'], 'graphics': {}},
            'SPECIES_DEOXYS': {'speciesName': 'Deoxys', 'types': ['TYPE_PSYCHIC'], 'abilities': ['ABILITY_PRESSURE'], 'graphics': {}},
            'SPECIES_DEOXYS_ATTACK': {'speciesName': 'Deoxys', 'baseSpecies': 'SPECIES_DEOXYS', 'types': ['TYPE_PSYCHIC'], 'abilities': ['ABILITY_PRESSURE'], 'graphics': {}},
        },
        'moves': {}, 'abilities': {}, 'items': {}, 'encounters': [], 'trainers': [], 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(_StubProject(raw, hoenn_dex=True))
    assert list(model.national_to_species.items())[-1] == (2, 'SPECIES_DEOXYS')
    assert model.metadata['active_dex_map']['SPECIES_DEOXYS_ATTACK'] == 2


def test_build_model_hoenn_dex_resolves_deoxys_enum_symbol_to_normal_form() -> None:
    raw = {
        'types': {'TYPE_PSYCHIC': 'Psychic'},
        'species_to_national': {
            'SPECIES_JIRACHI': 385,
            'SPECIES_DEOXYS_NORMAL': 386,
            'SPECIES_DEOXYS_ATTACK': 386,
        },
        'hoenn_dex_order': ['SPECIES_JIRACHI', 'SPECIES_DEOXYS'],
        'form_species_tables': {'sDeoxysFormSpeciesIdTable': ['SPECIES_DEOXYS_NORMAL', 'SPECIES_DEOXYS_ATTACK']},
        'species': {
            'SPECIES_JIRACHI': {'speciesName': 'Jirachi', 'types': ['TYPE_PSYCHIC'], 'abilities': ['ABILITY_SERENE_GRACE'], 'graphics': {}},
            'SPECIES_DEOXYS_NORMAL': {'speciesName': 'Deoxys', 'types': ['TYPE_PSYCHIC'], 'abilities': ['ABILITY_PRESSURE'], 'graphics': {}},
            'SPECIES_DEOXYS_ATTACK': {'speciesName': 'Deoxys', 'baseSpecies': 'SPECIES_DEOXYS_NORMAL', 'types': ['TYPE_PSYCHIC'], 'abilities': ['ABILITY_PRESSURE'], 'graphics': {}},
        },
        'moves': {}, 'abilities': {}, 'items': {}, 'encounters': [], 'trainers': [], 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(_StubProject(raw, hoenn_dex=True))
    assert list(model.national_to_species.items()) == [(1, 'SPECIES_JIRACHI'), (2, 'SPECIES_DEOXYS_NORMAL')]
    assert model.metadata['active_dex_map']['SPECIES_DEOXYS_NORMAL'] == 2
    assert model.metadata['active_dex_map']['SPECIES_DEOXYS_ATTACK'] == 2
